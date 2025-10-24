# Quick NordVPN Installation Script
Write-Host "NordVPN CLI Installation Helper" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

Write-Host "`nThis script will help you install NordVPN CLI" -ForegroundColor Yellow
Write-Host "Please follow these steps:" -ForegroundColor White

Write-Host "`n1. Download NordVPN:" -ForegroundColor Green
Write-Host "   - Go to: https://nordvpn.com/download/" -ForegroundColor White
Write-Host "   - Select 'Windows' and download the installer" -ForegroundColor White

Write-Host "`n2. Install NordVPN:" -ForegroundColor Green
Write-Host "   - Run the installer as Administrator" -ForegroundColor White
Write-Host "   - Follow the installation wizard" -ForegroundColor White

Write-Host "`n3. Verify Installation:" -ForegroundColor Green
Write-Host "   - Open PowerShell as Administrator" -ForegroundColor White
Write-Host "   - Run: nordvpn --version" -ForegroundColor White

Write-Host "`n4. Login to NordVPN:" -ForegroundColor Green
Write-Host "   - Run: nordvpn login" -ForegroundColor White
Write-Host "   - Follow the login instructions" -ForegroundColor White

Write-Host "`n5. Test the VPN setup script:" -ForegroundColor Green
Write-Host "   - Run: python vpn_setup.py" -ForegroundColor White

Write-Host "`nAlternative: Use Windows Package Manager" -ForegroundColor Yellow
Write-Host "Run this command in PowerShell as Administrator:" -ForegroundColor White
Write-Host "winget install NordVPN.NordVPN" -ForegroundColor Cyan

Read-Host "`nPress Enter to continue"
