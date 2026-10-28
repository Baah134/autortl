"""Stream signed samples through the harness FIR on the Basys 3 and check every output.

The PC sends a UART break to restart the filter, then sends signed 8-bit
samples in chunks and reads each chunk's 16-bit little-endian outputs. A
Python model of y = 3x[n] - 5x[n-1] + 7x[n-2] - 2x[n-3] (kept to 13 bits)
checks every output. --restart-every sends extra breaks mid-stream.
--wrong-model uses a 6 instead of the 7 and must fail, which shows the
check can tell the difference.

Usage:
    python scripts/fir_test.py --samples 100000
    python scripts/fir_test.py --samples 5000 --wrong-model
"""
import argparse
import os
import re
import struct
import sys
import time

import serial
from serial.tools import list_ports

FTDI_VID = 0x0403
COEFFS = (3, -5, 7, -2)
# Signed extremes first: worst-case magnitudes on every tap.
LEADING = [127, -128, 127, -128, -1, 0, -128, 127, -128, 127]


def find_port():
    candidates = [p for p in list_ports.comports() if p.vid == FTDI_VID]
    if not candidates:
        names = ", ".join(p.device for p in list_ports.comports()) or "none"
        sys.exit(f"No FTDI serial port found (ports seen: {names}). Use --port.")
    uart = [p for p in candidates if (p.serial_number or "").endswith("B")]
    number = lambda p: int(re.search(r"(\d+)$", p.device).group(1)) if re.search(r"(\d+)$", p.device) else -1
    return max(uart or candidates, key=number).device


class Fir4Model:
    def __init__(self, coeffs):
        self.coeffs = coeffs
        self.reset()

    def reset(self):
        self.history = [0, 0, 0]

    def step(self, x):
        taps = [x] + self.history
        full = sum(c * t for c, t in zip(self.coeffs, taps))
        self.history = [x] + self.history[:2]
        y = full & 0x1FFF                      # keep 13 bits, as the RTL does
        return y - 0x2000 if y & 0x1000 else y


def restart(ser, model):
    ser.send_break(duration=0.01)
    time.sleep(0.02)
    ser.reset_input_buffer()
    model.reset()


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--port")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--samples", type=int, default=100000)
    parser.add_argument("--chunk", type=int, default=16, help="at most 32, the input FIFO depth")
    parser.add_argument("--restart-every", type=int, default=25000)
    parser.add_argument("--wrong-model", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.chunk <= 32:
        sys.exit("--chunk must be 1..32")

    coeffs = (3, -5, 6, -2) if args.wrong_model else COEFFS
    model = Fir4Model(coeffs)
    rng = os.urandom(args.samples)
    samples = [(LEADING[i] if i < len(LEADING) else struct.unpack("b", rng[i:i + 1])[0])
               for i in range(args.samples)]
    port = args.port or find_port()

    checked = mismatches = restarts = 0
    first_bad = None
    largest = 0
    start = time.perf_counter()
    with serial.Serial(port, args.baud, timeout=max(1.0, 40 * args.chunk / args.baud)) as ser:
        restart(ser, model)
        restarts += 1
        sent_since_restart = 0
        for base in range(0, len(samples), args.chunk):
            if args.restart_every and sent_since_restart >= args.restart_every:
                restart(ser, model)
                restarts += 1
                sent_since_restart = 0
            chunk = samples[base:base + args.chunk]
            ser.write(struct.pack(f"{len(chunk)}b", *chunk))
            reply = ser.read(2 * len(chunk))
            if len(reply) != 2 * len(chunk):
                print(f"short reply at sample {base}: {len(reply)} of {2 * len(chunk)} bytes")
                break
            for i, (got,) in enumerate(struct.iter_unpack("<h", reply)):
                want = model.step(chunk[i])
                largest = max(largest, abs(want))
                checked += 1
                if got != want:
                    mismatches += 1
                    if first_bad is None:
                        first_bad = (base + i, chunk[i], want, got)
            sent_since_restart += len(chunk)
    elapsed = time.perf_counter() - start

    print(f"port {port} @ {args.baud} baud, model coefficients {coeffs}")
    print(f"samples {args.samples}  checked {checked}  mismatches {mismatches}  restarts {restarts}")
    print(f"largest expected |y| {largest}")
    if first_bad:
        print("first mismatch: sample {} x={} expected {} got {}".format(*first_bad))
    print(f"{checked / elapsed:,.0f} samples/s over {elapsed:.2f} s")
    if checked != args.samples or mismatches:
        print("FAIL")
        sys.exit(1)
    print("PASS")


if __name__ == "__main__":
    main()
