<#
.SYNOPSIS
    Firma digitalmente los ejecutables de PureTrack para Windows con un certificado Code Signing.

.DESCRIPTION
    Crea o utiliza un certificado de firma de código auto-firmado de confianza local
    y aplica la firma Authenticode a dist\PureTrack.exe o dist\PureTrack-Windows-x64.exe.
    Esto mitiga las alertas de "Editor desconocido" (Unknown Publisher) de Windows SmartScreen.
#>

param (
    [string]$TargetExe = "dist\PureTrack.exe"
)

$ErrorActionPreference = "Stop"

Write-Host "======================================================================"
Write-Host ">>> PURETRACK: FIRMA DIGITAL AUTHENTICODE PARA WINDOWS"
Write-Host "======================================================================"

if (-not (Test-Path $TargetExe)) {
    if (Test-Path "dist\PureTrack-Windows-x64.exe") {
        $TargetExe = "dist\PureTrack-Windows-x64.exe"
    } else {
        Write-Error "No se encontró el ejecutable en '$TargetExe'. Compila primero la aplicación."
        exit 1
    }
}

Write-Host "[*] Archivo a firmar: $TargetExe"

# 1. Comprobar si ya existe un certificado local para PureTrack
$certSubject = "CN=PureTrack Open Source Project"
$cert = Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert | Where-Object { $_.Subject -eq $certSubject } | Select-Object -First 1

if (-not $cert) {
    Write-Host "[*] Creando certificado Code Signing local para PureTrack..."
    $cert = New-SelfSignedCertificate `
        -Type CodeSigningCert `
        -Subject $certSubject `
        -CertStoreLocation "Cert:\CurrentUser\My" `
        -HashAlgorithm SHA256 `
        -KeyLength 2048 `
        -NotAfter (Get-Date).AddYears(5)
    
    # Exportar e importar en Root de CurrentUser para que Windows lo reconozca como de confianza
    $tempCertPath = "$env:TEMP\puretrack_cert.cer"
    Export-Certificate -Cert $cert -FilePath $tempCertPath | Out-Null
    Import-Certificate -FilePath $tempCertPath -CertStoreLocation "Cert:\CurrentUser\Root" | Out-Null
    Remove-Item -Path $tempCertPath -Force
    Write-Host "[+] Certificado creado e instalado como entidad de confianza local."
} else {
    Write-Host "[+] Certificado existente detectado: $($cert.Thumbprint)"
}

# 2. Aplicar firma Authenticode
Write-Host "[*] Firmando $TargetExe..."
$sigResult = Set-AuthenticodeSignature -FilePath $TargetExe -Certificate $cert -HashAlgorithm SHA256 -TimestampServer "http://timestamp.digicert.com"

if ($sigResult.Status -eq "Valid") {
    Write-Host "[✓] Ejecutable firmado con éxito (Estado: Válido)."
    Write-Host "    Editor: PureTrack Open Source Project"
    Write-Host "    Algoritmo: SHA256 con timestamp oficial RFC 3161"
} else {
    Write-Host "[!] Firma aplicada con estado: $($sigResult.StatusMessage)"
}

Write-Host "======================================================================"
