"""Keep the coordinator lease alive during long work.

    python scripts/lease_keeper.py --token-file FILE [--stop-file FILE] [--interval 600]

Renews the lease with `scripts/session.py renew` every --interval seconds until
the stop file appears. The token is read from the file on every cycle, so a
coordinator that reclaims the lease only has to rewrite the file. The keeper
never claims or takes over a lease: if a renewal is refused (the lease lapsed,
for example after the machine slept, or another coordinator holds it), it exits
with code 4 and says so; reclaiming is the coordinator's decision.

The token file is private. Keep it outside the repository.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

SESSION = Path(__file__).resolve().parent / "session.py"
EXIT_STOPPED, EXIT_REFUSED = 0, 4


def renew(token: str, run=subprocess.run) -> tuple[bool, str]:
    done = run([sys.executable, str(SESSION), "renew", "--token", token],
               capture_output=True, text=True, timeout=120)
    return done.returncode == 0, ((done.stdout or "") + (done.stderr or "")).strip()


def keep(token_file: Path, stop_file: Path | None = None, interval: float = 600.0,
         renew_once=renew, sleep=time.sleep, max_cycles: int | None = None) -> int:
    cycles = 0
    while stop_file is None or not Path(stop_file).exists():
        token = Path(token_file).read_text(encoding="utf-8").strip()
        ok, message = renew_once(token)
        if not ok:
            # Never print the token; the message comes from session.py and has none.
            print(f"lease renewal refused: {message.splitlines()[-1] if message else 'no output'}",
                  file=sys.stderr)
            return EXIT_REFUSED
        cycles += 1
        if max_cycles is not None and cycles >= max_cycles:
            break
        sleep(interval)
    return EXIT_STOPPED


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--token-file", required=True, type=Path)
    parser.add_argument("--stop-file", type=Path)
    parser.add_argument("--interval", type=float, default=600.0)
    a = parser.parse_args(argv)
    if a.interval < 30:
        parser.error("--interval must be at least 30 seconds")
    return keep(a.token_file, a.stop_file, a.interval)


if __name__ == "__main__":
    sys.exit(main())
