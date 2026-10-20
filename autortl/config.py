"""Run configuration for AutoRTL v4."""
from dataclasses import dataclass, field, asdict, fields
import json
import math
from pathlib import Path
from .state import atomic_write_text


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
    max_infra_retries: int = 2
    stall_restart_threshold: int = 3
    work_dir: Path = field(default_factory=lambda: Path("logs"))
    vivado_bin: str = "vivado"
    xvlog_bin: str = "xvlog"
    xelab_bin: str = "xelab"
    xsim_bin: str = "xsim"
    max_llm_calls: int = 200
    max_vivado_minutes: float = 120.0
    max_wall_minutes: float = 240.0

    def validate(self) -> None:
        if self.mode not in ("build", "optimize"):
            raise ValueError("invalid run mode")
        if self.objective not in ("minimize_luts", "minimize_ffs", "maximize_freq", "minimize_power"):
            raise ValueError("invalid objective")
        for name in ("max_iterations", "best_of_n", "max_replans", "max_fix_attempts",
                     "max_infra_retries", "stall_restart_threshold", "max_llm_calls"):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise ValueError(f"{name} must be a nonnegative integer")
        if self.best_of_n == 0 or self.stall_restart_threshold == 0:
            raise ValueError("best_of_n and stall_restart_threshold must be positive")
        for name in ("target_freq_mhz", "max_vivado_minutes", "max_wall_minutes"):
            value = getattr(self, name)
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                raise ValueError(f"{name} must be a finite nonnegative number")
        if self.target_freq_mhz == 0:
            raise ValueError("target_freq_mhz must be positive")
        if type(self.parallel_candidates) is not bool:
            raise ValueError("parallel_candidates must be boolean")
        if self.parallel_candidates:
            raise ValueError("parallel_candidates=True is unsupported; candidates execute sequentially")
        if self.work_dir is None:
            raise ValueError("work_dir is required")
        for name in ("target_part", "vivado_bin", "xvlog_bin", "xelab_bin", "xsim_bin"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be a nonempty string")

    def to_dict(self) -> dict:
        self.validate()
        data = asdict(self)
        for name in ("design_path", "testbench_path", "spec_path", "work_dir"):
            if data[name] is not None:
                data[name] = str(Path(data[name]).expanduser().resolve())
        data["schema_version"] = 1
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "RunConfig":
        data = dict(data)
        if data.pop("schema_version", None) != 1:
            raise ValueError("unsupported or missing run config schema_version")
        allowed = {item.name for item in fields(cls)}
        if set(data) - allowed:
            raise ValueError("unknown run config fields: " + ", ".join(sorted(set(data) - allowed)))
        missing = allowed - set(data)
        if missing:
            raise ValueError("incomplete saved run config: " + ", ".join(sorted(missing)))
        for name in ("design_path", "testbench_path", "spec_path", "work_dir"):
            if data[name] is not None:
                path = Path(data[name])
                if not path.is_absolute():
                    raise ValueError(f"saved {name} must be absolute")
                data[name] = path
        if data["mode"] not in ("build", "optimize"):
            raise ValueError("invalid saved mode")
        config = cls(**data)
        config.validate()
        return config

    def save(self, path: Path) -> None:
        atomic_write_text(path, json.dumps(self.to_dict(), indent=2))

    @classmethod
    def load(cls, path: Path) -> "RunConfig":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    @property
    def target_period_ns(self) -> float:
        return 1000.0 / self.target_freq_mhz

    def iteration_dir(self, iteration: int) -> Path:
        d = self.work_dir / f"iter_{iteration:03d}"
        d.mkdir(parents=True, exist_ok=True)
        return d
