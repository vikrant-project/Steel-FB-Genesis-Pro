# 🎭 Steel FB Genesis Pro v2.0
> **An elite, cloud-scaled Facebook automation engine powered by Steel.dev and Playwright.**

[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/Engine-Playwright-green)](https://playwright.dev/)
[![Cloud-Browser](https://img.shields.io/badge/Platform-Steel.dev-orange)](https://steel.dev/)
[![Status](https://img.shields.io/badge/Status-Operational-success)](#)

---

## 🔍 What is this Code?
**Steel FB Genesis Pro** is a high-concurrency automation suite designed for large-scale Facebook account creation. Unlike traditional local scrapers, this engine offloads the heavy browser lifting to **Steel Cloud Browsers**, allowing for massive scaling without triggering local hardware signatures.

It utilizes an advanced **Semaphore-based Burst Mode** that manages 20+ parallel workers, handling everything from identity synthesis to automated OTP retrieval via dedicated mail APIs.

---

## 🚀 Why Use It?
Manual account creation is blocked by sophisticated fingerprinting. This tool provides:
* **Stealth Cloud Execution:** Every session runs on a clean, isolated cloud instance via `steel.dev`.
* **Automated Captcha Solving:** Integrated cloud-side captcha resolution.
* **Burst Concurrency:** Optimized to handle 20 parallel accounts at once using `asyncio.Semaphore`.
* **Zero-Touch Mail Verification:** Automatically polls custom mail APIs for `FB-XXXXX` verification codes.

---

## 💎 Importance
For developers and marketers requiring large-scale social environments:
1.  **Anti-Fingerprint Technology:** Every browser instance has a unique, non-leaking fingerprint.
2.  **Scalable Architecture:** The `/create all` command enables an infinite loop of account generation.
3.  **Real-Time Monitoring:** Includes a dedicated Telegram Logging Channel (`LOGS_CHANNEL_ID`) for tracking success rates and credentials.

---

## ⚙️ How It Works
The engine follows a sophisticated **Genesis Pipeline**:

1.  **Identity Synthesis:** Randomly selects high-authority names and calculates age parameters (1990-2005).
2.  **Cloud Session Handshake:** Connects to `wss://connect.steel.dev` to launch a remote Chromium instance.
3.  **The Registration Loop:** * Navigates to the Facebook registration portal.
    * Injects credentials using human-mimicking typing delays.
    * Triggers the `/create` API call for a temporary email and mail-token.
4.  **OTP Polling:** A background task polls the mail server every 10 seconds for the Facebook verification string.
5.  **Finalization:** Confirms the account and logs the output in a formatted Telegram card.

---

## 📊 Comparison: Why Genesis Pro?

| Feature | Standard Local Scripts | Steel Genesis Pro |
| :--- | :--- | :--- |
| **Concurrency** | 1-2 Threads (Limited) | 20+ Workers (Cloud Scaled) |
| **IP Management** | Requires Proxy Rotation | Native Cloud Exit IPs |
| **Fingerprinting** | Easily detected | Zero-leak Cloud Browsers |
| **OTP Handling** | Manual | Automated API Polling |
| **Hardware** | Heavy RAM/CPU usage | Serverless (Runs on any VPS) |

---

## 🛠️ Installation & Setup

### 1. Prerequisites
* **Python 3.10+**
* **Steel.dev API Key:** Required for cloud browser control.
* **Playwright:** `pip install playwright`

### 2. Clone & Install
```bash
git clone https://github.com/vikrant-project/Steel-FB-Genesis-Pro
cd Steel-FB-Genesis-Pro
pip install steel-sdk playwright python-telegram-bot pytz requests
```

### 3. Configuration
Open `genesis_bot.py` and set:
* `STEEL_API_KEY`: Your Steel.dev key.
* `BOT_TOKEN`: Telegram bot token.
* `LOGS_CHANNEL_ID`: Channel for account logs.

### 4. Running the Engine
```bash
python3 genesis_bot.py
```

---

## 🎨 Professional UI & Commands
* `🚀 /create <num>` - Launch a specific batch of accounts.
* `♾️ /create all` - Infinite burst mode (20 parallel sessions).
* `🛑 /stop` - Gracefully shutdown all active cloud workers.
* `✅ /approve <id>` - Grant access to specific users.

---
**Disclaimer:** This tool is for educational and testing purposes only. Ensure compliance with the Terms of Service of the platforms involved. The developer is not responsible for any misuse.
