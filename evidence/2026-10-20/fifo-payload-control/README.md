# Generated default FIFO payload control

The actual generated scoreboard passed real xvlog/xelab/xsim simulation against
the supervised parameterized FIFO reference at defaultWIDTH8/DEPTH3. A small
supervised Python transaction-identity oracle passed the IOexamples and supplied
103payload transactions after reset. This oracle/reference is a qualification
artifact, not a model answer, seed or generated design. No model calls or PPA
measurements occurred. The six-corner independent temporal control is recorded
separately in fifo-qualification.

Exact spec/oracle/RTL/TB identities and raw process receipts are retained. The
control used autortl.tbgen.generate and autortl.vivado.xsim_run on a fresh work
directory. Do not use this one default payload check as parameter or capacity
proof. Compiled simulator artifacts are omitted; original paths are provenance.
