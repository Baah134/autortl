"""Controlled actual CLI DONE reuse and restored tamper checks; no manual promotion."""
import argparse, hashlib, json, os, subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument("--run",required=True);p.add_argument("--output",required=True);p.add_argument("--python",required=True)
a=p.parse_args();repo=Path.cwd();run=Path(a.run).resolve();out=Path(a.output).resolve()
saved=json.loads((run/"state.json").read_text(encoding="utf-8"))
summary=json.loads((run/"run_summary.json").read_text(encoding="utf-8"))
assert saved["phase"]=="DONE" and summary["status"]=="done"
out.mkdir(parents=True,exist_ok=False)
paths={Path(name) for name in saved["final_artifacts"]}
paths.update(run/name for name in ("state.json","runtime.json","config.json","budget.json","run_summary.json","inputs.json","design_spec.json",summary["top_module"]+"_best.v"))
manifest=json.loads((run/"inputs.json").read_text(encoding="utf-8"))
paths.update(Path(item["path"]) for item in manifest.values())
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
before={str(path):digest(path) for path in paths}
names_before={str(path.relative_to(run)) for path in run.rglob("*") if path.is_file()}
budget_before=json.loads((run/"budget.json").read_text(encoding="utf-8"))
def invoke(name):
    process=subprocess.Popen([a.python,"-u","run.py","resume","--run",str(run)],cwd=repo,env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"},stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding="utf-8",errors="replace")
    try:output=process.communicate(timeout=60)[0]
    except subprocess.TimeoutExpired:
        # Only this proof's owned CLI tree; never a user GUI or unrelated job.
        subprocess.run(["taskkill","/PID",str(process.pid),"/T","/F"],capture_output=True)
        output=process.communicate()[0];(out/(name+".txt")).write_text(output,encoding="utf-8")
        raise RuntimeError("DONE check timed out; owned CLI tree terminated")
    (out/(name+".txt")).write_text(output,encoding="utf-8")
    return {"exit_code":process.returncode,"log":name+".txt"}
results={"nominal":invoke("nominal")}
assert results["nominal"]["exit_code"]==0
assert all(digest(Path(k))==v for k,v in before.items()),"Nominal DONE modified protected evidence"
children=sorted((run/"modules").glob("*/*.v"))
spec=json.loads((run/"design_spec.json").read_text(encoding="utf-8"))
child=run/"modules"/spec["modules"][0]["name"]/(spec["modules"][0]["name"]+".v")
assert child in paths and run/"design_spec.json" in paths
probes=[("child_tamper",child,b"\n// controlled temporary DONE identity probe\n"),("resolved_spec_tamper",run/"design_spec.json",b"\n ")]
trial_reports=sorted(path for path in paths if path.suffix==".rpt" and any(part.startswith("doctor_") for part in path.parts))
if trial_reports:probes.append(("doctor_report_tamper",trial_reports[0],b"\ncontrolled temporary report identity probe\n"))
for label,path,suffix in probes:
    original=path.read_bytes()
    try:
        path.write_bytes(original+suffix)
        result=invoke(label)
        assert result["exit_code"]!=0,label+" was incorrectly accepted"
        assert "missing or modified" in (out/result["log"]).read_text(encoding="utf-8"),label+" did not reject identity drift"
        results[label]=result
    finally:path.write_bytes(original)
    assert all(digest(Path(k))==v for k,v in before.items()),"Tamper probe changed protected evidence after restoration"
names_after={str(path.relative_to(run)) for path in run.rglob("*") if path.is_file()}
assert names_before==names_after,"DONE probes created/deleted run files"
assert json.loads((run/"budget.json").read_text(encoding="utf-8"))==budget_before
result={"ok":True,"scope":"Actual completed-run reuse and controlled restored child/resolved-spec tamper; no in-flight kill/recovery claim.","run":str(run),"protected_identities":len(before),"all_restored_unchanged":True,"run_file_set_unchanged":True,"budget_unchanged":True,"no_new_model_or_tool_charges":True,"results":results,"identities":before}
(out/"result.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
manifest={path.name:digest(path) for path in out.iterdir() if path.is_file()}
(out/"archive-manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
print(json.dumps({k:v for k,v in result.items() if k not in ("identities",)}),flush=True)

