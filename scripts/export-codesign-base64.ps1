param(
  [Parameter(Mandatory = $true)]
  [string]$PfxPath,

  [switch]$CopyToClipboard,

  [string]$OutFile
)

if (-not (Test-Path $PfxPath)) {
  throw "PFX file not found: $PfxPath"
}

$base64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes((Resolve-Path $PfxPath)))

if ($OutFile) {
  Set-Content -Path $OutFile -Value $base64 -NoNewline
}

if ($CopyToClipboard) {
  Set-Clipboard -Value $base64
}

Write-Output $base64