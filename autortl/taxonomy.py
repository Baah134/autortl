"""Error taxonomy keyed on official Vivado message IDs (Upgrade A/B).

Fallback ladder when an unknown ID appears:
  1) query Vivado's own long help for the ID (offline, deterministic)
  2) inject that official text into the fix prompt
  3) log the ID for post-run curation (feeds the vivado-messages skill)
"""
from __future__ import annotations
import subprocess
from pathlib import Path
try:
    import yaml
except ImportError:
    yaml = None


class Taxonomy:
    def __init__(self, path: Path):
        self.path = path
        self.entries: dict[str, dict] = {}
        self.unknown_log = path.parent / "unknown_message_ids.log"
        self.methodology: dict[str, dict] = {}
        if path.exists() and yaml:
            data = yaml.safe_load(path.read_text()) or {}
            self.entries = data.get("messages", {})
            self.methodology = data.get("methodology", {})

    def promotions(self) -> dict[str, str]:
        return {mid: e["severity_override"] for mid, e in self.entries.items()
                if e.get("severity_override")}

    def lookup(self, message_id: str) -> dict | None:
        return self.entries.get(message_id)

    def lookup_methodology(self, rule_id: str) -> dict | None:
        """Advisory methodology entries (TIMING-6 etc). Never used to block."""
        return self.methodology.get(rule_id)

    def log_unknown(self, any_id: str) -> None:
        with open(self.unknown_log, "a", encoding="utf-8") as f:
            f.write(any_id + "\n")

    def repair_instruction(self, message_id: str, vivado_bin: str = "") -> str:
        e = self.lookup(message_id)
        if e:
            return f"[{message_id}] {e.get('meaning','')}. Repair: {e.get('repair','')}"
        # unknown: try Vivado's own help
        official = self._query_vivado_help(message_id, vivado_bin) if vivado_bin else ""
        with open(self.unknown_log, "a", encoding="utf-8") as f:
            f.write(message_id + "\n")
        if official:
            return f"[{message_id}] Vivado's official explanation:\n{official[:800]}"
        return f"[{message_id}] (no taxonomy entry; raw error follows)"

    @staticmethod
    def _query_vivado_help(message_id: str, vivado_bin: str) -> str:
        try:
            r = subprocess.run(
                [vivado_bin, "-mode", "batch", "-nolog", "-nojournal",
                 "-notrace", "-source", "/dev/stdin"],
                input=f"puts [help -message {{{message_id}}}]\n",
                capture_output=True, text=True, timeout=90)
            return r.stdout.strip()
        except Exception:
            return ""
