"""Recorded verification input schema, using the harness's existing JSON format."""
import hashlib
import json
from pathlib import Path
import pytest
from autortl.fsm import _verification_dependencies, VerificationEvidenceError


@pytest.fixture
def manifest(tmp_path):
    # The portable shape fixture's paths/digests are rebound to actual local files.
    data=json.loads((Path(__file__).parent/"fixtures/verification_inputs.json").read_text(encoding="utf-8"))
    for row,name in zip([*data["sources"],data["testbench"]],["m.v","m_tb.v"]):
        source=tmp_path/name; source.write_text("// controlled fixture "+name,encoding="utf-8")
        row.update(path=str(source.resolve()),sha256=hashlib.sha256(source.read_bytes()).hexdigest())
    path=tmp_path/"verification_inputs.log"
    path.write_text(json.dumps(data),encoding="utf-8")
    return path,data


def test_retained_dependencies_use_recorded_source_and_tb_digests(manifest):
    path,data=manifest
    assert _verification_dependencies(path)=={row["path"]:row["sha256"] for row in [*data["sources"],data["testbench"]]}


@pytest.mark.parametrize("change",["version","boolean_version","float_version","empty_sources","missing_tb","relative_path","bad_hash","changed_hash","invalid_json","deleted_manifest","deleted_source"])
def test_missing_malformed_or_changed_verification_inputs_cannot_be_blessed(manifest,change):
    path,data=manifest
    if change=="version":data["schema_version"]=2
    if change=="boolean_version":data["schema_version"]=True
    if change=="float_version":data["schema_version"]=1.0
    if change=="empty_sources":data["sources"]=[]
    if change=="missing_tb":data["testbench"]=None
    if change=="relative_path":data["sources"][0]["path"]="m.v"
    if change=="bad_hash":data["sources"][0]["sha256"]="not-a-hash"
    if change=="changed_hash":data["sources"][0]["sha256"]="0"*64
    if change=="deleted_source":Path(data["sources"][0]["path"]).unlink()
    path.write_text(json.dumps(data),encoding="utf-8")
    if change=="invalid_json":path.write_text("{",encoding="utf-8")
    if change=="deleted_manifest":path.unlink()
    with pytest.raises(VerificationEvidenceError,match="verification dependency"):
        _verification_dependencies(path)
