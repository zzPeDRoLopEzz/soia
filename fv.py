import cloudscraper
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import sys

# List of 20 common user agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59",
    "Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Trident/7.0; rv:11.0) like Gecko",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 OPR/77.0.4054.90",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Vivaldi/4.0",
    "Mozilla/5.0 (Linux; Android 10; SM-G980F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/91.0.4472.80 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Linux; Android 9; SM-G960F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
]

# Optimized worker function
def worker(target_url, duration, worker_id, use_cloudscraper):
    end_time = time.time() + duration
    request_count = 0
    success_count = 0
    error_count = 0
    
    # Create a session for this worker
    if use_cloudscraper:
        scraper = cloudscraper.create_scraper()
    else:
        import requests
        session = requests.Session()
    
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache',
    }
    
    while time.time() < end_time:
        try:
            # Alternate between GET and POST requests
            if random.random() > 0.5:  # 50% chance for GET/POST
                # GET request
                if use_cloudscraper:
                    response = scraper.get(target_url, headers=headers, timeout=10)
                else:
                    response = session.get(target_url, headers=headers, timeout=10)
            else:
                # POST request with random data
                data = {'random': str(random.randint(0, 1000000))}
                if use_cloudscraper:
                    response = scraper.post(target_url, data=data, headers=headers, timeout=10)
                else:
                    response = session.post(target_url, data=data, headers=headers, timeout=10)
            
            request_count += 1
            if response.status_code == 200:
                success_count += 1
            else:
                error_count += 1
            
            # Random sleep to simulate more natural traffic (0-100ms)
            time.sleep(random.uniform(0, 0.1))
            
        except Exception as e:
            error_count += 1
            request_count += 1
            # Short sleep on error to prevent tight loops
            time.sleep(0.1)
    
    return {
        'worker_id': worker_id,
        'requests': request_count,
        'success': success_count,
        'errors': error_count
    }

def main():
    parser = argparse.ArgumentParser(description='Website Load Testing Tool')
    parser.add_argument('url', help='Target URL to test')
    parser.add_argument('-d', '--duration', type=int, default=60, help='Test duration in seconds (default: 60)')
    parser.add_argument('-w', '--workers', type=int, default=30, help='Number of concurrent workers (default: 30)')
    parser.add_argument('-c', '--cloudscraper', action='store_true', help='Use cloudscraper to bypass Cloudflare')
    
    args = parser.parse_args()
    
    if not args.url.startswith(('http://', 'https://')):
        print("Error: URL must start with http:// or https://")
        sys.exit(1)
    
    print(f"Starting test with {args.workers} workers for {args.duration} seconds against {args.url}")
    if args.cloudscraper:
        print("Using cloudscraper to bypass Cloudflare protections")
    
    start_time = time.time()
    total_requests = 0
    total_success = 0
    total_errors = 0
    
    # Using ThreadPoolExecutor for optimized worker management
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(worker, args.url, args.duration, i, args.cloudscraper) 
                  for i in range(args.workers)]
        
        for future in as_completed(futures):
            result = future.result()
            total_requests += result['requests']
            total_success += result['success']
            total_errors += result['errors']
            print(f"Worker {result['worker_id']} completed: {result['requests']} requests")
    
    end_time = time.time()
    actual_duration = end_time - start_time
    
    print("\nTest completed!")
    print(f"Actual duration: {actual_duration:.2f} seconds")
    print(f"Total requests: {total_requests}")
    print(f"Successful responses: {total_success}")
    print(f"Errors: {total_errors}")
    print(f"Requests per second: {total_requests/actual_duration:.2f}")

if __name__ == "__main__":
    main()
