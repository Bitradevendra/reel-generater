"""
Advanced Usage Examples
Demonstrates various scraping scenarios and configurations
"""

from image_scraper import ImageScraper, main
import json
from pathlib import Path


def example_1_simple_scrape():
    """Example 1: Simple single query scrape"""
    print("\n" + "="*80)
    print("EXAMPLE 1: Simple Single Query Scrape")
    print("="*80)
    
    main(
        query="beautiful landscapes",
        target_count=20,
        source='bing',
        headless=True
    )


def example_2_batch_processing():
    """Example 2: Batch process multiple queries"""
    print("\n" + "="*80)
    print("EXAMPLE 2: Batch Processing Multiple Queries")
    print("="*80)
    
    queries = [
        "sunset",
        "ocean waves",
        "mountain peaks",
        "forest trees"
    ]
    
    scraper = ImageScraper(headless=True)
    
    try:
        scraper.initialize_driver()
        
        for query in queries:
            print(f"\n▶ Processing: {query}")
            urls = scraper.scrape_bing_images(query, target_count=15)
            scraper.download_images(urls, query)
            print(f"✓ Completed: {query}\n")
    
    except Exception as e:
        print(f"✗ Error in batch processing: {e}")
    
    finally:
        scraper.cleanup()


def example_3_google_images():
    """Example 3: Scrape from Google Images with monitoring"""
    print("\n" + "="*80)
    print("EXAMPLE 3: Google Images Scraping")
    print("="*80)
    
    scraper = ImageScraper(headless=False)  # Show browser for monitoring
    
    try:
        scraper.initialize_driver()
        
        query = "artificial intelligence"
        print(f"\nScraping Google Images for: {query}")
        
        urls = scraper.scrape_google_images(query, target_count=25)
        
        print(f"\nFound {len(urls)} URLs. Downloading...")
        successful = scraper.download_images(urls, query)
        
        print(f"\n✓ Downloaded {successful} images successfully")
    
    except Exception as e:
        print(f"✗ Error: {e}")
    
    finally:
        scraper.cleanup()


def example_4_custom_output_directory():
    """Example 4: Custom output directory structure"""
    print("\n" + "="*80)
    print("EXAMPLE 4: Custom Output Directory")
    print("="*80)
    
    scraper = ImageScraper(headless=True)
    
    try:
        scraper.initialize_driver()
        
        query = "space exploration"
        custom_dir = "Downloads/space_collection"
        
        print(f"\nCustom output directory: {custom_dir}")
        
        urls = scraper.scrape_bing_images(query, target_count=20)
        scraper.download_images(urls, query, output_dir=custom_dir)
        
        print(f"\n✓ Images saved to: {custom_dir}")
    
    except Exception as e:
        print(f"✗ Error: {e}")
    
    finally:
        scraper.cleanup()


def example_5_with_statistics():
    """Example 5: Scraping with statistics collection"""
    print("\n" + "="*80)
    print("EXAMPLE 5: Scraping with Statistics")
    print("="*80)
    
    queries = ["robots", "drones", "autonomous vehicles"]
    stats = {}
    
    scraper = ImageScraper(headless=True)
    
    try:
        scraper.initialize_driver()
        
        for query in queries:
            print(f"\n▶ Processing: {query}")
            
            urls = scraper.scrape_bing_images(query, target_count=15)
            downloaded = scraper.download_images(urls, query)
            
            stats[query] = {
                "target": 15,
                "urls_found": len(urls),
                "successfully_downloaded": downloaded,
                "success_rate": f"{(downloaded/len(urls)*100):.1f}%" if urls else "0%"
            }
            
            print(f"  URLs Found: {len(urls)}")
            print(f"  Downloaded: {downloaded}")
            print(f"  Success Rate: {stats[query]['success_rate']}")
        
        # Print summary
        print("\n" + "="*80)
        print("SUMMARY STATISTICS")
        print("="*80)
        print(json.dumps(stats, indent=2))
        
        # Save statistics
        with open("scraping_stats.json", "w") as f:
            json.dump(stats, f, indent=2)
        print("\n✓ Statistics saved to: scraping_stats.json")
    
    except Exception as e:
        print(f"✗ Error: {e}")
    
    finally:
        scraper.cleanup()


def example_6_error_recovery():
    """Example 6: Demonstrate error handling and recovery"""
    print("\n" + "="*80)
    print("EXAMPLE 6: Error Handling & Recovery")
    print("="*80)
    
    problematic_queries = [
        "",  # Empty query
        "   ",  # Whitespace
        "very long query" * 20,  # Very long query
        "😀 emoji query 🎨",  # Special characters
        "normal query"  # Normal query (should work)
    ]
    
    scraper = ImageScraper(headless=True)
    
    try:
        scraper.initialize_driver()
        
        for query in problematic_queries:
            try:
                print(f"\n▶ Attempting: '{query[:50]}...'")
                
                if not query or not query.strip():
                    print("  ✗ Skipped: Empty query")
                    continue
                
                urls = scraper.scrape_bing_images(query.strip(), target_count=5)
                
                if urls:
                    scraper.download_images(urls, query[:30], output_dir=f"results/{query[:20]}")
                    print(f"  ✓ Success: {len(urls)} images found")
                else:
                    print(f"  ⚠ No images found for this query")
            
            except Exception as e:
                print(f"  ✗ Error: {str(e)[:100]}")
                continue
    
    finally:
        scraper.cleanup()


def example_7_performance_comparison():
    """Example 7: Compare different scraping strategies"""
    print("\n" + "="*80)
    print("EXAMPLE 7: Performance Comparison")
    print("="*80)
    
    import time
    
    query = "technology"
    target_count = 10
    
    # Strategy 1: With scrolling
    print("\n▶ Strategy 1: With Scroll-to-Load")
    scraper1 = ImageScraper(headless=True)
    start = time.time()
    try:
        scraper1.initialize_driver()
        urls = scraper1.scrape_bing_images(query, target_count)
        duration1 = time.time() - start
        print(f"  ✓ Found {len(urls)} images in {duration1:.2f} seconds")
    finally:
        scraper1.cleanup()
    
    # Strategy 2: Different scroll settings
    print("\n▶ Strategy 2: With Reduced Scrolling")
    scraper2 = ImageScraper(headless=True)
    # Override scroll behavior by modifying the instance
    start = time.time()
    try:
        scraper2.initialize_driver()
        # This would use default scroll settings (10 scrolls)
        urls = scraper2.scrape_bing_images(query, target_count)
        duration2 = time.time() - start
        print(f"  ✓ Found {len(urls)} images in {duration2:.2f} seconds")
    finally:
        scraper2.cleanup()
    
    print(f"\nNote: Actual performance varies based on internet speed and website load")


def main_menu():
    """Interactive menu for running examples"""
    print("\n" + "="*80)
    print("IMAGE SCRAPER - ADVANCED EXAMPLES")
    print("="*80)
    print("\nSelect an example to run:")
    print("1. Simple Single Query Scrape")
    print("2. Batch Processing Multiple Queries")
    print("3. Google Images Scraping")
    print("4. Custom Output Directory")
    print("5. Scraping with Statistics")
    print("6. Error Handling & Recovery")
    print("7. Performance Comparison")
    print("8. Run All Examples")
    print("0. Exit")
    print("-" * 80)
    
    choice = input("\nEnter your choice (0-8): ").strip()
    
    examples = {
        '1': example_1_simple_scrape,
        '2': example_2_batch_processing,
        '3': example_3_google_images,
        '4': example_4_custom_output_directory,
        '5': example_5_with_statistics,
        '6': example_6_error_recovery,
        '7': example_7_performance_comparison,
    }
    
    if choice == '8':
        for func in examples.values():
            try:
                func()
            except KeyboardInterrupt:
                print("\n\n⚠ Interrupted by user")
                break
    elif choice in examples:
        try:
            examples[choice]()
        except KeyboardInterrupt:
            print("\n\n⚠ Script interrupted by user")
    elif choice == '0':
        print("\nGoodbye! 👋")
    else:
        print("\n✗ Invalid choice. Please try again.")


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\n⚠ Application terminated by user")
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
