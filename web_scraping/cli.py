#!/usr/bin/env python3
"""
Simple CLI wrapper for image scraper
Usage:
    python cli.py "search query"
    python cli.py "search query" --count 50 --source bing --show
"""

import argparse
import sys
from pathlib import Path
from image_scraper import ImageScraper, logger


def create_parser():
    """Create command-line argument parser"""
    parser = argparse.ArgumentParser(
        description='🖼️  Robust Image Scraping System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  %(prog)s "python programming"
  
  # With custom count
  %(prog)s "sunset photography" --count 100
  
  # Show browser during scraping
  %(prog)s "nature" --show
  
  # Use Google Images instead of Bing
  %(prog)s "mountains" --source google
  
  # Custom output directory
  %(prog)s "cats" --output my_images/
        """
    )
    
    parser.add_argument(
        'query',
        help='Search query for images'



    )
    
    parser.add_argument(
        '-c', '--count',
        type=int,
        default=50,
        help='Target number of images to download (default: 50)'
    )
    
    parser.add_argument(
        '-s', '--source',
        choices=['google', 'bing'],
        default='bing',
        help='Image source to scrape from (default: bing)'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        default=None,
        help='Custom output directory (default: query name)'
    )
    
    parser.add_argument(
        '--show',
        action='store_true',
        help='Show browser window during scraping (default: headless)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='Image Scraper v1.0.0'
    )
    
    return parser


def main():
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Validate query
    query = args.query.strip()
    if not query:
        parser.error("Search query cannot be empty")
    
    # Validate count
    if args.count <= 0:
        parser.error("Count must be greater than 0")
    
    if args.count > 500:
        print("⚠️  Warning: Requesting 500+ images may take a long time")
        response = input("Continue? (y/n): ").lower()
        if response != 'y':
            print("Cancelled.")
            return
    
    # Set default output to 'scraped' folder if not specified
    output_dir = args.output or Path("scraped") / query.replace(' ', '_')
    
    print("\n" + "="*80)
    print("🖼️  IMAGE SCRAPER STARTED")
    print("="*80)
    print(f"Query:        {query}")
    print(f"Count:        {args.count}")
    print(f"Source:       {args.source.upper()}")
    print(f"Headless:     {not args.show}")
    print(f"Output:       {output_dir}")
    print("="*80 + "\n")
    
    scraper = ImageScraper(headless=not args.show)
    
    try:
        # Initialize driver
        logger.info("Initializing browser...")
        scraper.initialize_driver()
        
        # Scrape images
        logger.info(f"Starting scrape from {args.source.upper()} Images...")
        if args.source == 'google':
            image_urls = scraper.scrape_google_images(query, args.count)
        else:
            image_urls = scraper.scrape_bing_images(query, args.count)
        
        if not image_urls:
            logger.error("No images found!")
            return 1
        
        logger.info(f"Found {len(image_urls)} image URLs")
        
        # Download images
        logger.info("Downloading images...")
        successful = scraper.download_images(image_urls, query, str(output_dir))
        print("\n" + "="*80)
        print("✅ SCRAPING COMPLETE!")
        print("="*80)
        print(f"Downloaded:   {successful}/{len(image_urls)} images")
        print(f"Success Rate: {(successful/len(image_urls)*100):.1f}%")
        print(f"Output Dir:   {Path(output_dir).absolute()}")
        print("="*80 + "\n")
        
        return 0 if successful > 0 else 1
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Scraping interrupted by user")
        return 130
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        return 1
    
    finally:
        scraper.cleanup()


if __name__ == '__main__':
    sys.exit(main())
