"""Write manifest.json: the SHA-256 of every other file in this folder."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

files = {p.relative_to(HERE).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
         for p in sorted(HERE.rglob("*")) if p.is_file() and p.name != "manifest.json"}
(HERE / "manifest.json").write_text(json.dumps({"algorithm": "sha256", "files": files}, indent=2) + "\n",
                                    encoding="utf-8", newline="\n")
print(f"{len(files)} files")
