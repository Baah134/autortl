# Oracle API and active-exit budget fixes

Full frozen regression: 1415 passed in 685.29 seconds;
all 220 source identities unchanged. Separate focused checks: prompt 7,
budget/resume 44, elastic fixture/verification 122 tests passed.

The prompt now supplies valid Python and documents the unchanged restricted
worker policy. Active dispatch exits persist final wall time without extra
model/tool charges; existing DONE reuse and preflight guards do not rewrite it.
Tests cover clean failures, provider/budget stops, raised exceptions and graceful
interruption. This does not establish atomic charging after a hard process kill.

The fixture spec and TB match the separately archived 19/19 actual Vivado
checker qualification. The original failed generated build and assertion-prefix
attempt are preserved separately. This suite does not establish generated RTL
success or PPA gain. A fresh full tier0 gate remains before main integration.
