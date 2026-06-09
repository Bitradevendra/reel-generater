# 🖼️ Robust Image Scraping System

A production-grade image scraper using Selenium and Requests with advanced bot detection bypass, lazy-load handling, and comprehensive error management.

## 📋 Features

✅ **Multi-Source Support**: Google Images, Bing Images  
✅ **Bot Detection Bypass**: Random User-Agent rotation, Chrome options stealth  
✅ **Lazy-Load Handling**: Automatic scroll-to-load implementation  
✅ **Original URL Extraction**: Fetches full-resolution image sources  
✅ **Robust Error Handling**: Try-except blocks for network, timeout, and element errors  
✅ **Automatic Driver Management**: webdriver-manager handles ChromeDriver installation  
✅ **Session Management**: Retry logic and connection pooling with requests  
✅ **Comprehensive Logging**: File and console logging with detailed information  
✅ **Organized Output**: Images saved as `[query]_[index].jpg`  

## 🛠️ Prerequisites

### System Requirements
- **Python**: 3.8+ (3.10+ recommended)
- **Chrome**: Latest version installed
- **OS**: Windows, macOS, or Linux
- **RAM**: 2GB minimum
- **Internet**: Active connection required

### Check Python Version
```bash
python --version
```

## 📦 Installation & Setup

### Step 1: Clone/Download Repository
```bash
cd web_scraping
```

### Step 2: Create Virtual Environment (Recommended)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**What gets installed:**
- `selenium` - Browser automation
- `requests` - HTTP library for image downloads
- `webdriver-manager` - Automatic ChromeDriver installation
- `urllib3` - HTTP client with retry logic

### Step 4: Verify Installation
```bash
python -c "import selenium; import requests; import webdriver_manager; print('✓ All packages installed correctly')"
```

## 🚀 Quick Start

### Basic Usage
```bash
python image_scraper.py "python programming"
```

### Using Python Script
```python
from image_scraper import ImageScraper

scraper = ImageScraper(headless=True)
try:
    scraper.initialize_driver()
    
    # Scrape from Bing Images (recommended)
    urls = scraper.scrape_bing_images("sunset photography", target_count=50)
    
    # Download images
    scraper.download_images(urls, "sunset_photography")
finally:
    scraper.cleanup()
```

## 📝 Usage Examples

### Example 1: Scrape and Download 100 Mountain Images
```python
from image_scraper import main

main(
    query="mountain landscape",
    target_count=100,
    source='bing',
    headless=True
)
```

### Example 2: Custom Implementation
```python
from image_scraper import ImageScraper

scraper = ImageScraper(headless=False)  # Show browser
scraperInitialize_driver()

# Scrape from Google Images
urls = scraper.scrape_google_images("nature", target_count=30)

# Download to custom directory
scraper.download_images(urls, "nature", output_dir="my_images/nature")

scraper.cleanup()
```

### Example 3: Batch Processing
```python
from image_scraper import ImageScraper

queries = ["cats", "dogs", "birds", "fish"]
scraper = ImageScraper(headless=True)

try:
    scraper.initialize_driver()
    
    for query in queries:
        urls = scraper.scrape_bing_images(query, target_count=20)
        scraper.download_images(urls, query)
        
finally:
    scraper.cleanup()
```

## 📂 Output Structure

```
web_scraping/
├── image_scraper.py
├── requirements.txt
├── README.md
├── scraper.log
├── python_programming/          # Query-specific folder
│   ├── python_programming_0001.jpg
│   ├── python_programming_0002.jpg
│   └── ...
└── sunset_photography/
    ├── sunset_photography_0001.jpg
    ├── sunset_photography_0002.jpg
    └── ...
```

## 🔧 Configuration

### Chrome Headless Mode
- **Default**: `headless=True` (no browser window)
- **Show Browser**: Set to `False` for debugging

```python
scraper = ImageScraper(headless=False)
```

### Scroll Pagination
- **Default**: 10 scrolls to load images
- Modify in `scroll_to_load()` method

### Download Timeout
- **Default**: 10 seconds per image
- Adjust in `RequestsSession.create_session()`

### Maximum Retry Attempts
- **Default**: 3 retries per failed request
- Modify `Retry` configuration in `RequestsSession`

## 🛡️ Bot Detection Bypass Techniques

### Implemented Strategies:

1. **User-Agent Rotation**
   - 6 different modern browser User-Agents
   - Random selection on each request

2. **ChromeOptions Stealth**
   ```
   --headless=new (new headless mode)
   --disable-blink-features=AutomationControlled
   excludeSwitches: ["enable-automation"]
   useAutomationExtension: False
   ```

3. **Request Headers**
   - Realistic browser headers (Accept, DNT, Sec-Fetch-*)
   - Proper Accept-Language and encoding

4. **Random Delays**
   - 0.5-2 second delays between downloads
   - 1-4 second waits between page loads
   - Variable scroll pause times

5. **Connection Management**
   - Retry strategy for failed requests
   - Session reuse with connection pooling

## ⚠️ Error Handling

The scraper handles:
- ✓ Network timeouts
- ✓ Connection errors
- ✓ Missing/stale DOM elements
- ✓ Invalid image URLs
- ✓ Non-image content
- ✓ HTTP errors (429, 5xx, etc.)

**All errors are logged** to `scraper.log` and console.

## 📊 Logging

### Log File
- **Location**: `scraper.log`
- **Format**: Timestamp, Level, Message
- **Retention**: Appended on each run

### Log Levels
```
INFO    - General progress (scraping, downloading)
WARNING - Non-fatal issues (failed images, parsing errors)
ERROR   - Fatal issues (initialization failures)
```

## 🎯 Best Practices

### 1. Respect Websites
- Add delays between requests (already implemented)
- Don't scrape excessively from one site
- Check website Terms of Service
- Use images for educational/personal purposes only

### 2. Performance
- Use `headless=True` for faster execution
- Start with `target_count=20-30` to test
- Batch multiple queries to reuse driver

### 3. Reliability
- Always use try-finally for `scraper.cleanup()`
- Monitor `scraper.log` for issues
- Use Bing Images (more stable than Google)

### 4. Storage
- Images are named with query and index: `[query]_[0001].jpg`
- Each query gets its own folder
- Automatic folder creation

## 🐛 Troubleshooting

### Issue: "ChromeDriver not found"
**Solution**: webdriver-manager automatically downloads it on first run. Ensure internet connection.

### Issue: "Port 9222 already in use"
**Solution**: Close existing Chrome processes or restart system.

### Issue: No images downloaded
**Solution**:
1. Check `scraper.log` for errors
2. Try with `headless=False` to see what's happening
3. Verify internet connection
4. Try a different query

### Issue: Timeout errors
**Solution**: 
- Add more scroll time: `scroll_pause=3.0`
- Increase implicit wait: `ImageScraper(implicit_wait=15)`
- Use a faster internet connection

### Issue: Blocked/denied access
**Solution**:
- Try Bing Images instead of Google
- Increase delays: `time.sleep(random.uniform(2, 5))`
- Use a VPN (if allowed by terms of service)

## 📈 Performance Metrics

Typical performance on standard connection:

| Metric | Value |
|--------|-------|
| Scraping time (50 images) | 2-5 minutes |
| Download time (50 images) | 3-8 minutes |
| Memory usage | 150-300 MB |
| CPU usage | 30-60% |

## 🔐 Privacy & Security

- No data is stored except downloaded images
- All activity logged locally (scraper.log)
- Random delays prevent pattern detection
- Standard HTTPS for all requests

## 📚 API Reference

### ImageScraper Class

#### `__init__(headless=True, implicit_wait=10)`
Initialize scraper instance.

#### `initialize_driver()`
Set up Selenium WebDriver with Chrome options.

#### `scroll_to_load(max_scrolls=10, scroll_pause=2.0)`
Scroll page to trigger lazy-loading of images.

#### `scrape_google_images(query, target_count=50)`
Scrape images from Google Images.

#### `scrape_bing_images(query, target_count=50)`
Scrape images from Bing Images (recommended).

#### `download_images(image_urls, query, output_dir=None)`
Download images and save to disk.

#### `cleanup()`
Close driver and session properly.

### Helper Classes

#### `UserAgentRotator`
- `get_random_user_agent()` - Return random User-Agent

#### `RequestsSession`
- `create_session(user_agent=None)` - Create configured session

## 📜 License

This project is for educational purposes. Ensure compliance with website terms of service and copyright laws.

## 🤝 Contributing

Improvements welcome! Consider:
- Additional image sources (Unsplash, Pexels, Pinterest)
- Image processing pipeline
- Multiprocessing for faster downloads
- Database integration

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review `scraper.log` for detailed errors
3. Verify all prerequisites are installed

---

**Happy Scraping! 🚀**

*Last Updated: 2024*
