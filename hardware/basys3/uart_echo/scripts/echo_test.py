"""Send random bytes to the Basys 3 echo design and check every byte returns.

stream (default) writes continuously at line rate from a background thread
while the main thread reads, so a design that cannot keep up loses bytes.
chunked writes a chunk and waits for its echo before sending the next one.

Usage:
    python scripts/echo_test.py                       # auto-detect the board
    python scripts/echo_test.py --port COM10 --bytes 100000
    python scripts/echo_test.py --mode chunked --baud 57600
"""
import argparse
import os
import re
import sys
import threading
import time

import serial
from serial.tools import list_ports

FTDI_VID = 0x0403


def _port_number(port):
    match = re.search(r"(\d+)$", port.device)
    return int(match.group(1)) if match else -1


def find_port():
    candidates = [p for p in list_ports.comports() if p.vid == FTDI_VID]
    if not candidates:
        names = ", ".join(p.device for p in list_ports.comports()) or "none"
        sys.exit(f"No FTDI serial port found (ports seen: {names}). Use --port.")
    # The Basys 3 FT2232 exposes JTAG on interface A and the UART on interface B,
    # whose serial number ends in "B".
    uart = [p for p in candidates if (p.serial_number or "").endswith("B")]
    return max(uart or candidates, key=_port_number).device


def run_chunked(ser, payload, chunk):
    received = bytearray()
    written = 0
    for i in range(0, len(payload), chunk):
        piece = payload[i:i + chunk]
        ser.write(piece)
        written += len(piece)
        got = ser.read(len(piece))
        received += got
        if len(got) != len(piece):
            break
    return written, received


def run_stream(ser, payload, chunk, idle_timeout):
    written = [0]

    def writer():
        for i in range(0, len(payload), chunk):
            piece = payload[i:i + chunk]
            ser.write(piece)
            written[0] += len(piece)

    thread = threading.Thread(target=writer, daemon=True)
    received = bytearray()
    thread.start()
    last = time.perf_counter()
    while True:
        got = ser.read(ser.in_waiting or 1)
        if got:
            received += got
            last = time.perf_counter()
        elif not thread.is_alive() and time.perf_counter() - last > idle_timeout:
            break
        if not thread.is_alive() and len(received) >= written[0]:
            break
    thread.join()
    return written[0], received


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--port")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--bytes", type=int, default=20000)
    parser.add_argument("--chunk", type=int, default=256)
    parser.add_argument("--mode", choices=("stream", "chunked"), default="stream")
    args = parser.parse_args()

    port = args.port or find_port()
    payload = os.urandom(args.bytes)
    # Allow ten bit times per byte at the chosen baud, doubled, for each read.
    read_timeout = max(1.0, 2 * 10 * args.chunk / args.baud)

    with serial.Serial(port, args.baud, timeout=0.2 if args.mode == "stream" else read_timeout) as ser:
        ser.reset_input_buffer()
        start = time.perf_counter()
        if args.mode == "stream":
            written, received = run_stream(ser, payload, args.chunk, idle_timeout=1.0)
        else:
            written, received = run_chunked(ser, payload, args.chunk)
        elapsed = time.perf_counter() - start

    sent = payload[:written]
    missing = written - len(received)
    first_bad = next((i for i, (a, b) in enumerate(zip(sent, received)) if a != b), None)
    rate = len(received) / elapsed if elapsed else 0.0
    print(f"port {port} @ {args.baud} baud, mode {args.mode}")
    print(f"requested {len(payload)}  written {written}  received {len(received)}  missing {missing}")
    print("first mismatch at byte " + (str(first_bad) if first_bad is not None else "none"))
    print(f"{rate:,.0f} bytes/s over {elapsed:.2f} s")

    if missing or first_bad is not None or written != len(payload):
        print("FAIL")
        sys.exit(1)
    print("PASS")


if __name__ == "__main__":
    main()
