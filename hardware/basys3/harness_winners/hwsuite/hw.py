"""Hardware check over the Basys 3 USB-UART: restart with a break, stream
transactions in chunks, compare every result with the reference model."""
from __future__ import annotations

import random
import re
import sys
import time

from .models import model_for

FTDI_VID = 0x0403
MAX_OUTSTANDING = 32                  # stream_shell FIFO_LOG2 = 5


def _serial():
    try:
        import serial
        from serial.tools import list_ports
    except ImportError:
        raise RuntimeError("pyserial is required for hardware runs: "
                           "python -m pip install -r requirements.txt") from None
    return serial, list_ports


def find_port() -> str:
    _, list_ports = _serial()
    candidates = [p for p in list_ports.comports() if p.vid == FTDI_VID]
    if not candidates:
        names = ", ".join(p.device for p in list_ports.comports()) or "none"
        raise RuntimeError(f"No FTDI serial port found (ports seen: {names}); pass --port")
    uart = [p for p in candidates if (p.serial_number or "").endswith("B")]   # FT2232 interface B

    def number(p):
        match = re.search(r"(\d+)$", p.device)
        return int(match.group(1)) if match else -1
    return max(uart or candidates, key=number).device


def run(design, port=None, count=20000, chunk=16, restart_every=5000, wrong_model=False,
        seed=28, baud=115200) -> dict:
    serial, _ = _serial()
    if not 1 <= chunk <= MAX_OUTSTANDING:
        raise ValueError(f"chunk must be 1..{MAX_OUTSTANDING}")
    model = model_for(design.name, wrong=wrong_model)
    rng = random.Random(seed)
    port = port or find_port()
    checked = mismatches = restarts = 0
    first_bad = None
    short_reply = None
    start = time.perf_counter()
    bytes_per_chunk = chunk * (design.in_bytes + design.out_bytes)
    timeout = max(1.0, 4 * 10 * bytes_per_chunk / baud)
    with serial.Serial(port, baud, timeout=timeout) as ser:
        sent_since_restart = None
        index = 0
        while index < count:
            if sent_since_restart is None or (restart_every and sent_since_restart >= restart_every):
                ser.send_break(duration=0.01)
                time.sleep(0.02)
                ser.reset_input_buffer()
                model.reset()
                restarts += 1
                sent_since_restart = 0
                pending = model.stimulus(rng, min(restart_every or count, count - index))
            n = min(chunk, count - index, len(pending))
            batch, pending = pending[:n], pending[n:]
            ser.write(b"".join(batch))
            reply = ser.read(n * design.out_bytes)
            if len(reply) != n * design.out_bytes:
                short_reply = {"at": index, "got": len(reply), "wanted": n * design.out_bytes}
                break
            for k, tx in enumerate(batch):
                want = model.step(tx)
                got = reply[k * design.out_bytes:(k + 1) * design.out_bytes]
                checked += 1
                if got != want:
                    mismatches += 1
                    if first_bad is None:
                        first_bad = {"index": index + k, "tx": tx.hex(), "expected": want.hex(), "got": got.hex()}
            index += n
            sent_since_restart += n
    elapsed = time.perf_counter() - start
    return {"design": design.name, "winner_sha256": design.sha256, "port": port, "baud": baud,
            "wrong_model": wrong_model, "seed": seed, "requested": count, "checked": checked,
            "mismatches": mismatches, "restarts": restarts, "first_mismatch": first_bad,
            "short_reply": short_reply, "seconds": round(elapsed, 2),
            "transactions_per_second": round(checked / elapsed, 1) if elapsed else 0.0,
            "passed": checked == count and mismatches == 0 and short_reply is None}


def format_report(r: dict) -> str:
    lines = [f"{r['design']:18} {'WRONG MODEL ' if r['wrong_model'] else ''}"
             f"checked {r['checked']}/{r['requested']}  mismatches {r['mismatches']}  restarts {r['restarts']}  "
             f"{r['transactions_per_second']}/s  -> {'PASS' if r['passed'] else 'FAIL'}"]
    if r["first_mismatch"]:
        m = r["first_mismatch"]
        lines.append(f"{'':18} first mismatch at {m['index']}: tx {m['tx']} expected {m['expected']} got {m['got']}")
    if r["short_reply"]:
        lines.append(f"{'':18} short reply: {r['short_reply']}")
    return "\n".join(lines)


if __name__ == "__main__":
    sys.exit("use: python -m hwsuite hw --design NAME")
