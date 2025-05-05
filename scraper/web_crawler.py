import os
import time
import argparse
import uuid
import logging
from urllib.parse import urlparse, urljoin
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import boto3
import requests
from bs4 import BeautifulSoup
import validators
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("crawler.log"),
        logging.StreamHandler()
    ]
)

load_dotenv()

class WebCrawler:
    """A web crawler that downloads content from websites and saves to files"""
    
    def __init__(self, max_depth=3, max_pages=100, timeout=10, delay=1, 
                 user_agent=None, respect_robots=False, threads=5):
        """Initialize the crawler with configuration parameters"""
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.timeout = timeout
        self.delay = delay
        self.crawled_urls = set()
        self.queued_urls = set()
        self.session = requests.Session()
        
        # Set user agent
        if user_agent is None:
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        
        self.session.headers.update({'User-Agent': user_agent})
        self.respect_robots = respect_robots
        self.threads = threads
        self.disallowed_paths = set()
    
    def _is_valid_url(self, url):
        """Check if URL is valid and within the same domain"""
        try:
            return validators.url(url)
        except:
            return False
    
    def _get_base_url(self, url):
        """Extract base URL (scheme + domain)"""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"
    
    def _get_domain(self, url):
        """Extract domain from URL"""
        return urlparse(url).netloc
    
    def _normalize_url(self, url, base_url):
        """Normalize URL to absolute path"""
        if not url:
            return None
            
        # Skip mailto, tel, javascript links
        if url.startswith(('mailto:', 'tel:', 'javascript:')):
            return None
            
        # Skip anchors
        if url.startswith('#'):
            return None
            
        # Convert relative URLs to absolute
        if not url.startswith(('http://', 'https://')):
            url = urljoin(base_url, url)
            
        # Remove fragments
        url = url.split('#')[0]
        
        # Remove trailing slash
        if url.endswith('/'):
            url = url[:-1]
            
        return url
    
    def _parse_robots_txt(self, base_url):
        """Parse robots.txt file to respect (or not) directives"""
        if not self.respect_robots:
            logging.info("Robots.txt directives will be ignored as requested")
            return
            
        robots_url = f"{base_url}/robots.txt"
        try:
            response = self.session.get(robots_url, timeout=self.timeout)
            if response.status_code == 200:
                lines = response.text.split('\n')
                user_agent_match = False
                
                for line in lines:
                    line = line.strip().lower()
                    
                    if line.startswith('user-agent:'):
                        agent = line.split(':', 1)[1].strip()
                        if agent == '*':
                            user_agent_match = True
                        else:
                            user_agent_match = False
                            
                    if user_agent_match and line.startswith('disallow:'):
                        path = line.split(':', 1)[1].strip()
                        if path:
                            self.disallowed_paths.add(path)
        except Exception as e:
            logging.warning(f"Error fetching robots.txt: {e}")
    
    def _is_allowed(self, url):
        """Check if URL is allowed by robots.txt"""
        if not self.respect_robots:
            return True
            
        parsed_url = urlparse(url)
        path = parsed_url.path
        
        for disallowed_path in self.disallowed_paths:
            if path.startswith(disallowed_path):
                return False
                
        return True
    
    def _extract_links(self, soup, base_url, current_url):
        """Extract all links from page"""
        links = []
        domain = self._get_domain(base_url)
        
        for anchor in soup.find_all('a', href=True):
            href = anchor['href']
            normalized_url = self._normalize_url(href, current_url)
            
            if normalized_url and self._get_domain(normalized_url) == domain:
                links.append(normalized_url)
                
        return links
    
    def _clean_text(self, soup):
        """Extract and clean text from page"""
        # Remove script and style elements
        for script_or_style in soup(['script', 'style', 'header', 'footer', 'nav']):
            script_or_style.decompose()
            
        # Get text
        text = soup.get_text()
        
        # Clean up text: break into lines and strip
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
    

    

    
    def _save_content(self, url, content, output_dir):
        """Save content to file"""
        # Create safe filename from URL
        parsed_url = urlparse(url)
        domain_dir = os.path.join(output_dir, parsed_url.netloc)
        
        if not os.path.exists(domain_dir):
            os.makedirs(domain_dir, exist_ok=True)
        
        # Create unique filename
        filename = f"{uuid.uuid4().hex}.txt"
        filepath = os.path.join(domain_dir, filename)
        
        # Save metadata and content
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"URL: {url}\n")
            f.write(f"Crawled at: {datetime.now().isoformat()}\n")
            f.write(f"{'-' * 80}\n\n")
            f.write(content)
        
        logging.info(f"Saved content from {url} to {filepath}")
        
        # Create an index file with URLs and filenames
        index_path = os.path.join(domain_dir, "index.txt")
        with open(index_path, 'a', encoding='utf-8') as f:
            f.write(f"{url} -> {filename}\n")
        
        def upload_to_s3(file_path, bucket_name, s3_key):
            s3 = boto3.client('s3')
            try:
                s3.upload_file(file_path, bucket_name, s3_key)
                print(f"[UPLOAD] Uploaded {file_path} to s3://{bucket_name}/{s3_key}")
            except Exception as e:
                print(f"[ERROR] S3 Upload failed: {e}")
            
        
        s3_key = f"{parsed_url.netloc}/{filename}"
        bucket_name = "zainxdev"
        
        upload_to_s3(filepath, bucket_name, s3_key)
        logging.info(f"Uploaded {filename} to S3 bucket {bucket_name} with key {s3_key}")
        
        
        return filepath
    
    def _crawl_page(self, url, depth, output_dir):
        """Crawl a single page and extract links"""
        if depth > self.max_depth or url in self.crawled_urls or len(self.crawled_urls) >= self.max_pages:
            return []
        
        if not self._is_allowed(url):
            logging.info(f"Skipping {url} (disallowed by robots.txt)")
            return []
        
        try:
            logging.info(f"Crawling {url} (depth {depth})")
            response = self.session.get(url, timeout=self.timeout)
            
            # Check if successful
            if response.status_code != 200:
                logging.warning(f"Failed to fetch {url}: Status code {response.status_code}")
                return []
            
            # Add to crawled set
            self.crawled_urls.add(url)
            
            # Parse content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract and save text
            text = self._clean_text(soup)
            self._save_content(url, text, output_dir)
            
            # Get links
            links = self._extract_links(soup, self._get_base_url(url), url)
            
            # Add new links to queue
            new_links = [link for link in links if link not in self.crawled_urls and link not in self.queued_urls]
            self.queued_urls.update(new_links)
            
            # Add delay to avoid overloading the server
            time.sleep(self.delay)
            
            return new_links
            
        except Exception as e:
            logging.error(f"Error crawling {url}: {e}")
            return []
    
    def crawl(self, start_url, output_dir="crawled_data"):
        """Start crawling from the given URL"""
        # Validate starting URL
        if not self._is_valid_url(start_url):
            logging.error(f"Invalid starting URL: {start_url}")
            return
        
        logging.info(f"Starting crawl at {start_url}")
        logging.info(f"Max depth: {self.max_depth}, Max pages: {self.max_pages}")
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # Parse robots.txt if enabled
        base_url = self._get_base_url(start_url)
        self._parse_robots_txt(base_url)
        
        # Add starting URL to queue
        self.queued_urls.add(start_url)
        
        # Process queue with breadth-first search
        current_depth = 1
        while self.queued_urls and len(self.crawled_urls) < self.max_pages:
            # Get URLs for current depth
            urls_at_current_depth = list(self.queued_urls)
            self.queued_urls = set()
            
            # Process URLs in parallel
            with ThreadPoolExecutor(max_workers=self.threads) as executor:
                # Submit crawling tasks
                future_to_url = {
                    executor.submit(self._crawl_page, url, current_depth, output_dir): url 
                    for url in urls_at_current_depth
                }
            
            # Process results and collect new links
            for future in future_to_url:
                future.result()  # Wait for completion
            
            # Increase depth
            current_depth += 1
            
            # Check if we've reached max depth
            if current_depth > self.max_depth:
                break
        
        logging.info(f"Crawl completed. Processed {len(self.crawled_urls)} pages.")
        return self.crawled_urls