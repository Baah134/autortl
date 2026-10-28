# Runs the three self-checking testbench scenarios in xsim and fails if any
# does not print PASS. Generics go through xelab option files because the
# Vivado .bat wrappers split command-line arguments at '='.
#   powershell -File scripts/run_sims.ps1 [-Vivado C:\AMDDesignTools\2025.2\Vivado\bin] [-Out build/sim]
param(
    [string]$Vivado = "C:\AMDDesignTools\2025.2\Vivado\bin",
    [string]$Out = ""
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
if (-not $Out) { $Out = Join-Path $root "build\sim" }
New-Item -ItemType Directory -Force $Out | Out-Null
$Out = (Resolve-Path -LiteralPath $Out).ProviderPath

$sources = @("rtl/uart_rx.v", "rtl/uart_tx.v", "rtl/sync_fifo.v", "rtl/basys3_uart_echo.v",
             "sim/tb_basys3_uart_echo.v") | ForEach-Object { (Join-Path $root $_).Replace('\', '/') }
$cases = [ordered]@{
    "mode0_exact"   = @("MODE=0", "CPB=16", "N=64")
    "mode1_fast0p5" = @("MODE=1", "CPB=400", "SEND_CPB=398", "N=1500", "FIFO_LOG2=1")
    "mode2_fast3p1" = @("MODE=2", "CPB=64", "SEND_CPB=62", "N=800")
}

Push-Location -LiteralPath $Out
try {
    $ErrorActionPreference = "Continue"
    & "$Vivado\xvlog.bat" @sources *> xvlog.txt
    if ($LASTEXITCODE -ne 0) { throw "xvlog failed; see $Out\xvlog.txt" }
    $failed = 0
    foreach ($name in $cases.Keys) {
        $opts = @("tb_basys3_uart_echo", "-s", "snap_$name", "-debug", "off") +
                ($cases[$name] | ForEach-Object { "-generic_top `"$_`"" })
        $opts -join "`n" | Out-File -Encoding ascii "xelab_$name.opt"
        & "$Vivado\xelab.bat" -f "xelab_$name.opt" *> "xelab_$name.txt"
        & "$Vivado\xsim.bat" "snap_$name" -R *> "xsim_$name.txt"
        $verdict = Select-String -Path "xsim_$name.txt" -Pattern "^(PASS|FAIL)" | Select-Object -Last 1
        $line = if ($verdict) { $verdict.Line } else { "FAIL: no verdict (see xelab_$name.txt)" }
        "${name}: $line"
        if ($line -notmatch "^PASS") { $failed++ }
    }
} finally {
    Pop-Location
}
if ($failed) { throw "$failed simulation scenario(s) failed" }
