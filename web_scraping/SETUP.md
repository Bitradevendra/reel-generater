# ⚙️ Setup Guide & Installation Tutorial

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Step-by-Step Installation](#step-by-step-installation)
3. [Verification](#verification)
4. [Troubleshooting](#troubleshooting)
5. [Chrome WebDriver Setup](#chrome-webdriver-setup)
6. [First Run Guide](#first-run-guide)

---

## Prerequisites

### System Requirements
- **OS**: Windows 10+ / macOS 10.13+ / Linux (Ubuntu 18.04+)
- **Python**: 3.8 or higher (recommend 3.10+)
- **Chrome**: Version 90+ (latest recommended)
- **RAM**: 2GB minimum, 4GB+ recommended
- **Disk Space**: 500MB for Python + dependencies + images

### Check Your System

**Check Python Version:**
```bash
python --version
```

Expected output: `Python 3.8.0` or higher

**Check Chrome Version:**
1. Open Chrome
2. Click Menu (⋮) → Help → About Google Chrome
3. Note the version number (should be 90+)

**Check Internet Connection:**
```bash
ping google.com
```

---

## Step-by-Step Installation

### Step 1: Create Project Directory

**Windows (PowerShell):**
```powershell
mkdir C:\Users\$env:USERNAME\Downloads\web_scraping
cd C:\Users\$env:USERNAME\Downloads\web_scraping
```

**macOS/Linux (Terminal):**
```bash
mkdir ~/Downloads/web_scraping
cd ~/Downloads/web_scraping
```

### Step 2: Create Virtual Environment

**Why virtual environment?**
- Isolates project dependencies
- Avoids conflicts with other Python projects
- Easy to manage and remove

**Windows (PowerShell/CMD):**
```bash
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` prefix in your terminal:
```
(venv) C:\Users\...\web_scraping>
```

**macOS/Linux (Terminal):**
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` prefix:
```
(venv) user@computer web_scraping %
```

### Step 3: Upgrade pip

**All Systems:**
```bash
python -m pip install --upgrade pip
```

Expected: Shows successful upgrade with version number

### Step 4: Install Dependencies

Download the files from the repository and place them in your project directory:
- `image_scraper.py`
- `requirements.txt`
- `cli.py`
- `examples.py`
- `README.md`

Then install:
```bash
pip install -r requirements.txt
```

**What gets installed:**
```
selenium==4.15.2          # Browser automation
requests==2.31.0         # HTTP requests
urllib3==2.1.0           # HTTP utilities
webdriver-manager==4.0.1 # ChromeDriver management
```

⏱️ Installation time: 2-5 minutes depending on internet speed

### Step 5: Verify Installation

**Test imports:**
```bash
python -c "import selenium; import requests; from webdriver_manager.chrome import ChromeDriverManager; print('✓ All packages imported successfully')"
```

**Expected output:**
```
✓ All packages imported successfully
```

**Test ChromeDriver installation:**
```bash
python -c "from webdriver_manager.chrome import ChromeDriverManager; print(ChromeDriverManager().install())"
```

Expected: Path to ChromeDriver executable

---

## Verification

### Full System Check

Create a file `verify_setup.py`:

```python
import sys
import os
from pathlib import Path

print("\n" + "="*60)
print("SYSTEM VERIFICATION")
print("="*60)

# Python Version
print(f"\n✓ Python Version: {sys.version.split()[0]}")
assert sys.version_info >= (3, 8), "Python 3.8+ required"

# Chrome Check
try:
    from webdriver_manager.chrome import ChromeDriverManager
    driver_path = ChromeDriverManager().install()
    print(f"✓ ChromeDriver: {driver_path}")
except Exception as e:
    print(f"✗ ChromeDriver Error: {e}")

# Required Packages
packages = ['selenium', 'requests', 'webdriver_manager', 'urllib3']
print(f"\n✓ Installed Packages:")
for pkg in packages:
    try:
        __import__(pkg)
        print(f"  ✓ {pkg}")
    except ImportError:
        print(f"  ✗ {pkg} (MISSING)")

# Virtual Environment
in_venv = hasattr(sys, 'real_prefix') or (
    hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
)
print(f"\n✓ Virtual Environment: {'Yes' if in_venv else 'No (recommend using venv)'}")

# Disk Space
import shutil
_, _, free = shutil.disk_usage("/")
free_gb = free / (1024**3)
print(f"✓ Free Disk Space: {free_gb:.2f} GB")

# Home Directory
print(f"✓ Home Directory: {Path.home()}")

print("\n" + "="*60)
print("VERIFICATION COMPLETE")
print("="*60 + "\n")
```

Run it:
```bash
python verify_setup.py
```

---

## Troubleshooting

### Problem: "Python command not found"

**Windows:**
1. Open Environment Variables:
   - Press `Win + X` → System
   - Click "Advanced system settings"
   - Click "Environment Variables..."
2. Check if Python is in PATH
3. Reinstall Python (check "Add Python to PATH")

**macOS/Linux:**
```bash
# Use python3 explicitly
python3 --version
# Create alias in ~/.bash_profile or ~/.zshrc
alias python=python3
```

### Problem: "venv not found" or "module venv not found"

**Solution:**
```bash
# Windows
python -m venv venv

# macOS/Linux
python3 -m venv venv
```

If still fails, install venv:
```bash
# Ubuntu/Debian
sudo apt-get install python3-venv

# macOS (with Homebrew)
brew install python3
```

### Problem: "Permission denied" on macOS/Linux

**Solution:**
```bash
chmod +x venv/bin/activate
source venv/bin/activate
```

### Problem: "pip install fails with SSL error"

**Solution 1: Update certificates**
```bash
# macOS
/Applications/Python\ 3.x/Install\ Certificates.command

# Windows
python -m pip install --upgrade certifi
```

**Solution 2: Disable SSL verification (not recommended)**
```bash
pip install --trusted-host pypi.python.org -r requirements.txt
```

### Problem: "ChromeDriver fails to download"

**Symptoms:**
- "Max retries exceeded"
- "Failed to download ChromeDriver"

**Solutions:**

1. **Manual download:**
   - Visit: https://chromedriver.chromium.org/
   - Download matching your Chrome version
   - Extract to: `C:\Users\<username>\AppData\Local\webdriver_manager\` (Windows)

2. **Use proxy:**
   ```python
   os.environ['WDM_PROXY'] = 'http://proxy:port'
   ```

3. **Increase timeout:**
   ```bash
   pip install --upgrade webdriver-manager
   ```

### Problem: "Chrome not found" or "Chrome not installed"

**Windows:**
1. Install Chrome from: https://www.google.com/chrome/
2. Verify installation:
   ```powershell
   Test-Path "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
   ```

**macOS:**
```bash
# Check if Chrome is installed
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version

# If not installed
brew install google-chrome
```

**Linux:**
```bash
# Ubuntu/Debian
sudo apt-get install chromium-browser

# Or Google Chrome
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
sudo apt-get install google-chrome-stable
```

### Problem: "Port 9222 already in use"

**Cause:** Chrome or another process is using the port

**Solution:**
```bash
# Windows (PowerShell)
Get-Process chrome | Stop-Process -Force

# macOS/Linux
killall chrome
# or
pkill -9 chrome
```

### Problem: "Stale element reference" errors

**Cause:** DOM elements are changing during iteration

**Solution:** Already handled in code, but if you see this:
- Check internet stability
- Use: `scroll_pause=3.0` (increase delay)
- Reduce target_count temporarily

### Problem: No images downloaded

**Check in order:**
1. **Review logs:**
   ```bash
   cat scraper.log
   ```

2. **Test web access:**
   ```bash
   python -c "import requests; print(requests.get('https://www.bing.com').status_code)"
   ```

3. **Try without headless:**
   ```python
   scraper = ImageScraper(headless=False)
   ```

4. **Try different query:**
   ```python
   main("cat", target_count=5)
   ```

---

## Chrome WebDriver Setup

### Automatic Setup (Recommended)

webdriver-manager handles everything automatically:

```python
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
```

**First run downloads ChromeDriver to:**
- Windows: `C:\Users\<user>\AppData\Local\webdriver_manager\`
- macOS: `~/Library/Caches/webdriver_manager/`
- Linux: `~/.wdm/`

### Manual Setup (Advanced)

If automatic fails:

1. **Find your Chrome version:**
   - Open Chrome
   - Press `Ctrl+Shift+I` (Developer Tools)
   - Go to Console
   - Type: `navigator.userAgent`
   - Note the version number

2. **Download matching ChromeDriver:**
   - Visit: https://chromedriver.chromium.org/downloads
   - Download version matching your Chrome
   - Extract `chromedriver.exe` (Windows) or `chromedriver` (macOS/Linux)

3. **Add to project:**
   ```
   web_scraping/
   ├── image_scraper.py
   ├── chromedriver.exe (or chromedriver)
   └── requirements.txt
   ```

4. **Update code:**
   ```python
   from selenium.webdriver.chrome.service import Service
   
   driver = webdriver.Chrome(service=Service('./chromedriver'))
   ```

---

## First Run Guide

### Quick Start

1. **Activate virtual environment:**
   ```bash
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

2. **Run simple example:**
   ```bash
   python cli.py "cats" --count 10 --source bing
   ```

3. **Wait for completion:**
   - Logs will show progress
   - Images saved to `cats/` folder
   - Use `--show` flag to see browser

### Running Examples

1. **Interactive menu:**
   ```bash
   python examples.py
   ```

2. **Specific example:**
   ```python
   from examples import example_1_simple_scrape
   example_1_simple_scrape()
   ```

3. **Python script:**
   ```python
   from image_scraper import main
   
   main(
       query="Eiffel Tower",
       target_count=30,
       source='bing',
       headless=True
   )
   ```

### Monitoring First Run

**Watch the logs:**
```bash
# Windows (PowerShell)
Get-Content scraper.log -Wait

# macOS/Linux
tail -f scraper.log
```

**Browser window:**
```python
scraper = ImageScraper(headless=False)  # Shows browser
```

**Expected timeline for 30 images:**
- Initialization: 5-10 seconds
- Scrolling: 20-30 seconds
- Downloading: 1-3 minutes
- **Total: 2-4 minutes**

---

## Next Steps

After successful setup:

1. **Read README.md** for detailed documentation
2. **Explore examples.py** for different use cases
3. **Review scraper.log** to understand operation
4. **Customize settings** based on your needs
5. **Batch process** multiple queries

---

## Support

**Still having issues?**

1. Check troubleshooting section above
2. Review `scraper.log` file
3. Run `verify_setup.py`
4. Ensure Chrome is latest version
5. Try a simple query like "cats"

**Common causes:**
- ❌ Old Python version → Update Python
- ❌ Missing Chrome → Install Chrome
- ❌ Internet issues → Check connection
- ❌ Firewall blocking → Check firewall/VPN
- ❌ Incompatible pip version → Run `pip install --upgrade pip`

---

**You're all set! Happy scraping! 🚀**
