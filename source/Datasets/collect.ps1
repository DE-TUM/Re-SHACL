Get-Content 'EnDe-Lite50(without_Ontology).ttl' | ForEach-Object -Begin { $i = 0 } -Process {
    if ($i -ge 658912 -and $i -le 658932) {
        Write-Host "${i}: $_"
    }
    $i++
}
