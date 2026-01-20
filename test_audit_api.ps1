# Test audit API endpoint
$loginData = @{
    username = "admin"
    password = "admin123"
} | ConvertTo-Json

$loginResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/login/" -Method Post -Body $loginData -ContentType "application/json"
$token = $loginResponse.access

Write-Host "Token: $($token.Substring(0, 20))..."

Write-Host "`n=== Testing /api/audit/ranking/ ==="
try {
    $headers = @{
        "Authorization" = "Bearer $token"
        "Content-Type" = "application/json"
    }
    
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/audit/ranking/" -Method Get -Headers $headers
    $response | ConvertTo-Json -Depth 10
    
    Write-Host "`nTotal events: $($response.results.Count)"
} catch {
    Write-Host "Error: $_"
    Write-Host $_.Exception.Response.StatusCode
}
