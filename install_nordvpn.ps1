# NordVPN CLI Installation Script for PowerShell
# This script will download and install NordVPN CLI on Windows

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "NordVPN CLI Installation Script" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "This script requires administrator privileges." -ForegroundColor Red
    Write-Host "Please run PowerShell as Administrator and try again." -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "✓ Running as Administrator" -ForegroundColor Green

# Check if NordVPN is already installed
try {
    $nordvpnVersion = & nordvpn --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ NordVPN CLI is already installed: $nordvpnVersion" -ForegroundColor Green
        Write-Host "You can now use the VPN setup script!" -ForegroundColor Green
        Read-Host "Press Enter to exit"
        exit 0
    }
} catch {
    Write-Host "NordVPN CLI not found, proceeding with installation..." -ForegroundColor Yellow
}

# Download NordVPN installer
Write-Host "`nDownloading NordVPN installer..." -ForegroundColor Yellow

$downloadUrl = "https://downloads.nordcdn.com/apps/windows/10/NordVPN/NordVPNSetup.exe"
$installerPath = "$env:TEMP\NordVPNSetup.exe"

try {
    Invoke-WebRequest -Uri $downloadUrl -OutFile $installerPath -UseBasicParsing
    Write-Host "✓ Download completed" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to download NordVPN installer" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Install NordVPN
Write-Host "`nInstalling NordVPN..." -ForegroundColor Yellow
Write-Host "This may take a few minutes. Please wait..." -ForegroundColor Yellow

try {
    # Run installer silently
    $process = Start-Process -FilePath $installerPath -ArgumentList "/S" -Wait -PassThru
    
    if ($process.ExitCode -eq 0) {
        Write-Host "✓ NordVPN installation completed successfully!" -ForegroundColor Green
    } else {
        Write-Host "⚠ NordVPN installation completed with warnings (Exit code: $($process.ExitCode))" -ForegroundColor Yellow
    }
} catch {
    Write-Host "✗ Failed to install NordVPN" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Clean up installer
Remove-Item $installerPath -Force -ErrorAction SilentlyContinue

# Verify installation
Write-Host "`nVerifying installation..." -ForegroundColor Yellow

# Wait a moment for installation to complete
Start-Sleep -Seconds 5

try {
    $nordvpnVersion = & nordvpn --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ NordVPN CLI installed successfully!" -ForegroundColor Green
        Write-Host "Version: $nordvpnVersion" -ForegroundColor Green
        
        # Test login prompt
        Write-Host "`nNext steps:" -ForegroundColor Cyan
        Write-Host "1. You'll need to log in to your NordVPN account" -ForegroundColor White
        Write-Host "2. Run: nordvpn login" -ForegroundColor White
        Write-Host "3. Or use the VPN setup script: python vpn_setup.py" -ForegroundColor White
        
    } else {
        Write-Host "⚠ NordVPN installed but CLI not accessible" -ForegroundColor Yellow
        Write-Host "You may need to restart your terminal or add NordVPN to PATH" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠ Could not verify NordVPN installation" -ForegroundColor Yellow
    Write-Host "Please try running 'nordvpn --version' manually" -ForegroundColor Yellow
}

Write-Host "`n================================================" -ForegroundColor Cyan
Write-Host "Installation script completed!" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

Read-Host "Press Enter to exit"