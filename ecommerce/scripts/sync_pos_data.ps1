param(
    [string]$ApiUrl = "http://localhost:8000/api/v1",
    [string]$Token,
    [int]$BranchId = $null
)

$headers = @{}
if ($Token) {
    $headers["Authorization"] = "Bearer $Token"
}

$url = "$ApiUrl/admin/sync/run"
if ($BranchId) {
    $url += "?branch_id=$BranchId"
}

Write-Host "Triggering POS sync..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri $url -Method Post -Headers $headers -ContentType "application/json"
    Write-Host "Sync completed successfully!" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 3
}
catch {
    Write-Host "Sync failed: $_" -ForegroundColor Red
}
