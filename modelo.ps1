param(
    [Parameter(Position=0)]
    [ValidateSet('ayuda','actualizar','cotizaciones','calcular','analisis','todo','estado','pruebas','motor','preparar-bonos','bonos','bonos-vivo','dashboard')]
    [string]$Accion = 'estado',
    [ValidateSet('bonos60','libre')]
    [string]$Perfil = 'bonos60',
    [double]$Patrimonio = 0,
    [double]$MaximoHistorico = 0,
    [ValidateSet('ON','OFF')]
    [string]$Opciones,
    [ValidateSet('ON','OFF')]
    [string]$Cauciones,
    [ValidateSet('ON','OFF')]
    [string]$Bonos
)

[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding = [Console]::OutputEncoding
$env:PYTHONIOENCODING = 'utf-8'

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = Join-Path $ProjectDir '.venv\Scripts\python.exe'
$BundledPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (Test-Path -LiteralPath $VenvPython) {
    $PythonExe = $VenvPython
} elseif (Test-Path -LiteralPath $BundledPython) {
    $PythonExe = $BundledPython
} else {
    $PythonCommand = Get-Command python -ErrorAction Stop
    $PythonExe = $PythonCommand.Source
}
$Today = Get-Date
$StartDate = $Today.AddDays(-1100).ToString('yyyy-MM-dd')
$EndExclusive = $Today.AddDays(1).ToString('yyyy-MM-dd')
$ProfileConfig = if ($Perfil -eq 'bonos60') { 'config\bonos60.json' } else { 'config\default.json' }

function Update-History {
    & $PythonExe -m byma_quant download `
        --start $StartDate `
        --end $EndExclusive `
        --max-assets 45 `
        --output data
    if ($LASTEXITCODE -ne 0) { throw 'Falló la actualización histórica. Revisá data\download_status.csv.' }
}

function Update-Quotes {
    param([switch]$AllowCached)
    & $PythonExe -m byma_quant quotes --output data
    if ($LASTEXITCODE -ne 0) {
        if ($AllowCached -and (Test-Path -LiteralPath 'data\current_execution_quotes.csv')) {
            Write-Warning 'No hubo una descarga de puntas válida; el cálculo continuará con el último snapshot preservado.'
            return
        }
        throw 'Falló la actualización automática de cotizaciones. Se conservó el snapshot anterior.'
    }
}

function Update-LiveBonds {
    param([switch]$AllowFailure)
    $BondArgs = @(
        '-m', 'byma_quant', 'bond-live',
        '--symbols', 'data\fixed_income\live_symbols.csv',
        '--data-dir', 'data\fixed_income',
        '--database', 'data\fixed_income\bonds.sqlite',
        '--ccl', 'data\implied_ccl.csv'
    )
    $BackfillReady = $false
    if (Test-Path -LiteralPath 'data\fixed_income\history.csv') {
        $HistoryRows = @(Import-Csv 'data\fixed_income\history.csv')
        $ReadyTickers = @($HistoryRows | Group-Object ticker | Where-Object Count -ge 66 |
            Select-Object -ExpandProperty Name)
        $BackfillReady = (@('AL30','GD30','TX26') | Where-Object { $_ -notin $ReadyTickers }).Count -eq 0
    }
    if (-not $BackfillReady) {
        $BondHistoryStart = $Today.AddDays(-240).ToString('yyyy-MM-dd')
        $BondHistoryEnd = $Today.ToString('yyyy-MM-dd')
        $BondArgs += @('--history-from', $BondHistoryStart, '--history-to', $BondHistoryEnd)
        Write-Host 'BONOS: primera carga; se descargarán 240 días de historia para el modelo.' -ForegroundColor Cyan
    } else {
        $BondArgs += @('--history-from', $Today.AddDays(-7).ToString('yyyy-MM-dd'),
                       '--history-to', $Today.ToString('yyyy-MM-dd'))
    }
    & $PythonExe @BondArgs
    if ($LASTEXITCODE -ne 0) {
        if ($AllowFailure) {
            Write-Warning 'Primary API no actualizó bonos; se descartan puntas vencidas y continúa el modelo.'
            return
        }
        throw 'Falló la actualización de bonos en Primary API. Revisá data\fixed_income\live_errors.csv.'
    }
    if (Test-Path -LiteralPath 'data\fixed_income\live_errors.csv') {
        $BondErrors = @(Import-Csv 'data\fixed_income\live_errors.csv')
        if ($BondErrors.Count -gt 0) {
            Write-Warning "Primary actualizó parcialmente: $($BondErrors.Count) errores. Revisá data\fixed_income\live_errors.csv."
        }
    }
}

function Prepare-BondContracts {
    & $PythonExe -m byma_quant bond-contracts --data-dir 'data\fixed_income' --config $ProfileConfig
    if ($LASTEXITCODE -ne 0) { throw 'Falló la construcción de fichas y flujos de bonos.' }
}

function Update-LiveBondsIfConfigured {
    if ($env:PRIMARY_USERNAME -and $env:PRIMARY_PASSWORD) {
        Update-LiveBonds -AllowFailure
    } else {
        Write-Host 'BONOS: Primary no está configurado; se usan sólo datos locales verificados.' -ForegroundColor Yellow
    }
}

function Calculate-Portfolio {
    param([switch]$FullAnalysis)
    $ModelArgs = @(
        '-m', 'byma_quant', 'run',
        '--config', $ProfileConfig,
        '--prices', 'data\historical_prices.csv',
        '--positions', 'data\current_positions.csv',
        '--options', 'data\options_clean.csv',
        '--ccl', 'data\implied_ccl.csv',
        '--execution-snapshot', 'data\current_execution_quotes.csv',
        '--equity', $Patrimonio,
        '--peak-equity', $MaximoHistorico,
        '--output', 'output\real'
    )
    if ($Opciones) { $ModelArgs += @('--options-mode', $Opciones.ToLowerInvariant()) }
    if ($Cauciones) { $ModelArgs += @('--cauciones-mode', $Cauciones.ToLowerInvariant()) }
    if ($Bonos) { $ModelArgs += @('--bonds-mode', $Bonos.ToLowerInvariant()) }
    if ($FullAnalysis) { $ModelArgs += '--full-analysis' }
    & $PythonExe @ModelArgs
    if ($LASTEXITCODE -ne 0) { throw 'El modelo rechazó la cartera. Revisá output\real\risk_report.json.' }
}

function Show-ModelHelp {
    Write-Host 'MODELO DE FINANZAS - PERFIL BONOS 60%' -ForegroundColor Cyan
    Write-Host '  60% bonos / hasta 35% otros activos / desde 5% caja'
    Write-Host '  Si faltan bonos aptos, la diferencia queda en caja y se informa.'
    Write-Host '  .\modelo.cmd calcular -Perfil libre   usa el perfil anterior'
    Write-Host 'Uso diario:'
    Write-Host '  .\modelo.cmd calcular           actualiza puntas y calcula la cartera'
    Write-Host '  .\modelo.cmd estado             muestra cartera, órdenes y estado de bonos'
    Write-Host '  .\modelo.cmd dashboard          abre el panel interactivo'
    Write-Host ''
    Write-Host 'Primera configuración de bonos:'
    Write-Host '  $env:PRIMARY_USERNAME = "usuario"'
    Write-Host '  $env:PRIMARY_PASSWORD = "clave"'
    Write-Host '  PRIMARY_BASE_URL y PRIMARY_HISTORY_ENVIRONMENT: ver GUIA_USO.md'
    Write-Host '  .\modelo.cmd bonos-vivo          arma contratos y hace el backfill inicial'
    Write-Host '  .\modelo.cmd calcular -Bonos ON'
    Write-Host ''
    Write-Host 'Revisión:'
    Write-Host '  .\modelo.cmd bonos              explica cobertura y faltantes'
    Write-Host '  .\modelo.cmd analisis           recalcula validación histórica'
    Write-Host '  .\modelo.cmd pruebas            ejecuta los controles automáticos'
    Write-Host ''
    Write-Host 'Guía completa: GUIA_USO.md' -ForegroundColor Green
}

Set-Location -LiteralPath $ProjectDir
switch ($Accion) {
    'ayuda'        { Show-ModelHelp; exit 0 }
    'actualizar'    { Update-History; Update-Quotes }
    'cotizaciones' { Update-Quotes }
    'calcular'      { Prepare-BondContracts; Update-Quotes -AllowCached; Update-LiveBondsIfConfigured; Calculate-Portfolio }
    'analisis'      { Prepare-BondContracts; Update-Quotes -AllowCached; Update-LiveBondsIfConfigured; Calculate-Portfolio -FullAnalysis }
    'todo'          { Update-History; Prepare-BondContracts; Update-Quotes -AllowCached; Update-LiveBondsIfConfigured; Calculate-Portfolio -FullAnalysis }
    'pruebas'    { & $PythonExe -m unittest discover -s tests -v; exit $LASTEXITCODE }
    'motor'       { & $PythonExe -m byma_quant engine-status }
    'preparar-bonos' { Prepare-BondContracts; exit 0 }
    'bonos'       { Prepare-BondContracts; & $PythonExe -m byma_quant bonds --config $ProfileConfig; exit $LASTEXITCODE }
    'bonos-vivo'  { Prepare-BondContracts; Update-LiveBonds; exit 0 }
    'dashboard'   { & $PythonExe -m streamlit run app.py --server.address 127.0.0.1; exit $LASTEXITCODE }
    'estado' {
        if (Test-Path output\real\risk_report.json) {
            $CurrentReport = Get-Content output\real\risk_report.json -Raw | ConvertFrom-Json
            if ($CurrentReport.allocation.policy.enabled) {
                $Allocation = $CurrentReport.allocation
                Write-Host ("MANDATO BONOS: objetivo {0:P0} | propuesta {1:P2} | {2}" -f `
                    $Allocation.target_bond_weight, $Allocation.proposed_bond_weight, $Allocation.status) -ForegroundColor Cyan
                Write-Host ("Faltante de bonos reservado en caja: ARS {0:N0}" -f $Allocation.bond_shortfall_ars)
            }
        }
        if (Test-Path output\real\risk_report.json) {
            $RiskState = Get-Content output\real\risk_report.json -Raw | ConvertFrom-Json
            if ($RiskState.instrument_modes) {
                $OptionsLabel = if ($RiskState.instrument_modes.options) { 'ON' } else { 'OFF' }
                $CaucionesLabel = if ($RiskState.instrument_modes.cauciones) { 'ON' } else { 'OFF' }
                $BonosLabel = if ($RiskState.instrument_modes.bonds) { 'ON' } else { 'OFF' }
                Write-Host "MODALIDADES: Opciones $OptionsLabel | Cauciones $CaucionesLabel | Bonos $BonosLabel" -ForegroundColor Cyan
            }
        }
        Write-Host 'CARTERA OBJETIVO' -ForegroundColor Cyan
        Import-Csv output\real\target_portfolio.csv |
            Select-Object ticker,asset_type,
                @{Name='peso';Expression={ '{0:P2}' -f [double]$_.target_weight }},
                @{Name='valor_ARS';Expression={ '{0:N0}' -f [double]$_.target_value }},
                target_quantity,reason |
            Format-Table -AutoSize
        Write-Host 'ORDENES PROPUESTAS' -ForegroundColor Cyan
        Import-Csv output\real\orders.csv |
            Select-Object ticker,side,quantity,
                @{Name='precio_ref';Expression={ '{0:N2}' -f [double]$_.reference_price }},
                @{Name='importe_ARS';Expression={ '{0:N0}' -f [double]$_.gross_value }},reason |
            Format-Table -AutoSize
        if (Test-Path output\real\factor_exposure.csv) {
            Write-Host 'DIVERSIFICACION POR FACTOR' -ForegroundColor Cyan
            Import-Csv output\real\factor_exposure.csv |
                Select-Object economic_factor,
                    @{Name='peso';Expression={ '{0:P2}' -f [double]$_.target_weight }},
                    @{Name='valor_ARS';Expression={ '{0:N0}' -f [double]$_.target_value }} |
                Format-Table -AutoSize
        }
        if (Test-Path output\real\bond_report.json) {
            $BondState = Get-Content output\real\bond_report.json -Raw | ConvertFrom-Json
            Write-Host 'ESTADO DE BONOS' -ForegroundColor Cyan
            Write-Host ("Contratos: {0} | Historia: {1} | TIR: {2} | Elegibles: {3}" -f `
                $BondState.verified_instruments, $BondState.history_rows, `
                $BondState.yield_rows, $BondState.eligible_with_inputs)
            if (Test-Path output\real\bond_signals.csv) {
                Import-Csv output\real\bond_signals.csv |
                    Select-Object ticker,family,fi_status,fi_strategy |
                    Format-Table -AutoSize
            }
        }
        if (Test-Path output\real\execution_quote_gaps.csv) {
            $MissingQuotes = @(Import-Csv output\real\execution_quote_gaps.csv)
            if ($MissingQuotes.Count -gt 0) {
                Write-Host "ATENCION: hay $($MissingQuotes.Count) ordenes todavia no ejecutables." -ForegroundColor Yellow
                $MissingQuotes |
                    Select-Object ticker,asset_type,side,quote_required,quote_quality,quote_rejection |
                    Format-Table -AutoSize
            }
        }
    }
}
