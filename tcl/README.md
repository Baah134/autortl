# tcl/

Intentionally empty of scripts.

AutoRTL v4 does NOT ship standalone .tcl files. All TCL is generated at run
time from templates inside `autortl/vivado.py` (see `SYNTH_TCL` and
`promotion_tcl`), with paths sanitised by `_tcl_path`. This is defence #11
(the TCL injection boundary): no LLM output and no unsanitised path ever
reaches a hand-edited script, because there are no hand-edited scripts.

If you need to inspect the exact TCL a run used, look in the per-iteration
candidate directory | each synthesis writes its `synth.tcl` there for audit.

This folder is kept as a documented placeholder so the layout matches
earlier versions and so this explanation has a home.
