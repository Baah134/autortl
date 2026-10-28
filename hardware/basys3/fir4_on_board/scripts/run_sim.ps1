# Simulates the FIR4 shell with xsim and fails unless the testbench prints PASS.
# -Dut selects the filter source (default: the harness winner in dut/), so a
# deliberately faulted copy can be checked to fail.
#   powershell -File scripts/run_sim.ps1 [-Dut path] [-Out build/sim] [-Vivado <bin>]
param(
    [string]$Dut = "",
    [string]$Out = "",
    [string]$Vivado = "C:\AMDDesignTools\2025.2\Vivado\bin"
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$uart = Join-Path (Split-Path -Parent $root) "uart_echo\rtl"
if (-not $Dut) { $Dut = Join-Path $root "dut\signed_fir4.v" }
if (-not $Out) { $Out = Join-Path $root "build\sim" }
New-Item -ItemType Directory -Force $Out | Out-Null
$Out = (Resolve-Path -LiteralPath $Out).ProviderPath

$sources = @((Join-Path $uart "uart_rx.v"), (Join-Path $uart "uart_tx.v"), (Join-Path $uart "sync_fifo.v"),
             (Resolve-Path -LiteralPath $Dut).ProviderPath,
             (Join-Path $root "rtl\basys3_fir4_shell.v"),
             (Join-Path $root "sim\tb_basys3_fir4_shell.v")) | ForEach-Object { $_.Replace('\', '/') }

Push-Location -LiteralPath $Out
try {
    $ErrorActionPreference = "Continue"
    & "$Vivado\xvlog.bat" @sources *> xvlog.txt
    if ($LASTEXITCODE -ne 0) { throw "xvlog failed; see $Out\xvlog.txt" }
    & "$Vivado\xelab.bat" tb_basys3_fir4_shell -s snap_fir4 -debug off *> xelab.txt
    & "$Vivado\xsim.bat" snap_fir4 -R *> xsim.txt
    $verdict = Select-String -Path xsim.txt -Pattern "^(PASS|FAIL)" | Select-Object -Last 1
    $line = if ($verdict) { $verdict.Line } else { "FAIL: no verdict (see xelab.txt)" }
    $line
} finally {
    Pop-Location
}
if ($line -notmatch "^PASS") { throw "simulation failed" }
