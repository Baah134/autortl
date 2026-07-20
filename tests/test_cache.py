from autortl.cache import code_hash, MetricsCache, ArtifactCache


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
