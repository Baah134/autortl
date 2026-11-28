"""Run configuration for AutoRTL v4."""
from dataclasses import dataclass, field, asdict, fields
import json
import math
import re
from pathlib import Path
from .state import atomic_write_text
from .fileio import read_json

IMPLEMENTATIONS = ("chip_top", "out_of_context")
# Benchmark arm B ablation (ablation_policy_seam_absent). "full" is the shipped
# behaviour; the other value is an explicit experiment setting only.
VERIFICATION_POLICIES = ("full", "skip_generated_tb_mutations")
# planner_spec_error_shared_by_oracle_and_rtl: an independent second reading of a
# prose request checks a planner-written spec (autortl/cross_check.py). A supplied
# JSON spec is law and is never cross-checked. See docs/DECISIONS.md for the default.
SPEC_CROSS_CHECK_POLICIES = ("request_traces", "off")


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
    generate_golden: bool = False             # build: also generate/qualify a unit oracle with --tb
    proposal_feedback: bool = False           # experimental prior-proposal context; journal always retained
    model: str | None = None                  # model alias for every role; None = the backend's own default
    # Harness-chosen implementation flow (chip_top_flow_for_soc_block): chip_top places
    # every port on a package pin; out_of_context implements a block without I/O buffers.
    implementation: str = "chip_top"
    # fixed_synthesis_timeout_blocks_heavy_designs: one synthesis/implementation call's
    # limit; the remaining tool budget still caps it.
    synthesis_timeout_minutes: float = 15.0
    # Experiment-only ablation: skip_generated_tb_mutations skips bug-injection
    # qualification of generated module testbenches; never inferred from other flags.
    verification_policy: str = "full"
    # grader_rejects_vendor_attribute: benchmark-only. When set, every xvlog_check
    # of design RTL also compiles it with this Icarus Verilog executable and the
    # evaluation grader's flags; a rejection is a design error for the existing
    # bounded repair loop. None (the default) runs no extra compiler.
    grader_iverilog: str | None = None
    # request_traces: a planner-written spec's golden model must agree with traces an
    # independent role call writes from the original request (one replan at most).
    # off (default until ROADMAP V1 measures it on fresh tasks): v1.0.0 behaviour,
    # recorded in config, events and summary so both settings can be benchmark arms.
    spec_cross_check: str = "off"

    def validate(self) -> None:
        if self.mode not in ("build", "optimize"):
            raise ValueError("invalid run mode")
        if self.implementation not in IMPLEMENTATIONS:
            raise ValueError("implementation must be one of: " + ", ".join(IMPLEMENTATIONS))
        if self.verification_policy not in VERIFICATION_POLICIES:
            raise ValueError("verification_policy must be one of: " + ", ".join(VERIFICATION_POLICIES))
        if self.spec_cross_check not in SPEC_CROSS_CHECK_POLICIES:
            raise ValueError("spec_cross_check must be one of: " + ", ".join(SPEC_CROSS_CHECK_POLICIES))
        if type(self.proposal_feedback) is not bool:
            raise ValueError("proposal_feedback must be boolean")
        if type(self.generate_golden) is not bool:
            raise ValueError("generate_golden must be boolean")
        if self.generate_golden and self.mode != "build":
            raise ValueError("generate_golden=True is supported only in build mode")
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
        timeout = self.synthesis_timeout_minutes
        if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 1 <= timeout <= 240:
            raise ValueError("synthesis_timeout_minutes must be between 1 and 240")
        if type(self.parallel_candidates) is not bool:
            raise ValueError("parallel_candidates must be boolean")
        if self.parallel_candidates:
            raise ValueError("parallel_candidates=True is unsupported; candidates execute sequentially")
        if self.model is not None and (not isinstance(self.model, str)
                                       or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,119}", self.model)):
            raise ValueError("model must be a plain model alias (letters, digits, . _ : / -)")
        if self.model == "default":
            raise ValueError("model 'default' would be the unpinned CLI default; omit --model instead")
        if self.grader_iverilog is not None and (not isinstance(self.grader_iverilog, str)
                                                 or not self.grader_iverilog.strip()):
            raise ValueError("grader_iverilog must be a nonempty executable path or None")
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
        # Additive schema-1 migration: older runs received neither option.
        # Preserve their original semantics. Proposal feedback is experimental
        # and disabled by default. Other required fields remain mandatory.
        data.setdefault("generate_golden", False)
        data.setdefault("proposal_feedback", False)
        # Runs saved before model pinning used the backend default model.
        data.setdefault("model", None)
        # Runs saved before the out-of-context flow implemented a chip top.
        data.setdefault("implementation", "chip_top")
        # Runs saved before the setting used the fixed 900 s synthesis limit.
        data.setdefault("synthesis_timeout_minutes", 15.0)
        # Runs saved before the arm B seam qualified every generated testbench.
        data.setdefault("verification_policy", "full")
        # Runs saved before the benchmark compile check ran no extra compiler.
        data.setdefault("grader_iverilog", None)
        # Runs saved before the request cross-check never ran it.
        data.setdefault("spec_cross_check", "off")
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
        return cls.from_dict(read_json(Path(path)))

    @property
    def target_period_ns(self) -> float:
        return 1000.0 / self.target_freq_mhz

    def iteration_dir(self, iteration: int) -> Path:
        d = self.work_dir / f"iter_{iteration:03d}"
        d.mkdir(parents=True, exist_ok=True)
        return d
