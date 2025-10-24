# NordVPN CLI Manual Installation Guide

## Method 1: Automated Installation (Recommended)

1. **Open PowerShell as Administrator**
   - Right-click on PowerShell
   - Select "Run as Administrator"

2. **Run the installation script**
   ```powershell
   cd CS2-Scanner
   .\install_nordvpn.ps1
   ```

## Method 2: Manual Installation

### Step 1: Download NordVPN
1. Go to [NordVPN Downloads](https://nordvpn.com/download/)
2. Download the Windows version
3. Run the installer as Administrator

### Step 2: Install NordVPN
1. Run `NordVPNSetup.exe`
2. Follow the installation wizard
3. Complete the installation

### Step 3: Verify Installation
```powershell
nordvpn --version
```

### Step 4: Login to NordVPN
```powershell
nordvpn login
```

## Method 3: Using Chocolatey (Alternative)

If you have Chocolatey installed:

```powershell
choco install nordvpn
```

## Method 4: Using Winget (Windows Package Manager)

```powershell
winget install NordVPN.NordVPN
```

## Verification Steps

After installation, verify everything works:

1. **Check version:**
   ```powershell
   nordvpn --version
   ```

2. **Login to your account:**
   ```powershell
   nordvpn login
   ```

3. **Test connection:**
   ```powershell
   nordvpn connect
   ```

4. **Check status:**
   ```powershell
   nordvpn status
   ```

## Troubleshooting

### If NordVPN CLI is not found:
1. **Restart your terminal**
2. **Add to PATH manually:**
   - Usually installed in: `C:\Program Files\NordVPN\`
   - Add this to your system PATH

### If installation fails:
1. **Run as Administrator**
2. **Disable antivirus temporarily**
3. **Check Windows Defender settings**

### If login fails:
1. **Check your NordVPN account**
2. **Try web login first**
3. **Contact NordVPN support**

## Next Steps

Once NordVPN CLI is installed:

1. **Run the VPN setup script:**
   ```powershell
   python vpn_setup.py
   ```

2. **Or use the advanced analyzer:**
   ```powershell
   python advanced_knife_analyzer.py
   ```

## Benefits for CS2 Market Analysis

- **Rate Limit Evasion**: Different IP addresses for each request
- **Geographic Diversity**: Requests from multiple countries
- **Server Rotation**: Automatic server switching
- **Reduced Blocking**: Lower chance of being rate limited
- **Faster Data Collection**: More reliable API access
