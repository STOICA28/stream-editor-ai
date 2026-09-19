
$peakRAM = 0
$peakDisk = 0
$proxyDir = "data/projects/real-5h-*"

while ($true) {
    $ffmpeg = Get-Process -Name ffmpeg -ErrorAction SilentlyContinue | Sort-Object WorkingSet -Descending | Select-Object -First 1
    if ($ffmpeg) {
        if ($ffmpeg.WorkingSet -gt $peakRAM) { $peakRAM = $ffmpeg.WorkingSet }
    }
    
    $celery = Get-Process -Name celery -ErrorAction SilentlyContinue | Sort-Object WorkingSet -Descending | Select-Object -First 1
    if ($celery) {
        if ($celery.WorkingSet -gt $peakRAM) { $peakRAM = $celery.WorkingSet }
    }

    $files = Get-ChildItem -Path $proxyDir -Recurse -File -ErrorAction SilentlyContinue
    foreach ($f in $files) {
        # ignore source
        if ($f.Name -match "source_5hr.mp4$") { continue }
        if ($f.Length -gt $peakDisk) { $peakDisk = $f.Length }
    }

    $out = "Peak RAM: $([math]::Round($peakRAM / 1MB, 2)) MB`nPeak Disk: $([math]::Round($peakDisk / 1MB, 2)) MB`nLast updated: $(Get-Date)"
    Set-Content -Path monitor_stats.txt -Value $out
    Start-Sleep -Seconds 5
}

