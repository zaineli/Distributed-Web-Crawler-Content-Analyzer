from web_crawler import WebCrawler
import logging

logging.basicConfig(level=logging.INFO)


def crawl_single_site(site, prefix='output'):
    """Crawl a single website and save the output"""
    # site = "https://example.com"
    
    # Create a base configuration for the crawler
    base_config = {
        "max_depth": 1,
        "max_pages": 10,
        "timeout": 10,
        "delay": 1.0,
        "respect_robots": False,
        "threads": 5
    }
    
    # Create a domain-specific output folder
    from urllib.parse import urlparse
    domain = urlparse(site).netloc
    output_dir = f"{prefix}/{domain}"
    
    # Create and configure the crawler
    crawler = WebCrawler(**base_config)
    
    # Start crawling
    crawler.crawl(site, output_dir)
    
    print(f"Crawled {len(crawler.crawled_urls)} pages from {site}.")


def batch_crawl_multiple_sites(sites):
    """Crawl multiple websites in sequence"""
    # sites = [
    #     "https://example.com",
    #     "https://wikipedia.org",
    #     "https://python.org"
    # ]

    # Process each site
    for site in sites:
        print(f"\nStarting crawl of {site}")
        crawl_single_site(site, 'batch_output')
    print("\nBatch crawling complete!")


if __name__ == "__main__":
    batch_crawl_multiple_sites()
   
