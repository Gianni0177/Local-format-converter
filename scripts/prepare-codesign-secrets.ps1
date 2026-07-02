param(
  [Parameter(Mandatory = $true)]
  [string]$PfxPath,

  [string]$RepoUrl = "https://github.com/Gianni0177/Local-format-converter",

  [switch]$CopyToClipboard,

  [string]$OutFile,

  [switch]$OpenSecretsPage
)

if (-not (Test-Path $PfxPath)) {
  throw "PFX file not found: $PfxPath"
}

$resolvedPfxPath = Resolve-Path $PfxPath
$base64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($resolvedPfxPath))

if ($OutFile) {
  Set-Content -Path $OutFile -Value $base64 -NoNewline
}

if ($CopyToClipboard) {
  Set-Clipboard -Value $base64
}

if ($OpenSecretsPage) {
  Start-Process "$RepoUrl/settings/secrets/actions"
}

Write-Host "CODE_SIGN_CERT_BASE64:"
Write-Output $base64
Write-Host ""
Write-Host "CODE_SIGN_CERT_PASSWORD: inseriscila manualmente come secret GitHub"
Write-Host ""
Write-Host "Pagina secret GitHub: $RepoUrl/settings/secrets/actions"