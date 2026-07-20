"""Run configuration for AutoRTL v4."""
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RunConfig:
    mode: str                                # "build" | "optimize"
    top_module: str = ""
    design_path: Path | None = None          # optimize mode: seed design
    testbench_path: Path | None = None       # optional hand-written tb
    spec_path: Path | None = None            # build mode: spec file
    target_part: str = "xc7a35tcpg236-1"
    target_freq_mhz: float = 100.0
    objective: str = "minimize_luts"
    max_iterations: int = 10
    best_of_n: int = 4
    parallel_candidates: bool = False
    max_replans: int = 2
    max_fix_attempts: int = 3
    stall_restart_threshold: int = 3
    work_dir: Path = field(default_factory=lambda: Path("logs"))
    vivado_bin: str = "vivado"
    xvlog_bin: str = "xvlog"
    xelab_bin: str = "xelab"
    xsim_bin: str = "xsim"
    max_llm_calls: int = 200
    max_vivado_minutes: float = 120.0
    max_wall_minutes: float = 240.0

    @property
    def target_period_ns(self) -> float:
        return 1000.0 / self.target_freq_mhz

    def iteration_dir(self, iteration: int) -> Path:
        d = self.work_dir / f"iter_{iteration:03d}"
        d.mkdir(parents=True, exist_ok=True)
        return d
