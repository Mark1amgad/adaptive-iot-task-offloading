param(
    [string]$Inventory = (Join-Path $PSScriptRoot 'runtime\TOPOLOGY_INVENTORY.json'),
    [string]$OutputDirectory = $PSScriptRoot
)

$ErrorActionPreference = 'Stop'
$inventory = Get-Content $Inventory -Raw | ConvertFrom-Json
$devices = @($inventory.devices | Sort-Object level -Descending)
$links = @($inventory.links)
$positions = @{}
$width = 1400
$height = 760
$boxWidth = 330
$boxHeight = 210
$top = 155
$gap = 55
$start = 55
for ($index = 0; $index -lt $devices.Count; $index++) {
    $positions[$devices[$index].name] = @{ x = $start + $index * ($boxWidth + $gap); y = $top }
}

function SafeText([object]$value) {
    if ($null -eq $value) { return 'unknown' }
    return [System.Security.SecurityElement]::Escape([string]$value)
}
function DeviceLabel($device) {
    return "{0} #{1}" -f $device.name, $device.id
}
function BoxText($device) {
    $items = @(
        (DeviceLabel $device),
        ("role: {0}" -f (SafeText $device.role)),
        ("MIPS: {0} | RAM: {1}" -f $device.mips, $device.ram),
        ("PEs: {0} | device BW up/down: {1}/{2}" -f $device.pes, $device.uplink_bandwidth, $device.downlink_bandwidth),
        ("host BW: {0} | storage: {1}" -f $device.host_bandwidth, $device.host_storage),
        ("module: {0}" -f (SafeText $device.module))
    )
    return $items
}

$svg = [System.Text.StringBuilder]::new()
[void]$svg.AppendLine('<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="760" viewBox="0 0 1400 760">')
[void]$svg.AppendLine('<rect width="1400" height="760" fill="#f7f8fa"/>')
[void]$svg.AppendLine('<text x="700" y="42" text-anchor="middle" font-family="Arial" font-size="28" font-weight="bold" fill="#18212b">Runtime iFogSim topology inventory</text>')
[void]$svg.AppendLine('<text x="700" y="72" text-anchor="middle" font-family="Arial" font-size="16" fill="#506070">Generated from TOPOLOGY_INVENTORY.json; Python is external control plane</text>')
foreach ($link in $links) {
    $sourceName = [string]$link.source_device
    $destinationName = [string]$link.destination_device
    $from = $positions[$sourceName]
    $to = $positions[$destinationName]
    $x1 = $from.x + $boxWidth / 2
    $x2 = $to.x + $boxWidth / 2
    $y = $top + $boxHeight
    $latency = SafeText $link.effective_latency_ms
    [void]$svg.AppendLine("<line x1='$x1' y1='$y' x2='$x2' y2='$y' stroke='#506070' stroke-width='4'/>")
    [void]$svg.AppendLine("<text x='$((($x1 + $x2) / 2))' y='$($y - 12)' text-anchor='middle' font-family='Arial' font-size='15' fill='#303b46'>$latency ms; Controller-derived</text>")
}
foreach ($device in $devices) {
    $p = $positions[$device.name]
    $fill = if ($device.role -eq 'cloud_executor') { '#fff0d5' } elseif ($device.role -eq 'edge_executor') { '#e3f4e8' } else { '#dceeff' }
    [void]$svg.AppendLine("<rect x='$($p.x)' y='$($p.y)' width='$boxWidth' height='$boxHeight' rx='12' fill='$fill' stroke='#506070' stroke-width='3'/>")
    $lines = BoxText $device
    for ($lineIndex = 0; $lineIndex -lt $lines.Count; $lineIndex++) {
        $fontSize = if ($lineIndex -eq 0) { 21 } else { 14 }
        $weight = if ($lineIndex -eq 0) { 'font-weight="bold"' } else { '' }
        [void]$svg.AppendLine("<text x='$($p.x + 165)' y='$($p.y + 38 + $lineIndex * 29)' text-anchor='middle' font-family='Arial' font-size='$fontSize' $weight fill='#18212b'>$($lines[$lineIndex])</text>")
    }
}
[void]$svg.AppendLine('<rect x="420" y="485" width="560" height="78" rx="12" fill="#ffffff" stroke="#7a4d9e" stroke-width="3" stroke-dasharray="9,7"/>')
[void]$svg.AppendLine('<text x="700" y="518" text-anchor="middle" font-family="Arial" font-size="18" font-weight="bold" fill="#18212b">Python RL JSONL service</text>')
[void]$svg.AppendLine('<text x="700" y="544" text-anchor="middle" font-family="Arial" font-size="14" fill="#506070">observation -&gt; action -&gt; outcome; external control plane, not a FogDevice</text>')
[void]$svg.AppendLine('<line x1="700" y1="485" x2="700" y2="365" stroke="#7a4d9e" stroke-width="3" stroke-dasharray="9,7"/>')
[void]$svg.AppendLine('<text x="55" y="625" font-family="Arial" font-size="16" font-weight="bold" fill="#18212b">Task paths</text>')
[void]$svg.AppendLine('<text x="55" y="651" font-family="Arial" font-size="14" fill="#303b46">Local: execute at local, no counted parent-child transfer</text>')
[void]$svg.AppendLine('<text x="55" y="675" font-family="Arial" font-size="14" fill="#303b46">Edge: local -&gt; edge input, edge -&gt; local result</text>')
[void]$svg.AppendLine('<text x="55" y="699" font-family="Arial" font-size="14" fill="#303b46">Cloud: local -&gt; edge -&gt; cloud input, then reverse result path</text>')
[void]$svg.AppendLine('<text x="850" y="625" font-family="Arial" font-size="16" font-weight="bold" fill="#18212b">Legend</text>')
[void]$svg.AppendLine('<text x="850" y="651" font-family="Arial" font-size="14" fill="#303b46">MIPS = million instructions per second; RAM/storage = simulator units</text>')
[void]$svg.AppendLine('<text x="850" y="675" font-family="Arial" font-size="14" fill="#303b46">PE = processing element; BW = configured device/host bandwidth</text>')
[void]$svg.AppendLine('<text x="850" y="699" font-family="Arial" font-size="14" fill="#303b46">Latency = effective simulator link latency in ms</text>')
[void]$svg.AppendLine('</svg>')
$svgPath = Join-Path $OutputDirectory 'topology.svg'
[IO.File]::WriteAllText($svgPath, $svg.ToString(), [Text.Encoding]::UTF8)

Add-Type -AssemblyName System.Drawing
$bitmap = New-Object Drawing.Bitmap $width, $height
$graphics = [Drawing.Graphics]::FromImage($bitmap)
$graphics.Clear([Drawing.Color]::FromArgb(247,248,250))
$fontTitle = New-Object Drawing.Font('Arial', 22, [Drawing.FontStyle]::Bold)
$font = New-Object Drawing.Font('Arial', 10)
$brush = [Drawing.Brushes]::Black
$graphics.DrawString('Runtime iFogSim topology inventory', $fontTitle, $brush, 55, 25)
foreach ($device in $devices) {
    $p = $positions[$device.name]
    $rect = New-Object Drawing.Rectangle([int]$p.x, [int]$p.y, $boxWidth, $boxHeight)
    $graphics.FillRectangle([Drawing.Brushes]::White, $rect)
    $graphics.DrawRectangle([Drawing.Pens]::DarkSlateGray, $rect)
    $lines = BoxText $device
    for ($lineIndex = 0; $lineIndex -lt $lines.Count; $lineIndex++) { $graphics.DrawString($lines[$lineIndex], $font, $brush, [float]($p.x + 12), [float]($p.y + 25 + $lineIndex * 29)) }
}
foreach ($link in $links) {
    $sourceName = [string]$link.source_device
    $destinationName = [string]$link.destination_device
    $from = $positions[$sourceName]
    $to = $positions[$destinationName]
    $graphics.DrawLine([Drawing.Pens]::DarkSlateGray, [int]($from.x + $boxWidth / 2), [int]($top + $boxHeight), [int]($to.x + $boxWidth / 2), [int]($top + $boxHeight))
}
$graphics.DrawString('Python RL JSONL service is external control plane; task paths and legend are shown in topology.svg.', $font, $brush, 55, 625)
$pngPath = Join-Path $OutputDirectory 'topology.png'
$bitmap.Save($pngPath, [Drawing.Imaging.ImageFormat]::Png)
$graphics.Dispose(); $bitmap.Dispose()
Write-Host "WROTE $svgPath"
Write-Host "WROTE $pngPath"
