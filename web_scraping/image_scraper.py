"""
Robust Image Scraping System using Selenium and Requests
Supports Google Images, Bing Images, and Unsplash with automatic bot detection bypass
"""

import os
import sys
import time
import random
import logging
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlencode, quote
from datetime import datetime

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service


# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class UserAgentRotator:
    """Rotate User-Agents to bypass bot detection"""
    
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    ]
    
    @staticmethod
    def get_random_user_agent() -> str:
        """Return a random User-Agent string"""
        return random.choice(UserAgentRotator.USER_AGENTS)


class RequestsSession:
    """Create a robust requests session with retry logic"""
    
    @staticmethod
    def create_session(user_agent: Optional[str] = None) -> requests.Session:
        """Create a session with retry strategy and headers"""
        session = requests.Session()
        
        # Retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Headers to mimic real browser
        headers = {
            'User-Agent': user_agent or UserAgentRotator.get_random_user_agent(),
            'Accept': 'image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'image',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
        }
        session.headers.update(headers)
        session.timeout = 10
        
        return session


class ImageScraper:
    """Main image scraper class"""
    
    def __init__(self, headless: bool = True, implicit_wait: int = 10):
        """Initialize the scraper with Selenium WebDriver"""
        self.headless = headless
        self.implicit_wait = implicit_wait
        self.driver: Optional[webdriver.Chrome] = None
        self.session: Optional[requests.Session] = None
        
    def _setup_chrome_options(self) -> webdriver.ChromeOptions:
        """Configure Chrome options to bypass bot detection"""
        options = webdriver.ChromeOptions()
        
        # Headless mode
        if self.headless:
            options.add_argument('--headless=new')
        
        # Bot detection bypass
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument(f'--user-agent={UserAgentRotator.get_random_user_agent()}')
        
        # Additional stealth options
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Performance options
        prefs = {
            'profile.managed_default_content_settings.images': 2,  # Don't load images for speed
            'profile.default_content_setting_values.notifications': 2,
        }
        options.add_experimental_option('prefs', prefs)
        
        return options
    
    def initialize_driver(self) -> webdriver.Chrome:
        """Initialize Selenium WebDriver with webdriver-manager"""
        try:
            logger.info("Initializing Chrome WebDriver...")
            options = self._setup_chrome_options()
            
            # Get ChromeDriver path and fix the path if needed
            driver_path = ChromeDriverManager().install()
            
            # Fix Windows path issue: extract the correct executable name
            if os.name == 'nt':  # Windows
                driver_dir = os.path.dirname(driver_path)
                # Find the actual chromedriver executable
                for file in os.listdir(driver_dir):
                    if file.startswith('chromedriver') and file.endswith('.exe'):
                        driver_path = os.path.join(driver_dir, file)
                        break
            
            logger.info(f"Using ChromeDriver: {driver_path}")
            service = Service(driver_path)
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.implicitly_wait(self.implicit_wait)
            logger.info("WebDriver initialized successfully")
            return self.driver
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise
    
    def cleanup(self) -> None:
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver closed successfully")
            except Exception as e:
                logger.warning(f"Error closing WebDriver: {e}")
        
        if self.session:
            try:
                self.session.close()
                logger.info("Session closed successfully")
            except Exception as e:
                logger.warning(f"Error closing session: {e}")
    
    def scroll_to_load(self, max_scrolls: int = 10, scroll_pause: float = 2.0) -> None:
        """Scroll page to load lazy-loaded images"""
        logger.info(f"Starting scroll-to-load (max scrolls: {max_scrolls})...")
        
        for i in range(max_scrolls):
            try:
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(scroll_pause)
                
                # Random delay to avoid detection
                time.sleep(random.uniform(0.5, 1.5))
                
                logger.info(f"Scroll {i+1}/{max_scrolls} completed")
                
            except Exception as e:
                logger.warning(f"Error during scroll iteration {i+1}: {e}")
                continue
    
    def scrape_google_images(self, query: str, target_count: int = 50) -> List[str]:
        """Scrape images from Google Images"""
        image_urls = []
        
        try:
            logger.info(f"Scraping Google Images for: {query}")
            
            # Initialize driver
            if not self.driver:
                self.initialize_driver()
            
            if not self.session:
                self.session = RequestsSession.create_session()
            
            # Navigate to Google Images
            search_url = f"https://www.google.com/search?q={quote(query)}&tbm=isch"
            logger.info(f"Navigating to: {search_url}")
            self.driver.get(search_url)
            
            time.sleep(random.uniform(2, 4))
            
            # Scroll to load images
            self.scroll_to_load(max_scrolls=10)
            
            # Extract image elements
            logger.info("Extracting image URLs...")
            thumbnails = self.driver.find_elements(By.CSS_SELECTOR, "img.rg_i")
            logger.info(f"Found {len(thumbnails)} thumbnails")
            
            for idx, thumbnail in enumerate(thumbnails[:target_count * 2]):  # Get more to account for failures
                if len(image_urls) >= target_count:
                    break
                
                try:
                    # Click thumbnail to load full image
                    thumbnail.click()
                    time.sleep(random.uniform(1, 2))
                    
                    # Wait for actual image to load
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "img.n3VNCb"))
                    )
                    
                    # Extract actual image URLs
                    images = self.driver.find_elements(By.CSS_SELECTOR, "img.n3VNCb")
                    for image in images:
                        src = image.get_attribute('src')
                        
                        # Filter valid URLs
                        if src and 'http' in src and 'base64' not in src:
                            if src not in image_urls:
                                image_urls.append(src)
                                logger.info(f"[{len(image_urls)}/{target_count}] URL extracted: {src[:80]}...")
                                
                                if len(image_urls) >= target_count:
                                    break
                    
                except StaleElementReferenceException:
                    logger.warning(f"Stale element reference at index {idx}")
                    continue
                except TimeoutException:
                    logger.warning(f"Timeout loading image at index {idx}")
                    continue
                except Exception as e:
                    logger.warning(f"Error processing thumbnail {idx}: {e}")
                    continue
            
            logger.info(f"Extracted {len(image_urls)} valid image URLs")
            return image_urls[:target_count]
            
        except Exception as e:
            logger.error(f"Error scraping Google Images: {e}")
            return image_urls
    
    def scrape_bing_images(self, query: str, target_count: int = 50) -> List[str]:
        """Scrape images from Bing Images (more reliable than Google)"""
        image_urls = []
        
        try:
            logger.info(f"Scraping Bing Images for: {query}")
            
            if not self.driver:
                self.initialize_driver()
            
            if not self.session:
                self.session = RequestsSession.create_session()
            
            # Navigate to Bing Images
            search_url = f"https://www.bing.com/images/search?q={quote(query)}"
            logger.info(f"Navigating to: {search_url}")
            self.driver.get(search_url)
            
            time.sleep(random.uniform(2, 4))
            
            # Scroll to load images
            self.scroll_to_load(max_scrolls=8)
            
            # Extract image links
            logger.info("Extracting image URLs from Bing...")
            image_elements = self.driver.find_elements(By.CSS_SELECTOR, "a.iusc")
            logger.info(f"Found {len(image_elements)} image elements")
            
            for idx, element in enumerate(image_elements[:target_count * 2]):
                if len(image_urls) >= target_count:
                    break
                
                try:
                    # Get image metadata
                    m_attr = element.get_attribute('m')
                    if m_attr:
                        import json
                        metadata = json.loads(m_attr)
                        image_url = metadata.get('murl') or metadata.get('turl')
                        
                        if image_url and image_url not in image_urls:
                            image_urls.append(image_url)
                            logger.info(f"[{len(image_urls)}/{target_count}] URL extracted: {image_url[:80]}...")
                    
                except json.JSONDecodeError:
                    logger.warning(f"Error parsing JSON metadata at index {idx}")
                    continue
                except Exception as e:
                    logger.warning(f"Error processing image element {idx}: {e}")
                    continue
            
            logger.info(f"Extracted {len(image_urls)} valid image URLs from Bing")
            return image_urls[:target_count]
            
        except Exception as e:
            logger.error(f"Error scraping Bing Images: {e}")
            return image_urls
    
    def download_images(self, image_urls: List[str], query: str, output_dir: Optional[str] = None) -> int:
        """Download images using requests"""
        if output_dir is None:
            output_dir = query.replace(' ', '_')
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory: {output_path.absolute()}")
        
        if not self.session:
            self.session = RequestsSession.create_session()
        
        successful_downloads = 0
        
        for idx, url in enumerate(image_urls, 1):
            try:
                logger.info(f"[{idx}/{len(image_urls)}] Downloading: {url[:80]}...")
                
                # Random delay between downloads
                time.sleep(random.uniform(0.5, 2))
                
                # Download image
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                
                # Validate content type
                content_type = response.headers.get('content-type', '')
                if 'image' not in content_type.lower():
                    logger.warning(f"Skipping non-image content: {content_type}")
                    continue
                
                # Save image
                filename = output_path / f"{query}_{idx:04d}.jpg"
                with open(filename, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"✓ Saved: {filename.name}")
                successful_downloads += 1
                
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout downloading image {idx}")
                continue
            except requests.exceptions.ConnectionError:
                logger.warning(f"Connection error downloading image {idx}")
                continue
            except requests.exceptions.HTTPError as e:
                logger.warning(f"HTTP error for image {idx}: {e}")
                continue
            except Exception as e:
                logger.warning(f"Error downloading image {idx}: {e}")
                continue
        
        logger.info(f"Successfully downloaded {successful_downloads}/{len(image_urls)} images")
        return successful_downloads


def main(query: str, target_count: int = 50, source: str = 'bing', headless: bool = True):
    """Main function to orchestrate image scraping"""
    logger.info("=" * 80)
    logger.info(f"Starting Image Scraper - Query: '{query}', Target: {target_count}, Source: {source}")
    logger.info("=" * 80)
    
    scraper = ImageScraper(headless=headless)
    
    try:
        # Initialize driver
        scraper.initialize_driver()
        
        # Scrape images based on source
        if source.lower() == 'google':
            image_urls = scraper.scrape_google_images(query, target_count)
        elif source.lower() == 'bing':
            image_urls = scraper.scrape_bing_images(query, target_count)
        else:
            logger.error(f"Unknown source: {source}")
            return
        
        if not image_urls:
            logger.warning("No images found!")
            return
        
        # Download images
        output_dir = query.replace(' ', '_')
        successful = scraper.download_images(image_urls, query, output_dir)
        
        logger.info("=" * 80)
        logger.info(f"Scraping complete! Downloaded {successful} images to '{output_dir}'")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    
    finally:
        scraper.cleanup()


if __name__ == "__main__":
    # Example usage
    if len(sys.argv) > 1:
        query = ' '.join(sys.argv[1:])
        main(query, target_count=50, source='bing', headless=True)
    else:
        # Default example
        main("Python programming", target_count=30, source='bing', headless=True)
