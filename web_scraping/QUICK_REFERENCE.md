# 📖 Quick Reference Guide

**Fast lookup for common tasks and commands**

---

## ⚡ Installation (One-Time)

```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Verify setup
python verify_setup.py
```

---

## 🖼️ Usage Scenarios

### Scenario 1: Quick Image Download
```bash
python cli.py "cats" --count 20
```
- Downloads 20 images of cats
- Saves to `cats/` folder
- Uses Bing Images (faster)

### Scenario 2: Specific Image Count
```bash
python cli.py "sunset" --count 100 --source bing
```
- Downloads 100 sunset images
- Slower but more reliable

### Scenario 3: Watch Browser During Scrape
```bash
python cli.py "nature" --show
```
- Shows browser window (helpful for debugging)
- Same result but slower

### Scenario 4: Custom Output Directory
```bash
python cli.py "mountains" --output my_collection/mountains/
```
- Saves images to custom location
- Creates directory if doesn't exist

### Scenario 5: Python Integration
```python
from image_scraper import ImageScraper

scraper = ImageScraper(headless=True)
scraper.initialize_driver()
urls = scraper.scrape_bing_images("query", 50)
scraper.download_images(urls, "query")
scraper.cleanup()
```

### Scenario 6: Batch Multiple Queries
```python
from image_scraper import ImageScraper

scraper = ImageScraper()
scraper.initialize_driver()

queries = ["cats", "dogs", "birds"]
for query in queries:
    urls = scraper.scrape_bing_images(query, 20)
    scraper.download_images(urls, query)

scraper.cleanup()
```

---

## 🎯 Command Matrix

| Goal | Command | Time | Quality |
|------|---------|------|---------|
| Quick 10 images | `python cli.py "cats" --count 10` | 1-2 min | Good |
| Normal 50 images | `python cli.py "dogs" --count 50` | 3-5 min | Excellent |
| Batch 100 images | `python cli.py "birds" --count 100` | 8-12 min | Very Good |
| See what's happening | `python cli.py "cats" --show` | Same + slow | Debug |
| Google Images | `python cli.py "cats" --source google` | 5-10 min | Variable |
| Bing Images | `python cli.py "cats" --source bing` | 3-5 min | Best |

---

## 🔧 Common Configuration Changes

### Speed Up Scraping
```python
# In image_scraper.py, scroll_to_load():
self.scroll_to_load(max_scrolls=5, scroll_pause=1.0)  # Instead of 10, 2.0
```

### Slow Down for Reliability
```python
# In image_scraper.py, scroll_to_load():
self.scroll_to_load(max_scrolls=15, scroll_pause=3.0)  # Slower, more reliable
```

### Different User-Agent
```python
# In UserAgentRotator.get_random_user_agent():
# Add your own user agent to USER_AGENTS list
```

---

## 📊 Troubleshooting Quick Fixes

| Problem | Quick Fix |
|---------|-----------|
| No images found | Try: `cli.py "cats"` (simple query) |
| Timeout errors | Add delay: `time.sleep(3)` before downloading |
| Chrome not found | Install Chrome from google.com |
| Port already in use | Close Chrome: `taskkill /IM chrome.exe /F` |
| Permission error | Run as admin or use `sudo` |
| No space on disk | Delete old images or free up disk |
| Too slow | Use `--count 10` instead of 100 |

---

## 📁 File Locations

```
# Downloaded images
C:\Users\username\Downloads\web_scraping\[query]/

# Log file
C:\Users\username\Downloads\web_scraping\scraper.log

# Configuration
C:\Users\username\Downloads\web_scraping\config.ini
```

---

## 🐛 Debug Mode

```python
# Show browser and logging
scraper = ImageScraper(headless=False)  # Shows browser
import logging
logging.basicConfig(level=logging.DEBUG)  # More verbose logs
```

---

## 📋 Verify Installation Checklist

- [ ] Python 3.8+ installed
- [ ] Virtual environment activated
- [ ] `pip install -r requirements.txt` completed
- [ ] Chrome browser installed
- [ ] `verify_setup.py` shows all green
- [ ] Can run `python cli.py "test" --count 5`
- [ ] Images downloaded to `test/` folder

---

## 🚨 Error Messages & Solutions

### "ModuleNotFoundError: No module named 'selenium'"
```bash
pip install -r requirements.txt
```

### "Chrome not found"
- Install Chrome: https://google.com/chrome

### "ChromeDriver failed to download"
```bash
pip install --upgrade webdriver-manager
```

### "Port 9222 already in use"
```bash
# Windows
taskkill /IM chrome.exe /F

# macOS/Linux
killall chrome
```

### "No such file or directory: 'image_scraper.py'"
```bash
# Make sure you're in correct directory
cd web_scraping
ls  # or 'dir' on Windows
```

---

## 💡 Pro Tips

1. **Start small:** Test with `--count 10` before scraping 100+
2. **Use Bing:** More reliable than Google Images
3. **Check logs:** `cat scraper.log` shows what happened
4. **Batch processing:** Reuse driver for multiple queries (example_2)
5. **Random delays:** Already built in to avoid detection
6. **Organize queries:** Use meaningful folder names
7. **Monitor first run:** Use `--show` to watch it work
8. **Save bandwidth:** Disable browser image loading in config

---

## 📚 File Quick Access

| File | Purpose | When to Read |
|------|---------|--------------|
| README.md | Overview & features | First time |
| SETUP.md | Installation help | Installation issues |
| INDEX.md | File structure | Understanding project |
| config.ini | Settings | Fine-tuning |
| requirements.txt | Dependencies | Installation |

---

## 🕐 Typical Timeline

```
# Scraping 50 images from Bing

Initialization       : 5-10 seconds
Page Load           : 2-4 seconds
Scrolling           : 20-30 seconds
URL Extraction      : 10-20 seconds
Downloading (50x)   : 2-3 minutes
Total               : 3-5 minutes
```

---

## 🔐 Privacy Checklist

- ✓ Images saved locally
- ✓ No automatic uploads
- ✓ Logs don't contain sensitive data
- ✓ Random delays prevent rate limiting
- ✓ Standard HTTPS for all requests

---

## 📞 When Things Go Wrong

1. **Stop and restart:** Keyboard Ctrl+C
2. **Check logs:** `scraper.log` has details
3. **Try simple query:** `cli.py "cat"`
4. **Verify setup:** `verify_setup.py`
5. **Check internet:** `ping google.com`
6. **Read SETUP.md:** Troubleshooting section
7. **Restart computer:** Sometimes helps with ports

---

## 🎓 Learning Path

1. Run: `python cli.py "cats" --count 10`
2. See: Images in `cats/` folder
3. Read: README.md for features
4. Try: `python cli.py "dogs" --count 50`
5. Explore: `python examples.py`
6. Study: `image_scraper.py` source code
7. Customize: Modify for your needs

---

## ⚙️ Performance Tuning

### Faster Scraping
```python
ImageScraper(headless=True)  # vs headless=False
scroll_to_load(max_scrolls=5)  # vs 10
scroll_pause=1.0  # vs 2.0
```

### More Reliable
```python
scroll_to_load(max_scrolls=15)  # vs 10
scroll_pause=3.0  # vs 2.0
ImageScraper(implicit_wait=15)  # vs 10
```

---

## 📖 Documentation Map

```
Start Here
    ↓
  README.md (Overview)
    ↓
  SETUP.md (Installation)
    ↓
  Examples.py (Learn by doing)
    ↓
  cli.py (Use it)
    ↓
  image_scraper.py (Understand it)
    ↓
  config.ini (Customize it)
```

---

## 🞹 Keyboard Shortcuts

| Task | Keys |
|------|------|
| Stop scraping | `Ctrl + C` |
| View logs | `tail -f scraper.log` (macOS/Linux) |
| List files | `ls` (macOS/Linux) or `dir` (Windows) |
| Open file | Your text editor |
| Go back folder | `cd ..` |

---

**Remember:** Check `scraper.log` when things don't work!

```bash
# View last 20 lines of log
tail -20 scraper.log

# Or open in text editor
# Windows: notepad scraper.log
# macOS: open -t scraper.log
# Linux: nano scraper.log
```

---

**Last Updated:** 2024  
**Quick Reference v1.0**
