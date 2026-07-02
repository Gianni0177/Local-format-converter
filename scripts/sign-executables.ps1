param(
  [string]$CertBase64,

  [string]$CertPassword,

  [Parameter(Mandatory = $true)]
  [string[]]$Targets
)

if (-not $CertBase64) {
  $CertBase64 = $env:CODE_SIGN_CERT_BASE64
}

if (-not $CertPassword) {
  $CertPassword = $env:CODE_SIGN_CERT_PASSWORD
}

if (-not $CertBase64 -or -not $CertPassword) {
  throw "Missing signing credentials"
}

$signtool = Get-ChildItem "${env:ProgramFiles(x86)}\Windows Kits\10\bin" -Recurse -Filter signtool.exe |
  Sort-Object FullName -Descending |
  Select-Object -First 1 -ExpandProperty FullName

if (-not $signtool) {
  throw "signtool.exe not found on the runner"
}

$certPath = Join-Path $env:TEMP "codesign.pfx"
[IO.File]::WriteAllBytes($certPath, [Convert]::FromBase64String($CertBase64))

foreach ($target in $Targets) {
  if (-not (Test-Path $target)) {
    throw "Target not found: $target"
  }

  & $signtool sign /f $certPath /p $CertPassword /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 $target
}