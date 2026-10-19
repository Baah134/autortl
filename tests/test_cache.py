from autortl.cache import code_hash, MetricsCache, ArtifactCache
import pytest


@pytest.fixture
def evidence(tmp_path):
    root = tmp_path / "evidence"
    root.mkdir()
    (root / "m.v").write_text("module m; endmodule", encoding="utf-8")
    (root / "timing.rpt").write_text("WNS 1.0", encoding="utf-8")
    return root


def test_hash_ignores_comments_and_whitespace():
    a = "module m; // hello\n  assign y = x;\nendmodule"
    b = "module m;   assign y=x; endmodule".replace("y=x", "y = x")
    assert code_hash(a) == code_hash(b)


def test_hash_sensitive_to_logic():
    assert code_hash("assign y = a & b;") != code_hash("assign y = a | b;")


def test_metrics_cache_roundtrip(tmp_path):
    c = MetricsCache(tmp_path / "m.json")
    c.put("module m; endmodule", {"lut_used": 5})
    c2 = MetricsCache(tmp_path / "m.json")     # reload from disk
    assert c2.get("module m; endmodule") == {"lut_used": 5}


def test_artifact_cache_roundtrip(tmp_path):
    c = ArtifactCache(tmp_path / "a.json")
    c.put("abc123", "module x; endmodule", {"ok": True})
    c2 = ArtifactCache(tmp_path / "a.json")
    assert c2.get("abc123")["verilog"] == "module x; endmodule"
    assert c2.get("nope") is None


def test_context_cache_roundtrip_and_detached_result(tmp_path, evidence):
    c = MetricsCache(tmp_path / "m.json")
    context = {"part": "device", "period": 10, "tb_hash": "abc"}
    c.put("module m; endmodule", {"lut_used": 5}, context, evidence)
    entry = MetricsCache(c.path).get_entry("module m; endmodule", context)
    assert entry["metrics"]["lut_used"] == 5
    assert entry["artifact_dir"] == str(evidence.resolve())
    entry["metrics"]["lut_used"] = 999
    assert c.get("module m; endmodule", context)["lut_used"] == 5


def test_context_changes_and_legacy_cache_never_hit(tmp_path, evidence):
    c = MetricsCache(tmp_path / "m.json")
    source = "module m; endmodule"
    c.put(source, {"lut_used": 5})
    assert c.get(source, {"part": "a"}) is None
    c.put(source, {"lut_used": 5}, {"part": "a"}, evidence)
    assert c.get(source, {"part": "b"}) is None
    assert c.get(source + " // cosmetic", {"part": "a"}) is None


@pytest.mark.parametrize("target", ["m.v", "timing.rpt"])
@pytest.mark.parametrize("change", ["edit", "delete"])
def test_changed_or_missing_evidence_invalidates_cache(tmp_path, evidence, target, change):
    c = MetricsCache(tmp_path / "m.json")
    source = "module m; endmodule"
    c.put(source, {"lut_used": 5}, {"part": "a"}, evidence)
    if change == "edit":
        (evidence / target).write_text("changed", encoding="utf-8")
    else:
        (evidence / target).unlink()
    assert c.get(source, {"part": "a"}) is None


def test_context_cache_requires_actual_source_and_reports(tmp_path, evidence):
    c = MetricsCache(tmp_path / "m.json")
    c.put("module other; endmodule", {}, {}, evidence)
    assert c.get_entry("module other; endmodule", {}) is None
    c.put("module m; endmodule", {}, {})
    assert c.get_entry("module m; endmodule", {}) is None


def test_path_escape_in_cache_manifest_is_rejected(tmp_path, evidence):
    c = MetricsCache(tmp_path / "m.json")
    source = "module m; endmodule"
    c.put(source, {}, {}, evidence)
    entry = c._data[c._context_key(source, {})]
    entry["artifacts"]["../outside.rpt"] = "fake"
    assert c.get_entry(source, {}) is None


@pytest.mark.parametrize("cache_type", [MetricsCache, ArtifactCache])
def test_failed_atomic_cache_write_preserves_memory_and_disk(monkeypatch, tmp_path, cache_type):
    from autortl import state
    cache = cache_type(tmp_path / "cache.json")
    args = ("module m; endmodule", {"lut_used": 5}) if cache_type is MetricsCache else ("contract", "rtl", {"ok": True})
    cache.put(*args)
    before = cache.path.read_text()
    def fail(*args):
        raise OSError("interrupted")
    monkeypatch.setattr(state.os, "replace", fail)
    bad = ("different", {"lut_used": 1}) if cache_type is MetricsCache else ("different", "rtl", {})
    with pytest.raises(OSError):
        cache.put(*bad)
    assert cache.path.read_text() == before
    assert cache.get("different") is None


@pytest.mark.parametrize("contents", ['{"partial":', '[]'])
def test_corrupt_or_nonobject_cache_is_safe_miss(tmp_path, contents):
    path = tmp_path / "cache.json"
    path.write_text(contents)
    assert MetricsCache(path).get("anything", {}) is None


def test_context_key_ignores_dictionary_order(tmp_path, evidence):
    c = MetricsCache(tmp_path / "cache.json")
    source = "module m; endmodule"
    c.put(source, {"lut_used": 3}, {"part": "a", "clock": 10}, evidence)
    assert c.get(source, {"clock": 10, "part": "a"}) == {"lut_used": 3}
