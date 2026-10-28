"""Stream random bytes to the Basys 3 echo design and check every byte returns.

Usage:
    python scripts/echo_test.py              # auto-detect the board's COM port
    python scripts/echo_test.py --port COM5 --bytes 20000
"""
import argparse
import os
import sys
import time

import serial
from serial.tools import list_ports

FTDI_VID = 0x0403


def find_port():
    candidates = [p for p in list_ports.comports() if p.vid == FTDI_VID]
    if not candidates:
        names = ", ".join(p.device for p in list_ports.comports()) or "none"
        sys.exit(f"No FTDI serial port found (ports seen: {names}). Use --port.")
    # The Basys 3 FT2232 exposes JTAG on interface A and UART on interface B.
    candidates.sort(key=lambda p: p.device)
    return candidates[-1].device


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--port")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--bytes", type=int, default=10000)
    parser.add_argument("--chunk", type=int, default=256)
    args = parser.parse_args()

    port = args.port or find_port()
    payload = os.urandom(args.bytes)
    received = bytearray()

    with serial.Serial(port, args.baud, timeout=2) as ser:
        ser.reset_input_buffer()
        start = time.perf_counter()
        for i in range(0, len(payload), args.chunk):
            chunk = payload[i:i + args.chunk]
            ser.write(chunk)
            got = ser.read(len(chunk))
            received += got
            if len(got) != len(chunk):
                break
        elapsed = time.perf_counter() - start

    mismatches = sum(a != b for a, b in zip(payload, received))
    missing = len(payload) - len(received)
    rate = len(received) / elapsed if elapsed else 0.0
    print(f"port {port} @ {args.baud} baud")
    print(f"sent {len(payload)}  received {len(received)}  "
          f"missing {missing}  mismatches {mismatches}")
    print(f"{rate:,.0f} bytes/s over {elapsed:.2f} s")

    if missing or mismatches:
        print("FAIL")
        sys.exit(1)
    print("PASS")


if __name__ == "__main__":
    main()
