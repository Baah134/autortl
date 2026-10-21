"""Parse Vivado reports into structured metrics."""
from __future__ import annotations
import re
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class VivadoMetrics:
    sim_passed: bool = False
    sim_error: str = ""
    wns_ns: float = -999.0
    whs_ns: float = -999.0
    timing_met: bool = False
    lut_used: int = 0
    lut_total: int = 0
    ff_used: int = 0
    ff_total: int = 0
    dsp_used: int = 0
    dsp_total: int = 0
    bram_used: float = 0.0
    bram_total: float = 0.0
    total_power_w: float = 0.0
    dynamic_power_w: float = 0.0
    synth_error: str = ""

    @property
    def lut_pct(self) -> float:
        return 100.0 * self.lut_used / self.lut_total if self.lut_total else 0.0

    @property
    def ff_pct(self) -> float:
        return 100.0 * self.ff_used / self.ff_total if self.ff_total else 0.0

    def to_dict(self) -> dict:
        d = asdict(self)
        d["lut_pct"] = self.lut_pct
        d["ff_pct"] = self.ff_pct
        return d

    @staticmethod
    def from_dict(d: dict) -> "VivadoMetrics":
        clean = {k: v for k, v in d.items() if k not in ("lut_pct", "ff_pct")}
        return VivadoMetrics(**clean)


def parse_sim_log(log_path: Path) -> tuple[bool, str]:
    if not log_path.exists():
        return False, "Simulation log not found"
    text = log_path.read_text(errors="replace")
    fails = [l.strip() for l in text.splitlines()
             if l.strip().startswith("FAIL") or "mismatch" in l.lower()]
    if re.search(r"TEST\s+FAILED", text, re.IGNORECASE) or fails:
        return False, "Testbench failures:\n" + "\n".join(fails[:15]) if fails \
               else "testbench reported failure"
    if re.search(r"\$fatal|\*\*\s*Error|^\s*(?:ERROR|FATAL|CRITICAL WARNING)\s*:",
                 text, re.IGNORECASE | re.MULTILINE):
        return False, "Fatal error in simulation"
    if re.search(r"^\s*TEST\s+PASSED\s*$", text, re.IGNORECASE | re.MULTILINE):
        return True, ""
    return False, "Simulation ended without clear pass/fail"


def parse_utilization(rpt_path: Path, m: VivadoMetrics) -> None:
    if not rpt_path.exists():
        return
    text = rpt_path.read_text(errors="replace")
    pat = lambda label: re.compile(
        r"\|\s*" + label + r"\s*\|\s*([\d.]+)\s*\|\s*[\d.]+\s*\|(?:\s*[\d.]+\s*\|)?\s*([\d.]+)\s*\|")
    mm = pat(r"(?:Slice|CLB)\s+LUTs?\*?").search(text)
    if mm:
        m.lut_used, m.lut_total = int(float(mm.group(1))), int(float(mm.group(2)))
    mm = pat(r"(?:Slice|CLB)\s+Registers?").search(text)
    if mm:
        m.ff_used, m.ff_total = int(float(mm.group(1))), int(float(mm.group(2)))
    mm = pat(r"DSPs?").search(text)
    if mm:
        m.dsp_used, m.dsp_total = int(float(mm.group(1))), int(float(mm.group(2)))
    mm = pat(r"Block\s+RAM\s+Tile").search(text)
    if mm:
        m.bram_used, m.bram_total = float(mm.group(1)), float(mm.group(2))


def parse_timing(rpt_path: Path, m: VivadoMetrics) -> None:
    if not rpt_path.exists():
        return
    parse_timing_text(rpt_path.read_bytes().decode("utf-8", errors="replace"), m)


def parse_timing_text(text: str, m: VivadoMetrics) -> None:
    """Canonical timing summary parser over an immutable decoded snapshot."""
    lines = text.splitlines()
    found = set()
    for i, line in enumerate(lines):
        header = line.strip().lstrip("| ")
        if not header.startswith(("WNS(ns)", "WHS(ns)")):
            continue
        columns = re.split(r"\s{2,}", header)
        for row in lines[i + 1:i + 4]:
            values = row.strip().split()
            if not values or not re.fullmatch(r"-?\d+(?:\.\d+)?", values[0]):
                continue
            for label, attr in (("WNS(ns)", "wns_ns"), ("WHS(ns)", "whs_ns")):
                if label not in columns or label in found:
                    continue
                index = columns.index(label)
                if index < len(values):
                    try:
                        setattr(m, attr, float(values[index]))
                        found.add(label)
                    except ValueError:
                        pass
            break
    m.timing_met = m.wns_ns >= 0.0 and m.whs_ns >= 0.0


def parse_power(rpt_path: Path, m: VivadoMetrics) -> None:
    if not rpt_path.exists():
        return
    text = rpt_path.read_text(errors="replace")
    mm = re.search(r"\|\s*Total On-Chip Power.*?\|\s*([\d.]+)\s*\|", text)
    if mm:
        m.total_power_w = float(mm.group(1))
    mm = re.search(r"\|\s*Dynamic.*?\|\s*([\d.]+)\s*\|", text)
    if mm:
        m.dynamic_power_w = float(mm.group(1))


def parse_all(work_dir: Path) -> VivadoMetrics:
    m = VivadoMetrics()
    m.sim_passed, m.sim_error = parse_sim_log(work_dir / "sim_log.txt")
    util = work_dir / "utilization_routed.rpt"
    if not util.exists():
        util = work_dir / "utilization.rpt"
    parse_utilization(util, m)
    timing = work_dir / "timing_routed.rpt"
    if not timing.exists():
        timing = work_dir / "timing.rpt"
    parse_timing(timing, m)
    parse_power(work_dir / "power.rpt", m)
    return m


def extract_message_ids(text: str) -> list[str]:
    """Pull structured Vivado message IDs like [Synth 8-327] out of any log."""
    return list(dict.fromkeys(re.findall(r"\[([A-Za-z]+ \d+-\d+)\]", text)))


# ---------------- Planner-advisory parsers (advisory only, never blocking) ----

def parse_methodology(rpt_path: Path) -> list[tuple[str, str, str]]:
    """Parse report_methodology output.

    Returns [(rule_id, severity, description)] for each violation row.
    Tolerant of table variants across Vivado versions: matches any line
    containing an UPPERCASE-N rule id followed by a known severity word.
    """
    if not rpt_path.exists():
        return []
    out: list[tuple[str, str, str]] = []
    text = rpt_path.read_text(errors="replace")
    pat = re.compile(
        r"^\s*\|?\s*([A-Z][A-Z0-9]{2,7}-\d+)\s*(?:#\d+)?\s*\|?\s*"
        r"(Critical Warning|Warning|Advisory|Error)\s*\|?\s*(.+?)\s*\|?\s*$",
        re.MULTILINE)
    for m in pat.finditer(text):
        rid, sev, desc = m.group(1), m.group(2), m.group(3)
        # collapse trailing violation-count columns if present
        desc = re.sub(r"\|\s*\d+\s*$", "", desc).strip()
        out.append((rid, sev, desc[:160]))
    # dedupe by rule id, keep first (highest in report = usually worst)
    seen, uniq = set(), []
    for rid, sev, desc in out:
        if rid not in seen:
            seen.add(rid)
            uniq.append((rid, sev, desc))
    return uniq


def parse_qor_suggestions(rpt_path: Path, limit: int = 8) -> list[str]:
    """Parse report_qor_suggestions output into short suggestion strings.

    Format varies across versions; we extract RQS ids with their text where
    present, else any line that reads like a suggestion. Advisory only.
    """
    if not rpt_path.exists():
        return []
    text = rpt_path.read_text(errors="replace")
    out: list[str] = []
    for m in re.finditer(r"^\s*\|?\s*(RQS[A-Z]*-\d+)\s*\|?\s*(.+?)\s*\|?\s*$",
                         text, re.MULTILINE):
        out.append(f"[{m.group(1)}] {m.group(2)[:160]}")
    if not out:
        for line in text.splitlines():
            s = line.strip().strip("|").strip()
            if re.search(r"\bsuggest(?:ion|ed|s)?\b", s, re.IGNORECASE) \
               and len(s) > 20 and not s.lower().startswith("report"):
                out.append(s[:180])
    return list(dict.fromkeys(out))[:limit]
