"""
Image Engine - Wraps the web_scraping/ module with NLP keyword extraction.
Scrapes images per sentence/keyword with aggressive retry logic.
"""

import os
import sys
import re
import time
import json
import random
import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.resolve()


# ============================================================================
# KEYWORD EXTRACTION — Script-Aware, Topic-Contextualized
# ============================================================================

# Comprehensive stop words — common verbs, pronouns, prepositions, etc.
# These NEVER carry visual meaning for image searches.
_STOP_WORDS = {
    # articles / determiners
    'the', 'a', 'an', 'this', 'that', 'these', 'those',
    # pronouns
    'i', 'me', 'my', 'we', 'our', 'you', 'your', 'he', 'him', 'his',
    'she', 'her', 'it', 'its', 'they', 'them', 'their', 'who', 'whom',
    # be / have / do / modal
    'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did',
    'will', 'would', 'could', 'should', 'may', 'might', 'must',
    'shall', 'can', 'need', 'dare',
    # prepositions / conjunctions
    'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as',
    'into', 'through', 'during', 'before', 'after', 'above', 'below',
    'between', 'out', 'off', 'over', 'under', 'up', 'down',
    'and', 'but', 'or', 'nor', 'not', 'so', 'yet', 'if', 'than',
    # adverbs / fillers
    'again', 'further', 'then', 'once', 'also', 'just', 'very',
    'too', 'only', 'even', 'really', 'actually', 'ever', 'well',
    'here', 'there', 'where', 'when', 'how', 'what', 'which', 'why',
    'about', 'because', 'both', 'each', 'few', 'more', 'most',
    'other', 'some', 'such', 'no', 'own', 'same', 'every', 'all',
    # generic verbs (too vague to search images)
    'let', 'like', 'think', 'know', 'make', 'get', 'say', 'tell',
    'give', 'take', 'come', 'go', 'see', 'look', 'want', 'use',
    'find', 'put', 'try', 'ask', 'work', 'seem', 'feel', 'leave',
    'call', 'keep', 'start', 'show', 'hear', 'play', 'run', 'move',
    'live', 'believe', 'hold', 'bring', 'happen', 'write', 'provide',
    'sit', 'stand', 'lose', 'pay', 'meet', 'include', 'continue',
    'set', 'learn', 'change', 'lead', 'understand', 'watch', 'follow',
    'stop', 'create', 'speak', 'read', 'allow', 'add', 'spend',
    'grow', 'open', 'walk', 'win', 'offer', 'remember', 'love',
    'consider', 'appear', 'buy', 'wait', 'serve', 'die', 'send',
    'expect', 'build', 'stay', 'fall', 'cut', 'reach', 'kill',
    'remain', 'suggest', 'raise', 'pass', 'sell', 'require', 'report',
    # generic adjectives/adverbs (too vague for visual searches)
    'good', 'great', 'best', 'better', 'bad', 'worse', 'worst',
    'big', 'small', 'large', 'long', 'short', 'high', 'low',
    'old', 'new', 'young', 'first', 'last', 'next', 'different',
    'important', 'real', 'true', 'full', 'whole', 'little',
    'rich', 'helps', 'help', 'helped', 'helping', 'makes',
    'made', 'making', 'used', 'using', 'uses', 'called',
    'become', 'became', 'becoming', 'turn', 'turned', 'known',
    # number words
    'one', 'two', 'three', 'four', 'five', 'six', 'seven',
    'eight', 'nine', 'ten', 'hundred', 'thousand', 'million',
    # reel-script filler
    'right', 'now', 'today', 'thing', 'things', 'way', 'ways',
    'time', 'times', 'fact', 'much', 'many', 'people', 'something',
    'everything', 'nothing', 'anything', 'someone', 'everyone',
    'lot', 'lots', 'part', 'parts', 'kind', 'bit', 'stuff',
    'gonna', 'gotta', 'wanna', 'yeah', 'okay',
}


def _naive_singular(word: str) -> str:
    """Cheap singular form for dedup only.
    Only strips the most obvious English plural endings.
    Intentionally conservative to avoid mangling words like 'nutritious'."""
    w = word.lower()
    # Never touch words ending in -ss, -us, -ous, -is, -ies (5+ chars only)
    if w.endswith(('ss', 'us', 'ous', 'is', 'ness')):
        return w
    # berries -> berry, studies -> study
    if w.endswith('ies') and len(w) > 5:
        return w[:-3] + 'y'
    # boxes -> box, watches -> watch (but NOT 'es' at len <= 4 or if stem < 3)
    if w.endswith('es') and len(w) > 5 and w[-3] in 'shxz':
        return w[:-2]
    # bananas -> banana, cats -> cat (simple -s only)
    if w.endswith('s') and not w.endswith('ss') and len(w) > 4:
        return w[:-1]
    return w


def _extract_main_words(text: str, max_words: int = 3) -> List[str]:
    """
    Extract the 2-3 most meaningful *content* words from a sentence.

    Strategy:
        1. Tokenize into words (3+ chars, alpha only).
        2. Strip every stop-word / filler.
        3. Collapse plural/singular duplicates (banana + bananas = banana).
        4. Return the remaining words in their original order (max 3).

    Example:
        "Banana is one of the most nutritious fruits on Earth"
        -> ['banana', 'nutritious', 'fruit']
    """
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    content = [w for w in words if w not in _STOP_WORDS]

    # Deduplicate while collapsing plurals
    seen_stems = set()
    unique = []
    for w in content:
        stem = _naive_singular(w)
        if stem not in seen_stems:
            seen_stems.add(stem)
            # Prefer the singular form for cleaner search queries
            unique.append(stem)

    return unique[:max_words]


def _extract_main_words_rake(text: str, max_words: int = 3) -> List[str]:
    """
    Extract main words using RAKE, falling back to the simple extractor.
    RAKE can find multi-word phrases like "neural network" or "blood pressure".
    """
    try:
        from rake_nltk import Rake
        r = Rake(min_length=1, max_length=3)
        r.extract_keywords_from_text(text)
        phrases = r.get_ranked_phrases()

        # Flatten RAKE phrases into individual meaningful words + keep
        # the best multi-word phrase if RAKE found one.
        result = []
        for phrase in phrases:
            if len(phrase) > 2:
                result.append(phrase)
            if len(result) >= max_words:
                break

        if result:
            return result[:max_words]

        # RAKE returned nothing useful → fall back
        return _extract_main_words(text, max_words)

    except ImportError:
        logger.debug("[Image] rake-nltk not installed, using simple extractor")
        return _extract_main_words(text, max_words)
    except Exception as e:
        logger.debug(f"[Image] RAKE error: {e}")
        return _extract_main_words(text, max_words)


def _build_search_query(topic: str, main_words: List[str], add_context: bool) -> str:
    """
    Combine topic + main words into ONE search query string.

    Examples (topic = "uses of banana"):
        main_words = ['potassium', 'heart', 'health']
        → "banana potassium heart health"

        main_words = ['smoothie', 'recipe']
        → "banana smoothie recipe"

    If the topic itself already contains one of the words, we avoid duplication.
    """
    # Extract topic's own content words so we can prepend the most meaningful part
    topic_words = _extract_main_words(topic, max_words=2) if topic else []

    if not add_context or not topic_words:
        # No context requested or no topic — just join the sentence words
        return ' '.join(main_words) if main_words else topic

    # Merge topic words + sentence words, avoiding duplication
    merged = list(topic_words)  # start with topic context
    for w in main_words:
        if w.lower() not in {tw.lower() for tw in merged}:
            merged.append(w)

    return ' '.join(merged)


def extract_search_queries(
    sentences: List[Dict],
    topic: str = "",
    config: Optional[Dict] = None,
) -> List[Dict]:
    """
    Extract image search queries for each sentence in the script.

    For each sentence we:
      1. Pull out 2-3 *main content words* (nouns/adjectives that carry visual meaning).
      2. Combine them with the overall topic to form ONE contextual search query.
      3. Optionally add a second, topic-only fallback query.

    Args:
        sentences: List of sentence timing dicts with 'text' key
        topic: Overall topic for context (e.g. "uses of banana")
        config: Optional config

    Returns:
        List of dicts with 'sentence', 'queries', 'start', 'end' keys
    """
    cfg = (config or {}).get("scraping", {}).get("keyword_extraction", {})
    max_kw = cfg.get("max_keywords_per_sentence", 3)
    add_context = cfg.get("add_topic_context", True)

    results = []
    for sent_data in sentences:
        text = sent_data.get("text", "")

        # 1. Extract the 2-3 most important words from this sentence
        main_words = _extract_main_words_rake(text, max_kw)

        # 2. Build ONE combined search query: topic + main words
        queries = []
        if main_words:
            combined_query = _build_search_query(topic, main_words, add_context)
            queries.append(combined_query)

            # Also add a shorter variant (just the sentence's own words) as fallback
            sentence_only_query = ' '.join(main_words)
            if sentence_only_query != combined_query:
                queries.append(sentence_only_query)
        else:
            # Nothing extracted → use topic or first few words as last resort
            fallback_words = text.split()[:5]
            if fallback_words:
                queries.append(' '.join(fallback_words))
            if topic:
                queries.append(topic)

        logger.info(f"[Image] Sentence: \"{text[:60]}...\" → queries: {queries}")

        results.append({
            "sentence": text,
            "queries": queries,
            "start": sent_data.get("start", 0),
            "end": sent_data.get("end", 0),
        })

    return results


# ============================================================================
# IMAGE SCRAPING
# ============================================================================

def _create_session() -> requests.Session:
    """Create a robust requests session with retry logic."""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    ]
    
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    session.headers.update({
        'User-Agent': random.choice(user_agents),
        'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'DNT': '1',
    })
    
    return session


def _scrape_bing_api(query: str, count: int = 5, session: requests.Session = None) -> List[str]:
    """Scrape image URLs from Bing using Selenium."""
    urls = []
    
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        driver_path = ChromeDriverManager().install()
        if os.name == 'nt':
            driver_dir = os.path.dirname(driver_path)
            for file in os.listdir(driver_dir):
                if file.startswith('chromedriver') and file.endswith('.exe'):
                    driver_path = os.path.join(driver_dir, file)
                    break
        
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(10)
        
        try:
            # Append &qft=+filterui:aspect-wide to rigidly ask Bing for landscape images
            search_url = f"https://www.bing.com/images/search?q={quote(query)}&qft=+filterui:aspect-wide"
            driver.get(search_url)
            time.sleep(random.uniform(2, 3))
            
            # Scroll to load images
            for _ in range(3):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
            
            # Extract image URLs
            elements = driver.find_elements(By.CSS_SELECTOR, "a.iusc")
            
            for elem in elements[:count * 2]:
                if len(urls) >= count:
                    break
                try:
                    m_attr = elem.get_attribute('m')
                    if m_attr:
                        metadata = json.loads(m_attr)
                        url = metadata.get('murl') or metadata.get('turl')
                        if url and url not in urls:
                            urls.append(url)
                except Exception:
                    continue
                    
        finally:
            driver.quit()
            
    except Exception as e:
        logger.warning(f"[Image] Bing scrape failed for '{query}': {e}")
    
    return urls


def _download_single_image(
    url: str,
    save_path: str,
    session: requests.Session,
    max_retries: int = 5,
    retry_delay: float = 2.0,
    retry_backoff: float = 1.5,
    min_width: int = 400,
    min_height: int = 300,
) -> Optional[str]:
    """Download a single image with retry logic and validation."""
    from PIL import Image
    from io import BytesIO
    
    for attempt in range(1, max_retries + 1):
        try:
            response = session.get(url, timeout=15)
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '')
            if 'image' not in content_type.lower() and 'octet-stream' not in content_type.lower():
                logger.debug(f"[Image] Not an image: {content_type}")
                return None
            
            # Validate image size
            img = Image.open(BytesIO(response.content))
            
            if img.width < min_width or img.height < min_height:
                logger.debug(f"[Image] Too small: {img.width}x{img.height}")
                return None
                
            # Reject tall/portrait images since they won't fit well in a landscape box
            if img.height > img.width:
                logger.debug(f"[Image] Rejected tall image: {img.width}x{img.height}")
                return None
            
            # Convert to RGB if needed
            if img.mode in ('RGBA', 'P', 'LA'):
                img = img.convert('RGB')
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Save
            img.save(save_path, 'JPEG', quality=90)
            logger.debug(f"[Image] Downloaded: {Path(save_path).name}")
            return save_path
            
        except requests.exceptions.Timeout:
            logger.debug(f"[Image] Timeout (attempt {attempt})")
        except requests.exceptions.ConnectionError:
            logger.debug(f"[Image] Connection error (attempt {attempt})")
        except Exception as e:
            logger.debug(f"[Image] Download error (attempt {attempt}): {e}")
        
        if attempt < max_retries:
            delay = retry_delay * (retry_backoff ** (attempt - 1))
            time.sleep(delay)
    
    return None


def scrape_images_for_video(
    search_queries: List[Dict],
    output_dir: str,
    config: Optional[Dict] = None,
) -> Dict[int, List[str]]:
    """
    Scrape images for each sentence in the video.
    
    Args:
        search_queries: Output from extract_search_queries()
        output_dir: Directory to save downloaded images
        config: Optional config dict
        
    Returns:
        Dict mapping sentence index to list of downloaded image paths
    """
    cfg = (config or {}).get("scraping", {})
    images_per_kw = cfg.get("images_per_keyword", 5)
    max_total = cfg.get("max_total_images", 80)
    max_retries = cfg.get("max_retries", 5)
    retry_delay = cfg.get("retry_delay", 2.0)
    retry_backoff = cfg.get("retry_backoff", 1.5)
    min_width = cfg.get("min_image_width", 400)
    min_height = cfg.get("min_image_height", 300)
    parallel = (config or {}).get("performance", {}).get("parallel_image_downloads", 4)
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    session = _create_session()
    result = {}
    total_downloaded = 0
    all_downloaded_hashes = set()  # Avoid duplicate images
    
    for sent_idx, sent_data in enumerate(search_queries):
        if total_downloaded >= max_total:
            logger.warning(f"[Image] Reached max total images ({max_total})")
            break
        
        queries = sent_data.get("queries", [])
        sentence_images = []
        
        logger.info(f"[Image] Sentence {sent_idx + 1}/{len(search_queries)}: {queries}")
        
        for query in queries:
            if len(sentence_images) >= images_per_kw:
                break
            
            # Scrape URLs with retry on the scraping itself
            urls = []
            for scrape_attempt in range(3):
                urls = _scrape_bing_api(query, count=images_per_kw * 2, session=session)
                if urls:
                    break
                logger.info(f"[Image] Scrape retry {scrape_attempt + 1} for: {query}")
                time.sleep(2)
            
            if not urls:
                logger.warning(f"[Image] No URLs found for: {query}")
                continue
            
            # Download images
            for url_idx, url in enumerate(urls):
                if len(sentence_images) >= images_per_kw:
                    break
                if total_downloaded >= max_total:
                    break
                
                filename = f"sent{sent_idx:03d}_img{len(sentence_images):03d}.jpg"
                save_path = str(output_path / filename)
                
                downloaded = _download_single_image(
                    url, save_path, session,
                    max_retries=max_retries,
                    retry_delay=retry_delay,
                    retry_backoff=retry_backoff,
                    min_width=min_width,
                    min_height=min_height,
                )
                
                if downloaded:
                    # Check for duplicate images via hash
                    try:
                        with open(downloaded, 'rb') as f:
                            img_hash = hashlib.md5(f.read()).hexdigest()
                        if img_hash in all_downloaded_hashes:
                            os.remove(downloaded)
                            continue
                        all_downloaded_hashes.add(img_hash)
                    except Exception:
                        pass
                    
                    sentence_images.append(downloaded)
                    total_downloaded += 1
        
        # CRITICAL: If no images for this sentence, use images from adjacent sentences
        if not sentence_images:
            logger.warning(f"[Image] No images for sentence {sent_idx} - will use fallback")
        
        result[sent_idx] = sentence_images
    
    # Fill in gaps: sentences with no images get images from neighbors
    for sent_idx in range(len(search_queries)):
        if sent_idx not in result or not result[sent_idx]:
            # Look for nearest sentence with images
            for offset in range(1, len(search_queries)):
                for neighbor in [sent_idx - offset, sent_idx + offset]:
                    if 0 <= neighbor < len(search_queries) and neighbor in result and result[neighbor]:
                        result[sent_idx] = result[neighbor][:1]  # Use first image
                        logger.info(f"[Image] Filled sentence {sent_idx} with image from sentence {neighbor}")
                        break
                if result.get(sent_idx):
                    break
    
    session.close()
    logger.info(f"[Image] Total downloaded: {total_downloaded} images for {len(search_queries)} sentences")
    return result
