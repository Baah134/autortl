"""Builders that three or more test files share; each returns exactly what its copies did."""
import importlib.util
import json

import yaml

from autortl.golden import GoldenModel
from autortl.spec import DesignSpec


def load_module(path, name):
    """Execute a Python file as a fresh module called ``name`` (not added to sys.modules)."""
    loaded = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(loaded)
    loaded.loader.exec_module(module)
    return module


def tier_entry_dirs(tier):
    """The entry folders of a curriculum tier, sorted, without __pycache__."""
    return sorted(p for p in tier.iterdir() if p.is_dir() and p.name != "__pycache__")


def load_tier_entry(tier, name):
    """(entry, meta, spec, tb, reference, mutants) of one tier build entry."""
    entry = tier / name
    meta = yaml.safe_load((entry / "meta.yaml").read_text(encoding="utf-8"))
    spec = DesignSpec.load(entry / meta["spec"])
    tb = (entry / meta["tb"]).read_text(encoding="utf-8")
    reference = (entry / "qualification" / "reference.v").read_text(encoding="utf-8")
    mutants = json.loads((entry / "qualification" / "mutants.json").read_text(encoding="utf-8"))
    return entry, meta, spec, tb, reference, mutants


def text_oracle(tmp_path, filename, source):
    """A GoldenModel for a test-only oracle written to ``tmp_path / filename``."""
    path = tmp_path / filename
    path.write_text(source, encoding="utf-8")
    model = GoldenModel(path)
    model.work_parent = tmp_path
    return model
