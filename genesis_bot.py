import os
import asyncio
import json
import logging
import random
import re
import requests
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pytz

# Steel and Playwright
from steel import Steel
from playwright.async_api import async_playwright

# Telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode

# --- 1. CONFIGURATION ---
STEEL_API_KEY = "ste-wKE9oOAt04vWpm2DsAelzb0cGDP5WFIxQxhanuSMtpboVsJVPjmxnn6mqHirs1EhCvbf64YySZ0Wk2ubKk7D73Gppzz5AZpaR9a"
BOT_TOKEN = "7568580309RSYFss"
INITIAL_ADMIN = 160083223
LOGS_CHANNEL_ID = -100

SCRIPT_DIR = Path(__file__).parent.absolute()
USERS_FILE = SCRIPT_DIR / "approved_users.json"
ADMINS_FILE = SCRIPT_DIR / "admins.json"

# --- SCALING CONFIGURATION ---
STOP_FLAG = False
PARALLEL_WORKERS = 20  # Updated to 20 as requested
semaphore = asyncio.Semaphore(PARALLEL_WORKERS)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 2. DATA PERSISTENCE ---
def load_data(file_path, initial_val=None):
    if file_path.exists():
        with open(file_path, 'r') as f: return json.load(f)
    return [initial_val] if initial_val else []

def save_data(file_path, data):
    with open(file_path, 'w') as f: json.dump(data, f)

admins = load_data(ADMINS_FILE, INITIAL_ADMIN)
approved_users = load_data(USERS_FILE)

# --- 3. AUTOMATION ENGINE ---
class FacebookAutomation:
    def __init__(self):
        self.api_base = "http://72.60.39.128:4500"
        self.steel_client = Steel(steel_api_key=STEEL_API_KEY)

    async def fetch_email(self):
        try:
            # Added small timeout and retry for high concurrency
            response = requests.get(f"{self.api_base}/create", timeout=20).json()
            email = response.get("address")
            token = response.get("token")
            if not email:
                inner = json.loads(response.get("details", {}).get("details", {}).get("response", "{}"))
                email, token = inner.get("address"), inner.get("token")
            return email, token
        except: return None, None

    async def create_account(self, f_name, l_name):
        email, token = await self.fetch_email()
        if not email: return None

        # Start Steel Cloud Session
        try:
            session = self.steel_client.sessions.create(solve_captcha=True)
            cdp_url = f"wss://connect.steel.dev?apiKey={STEEL_API_KEY}&sessionId={session.id}"
        except Exception as e:
            logger.error(f"Steel Session Error: {e}")
            return None

        async with async_playwright() as p:
            # Connect over CDP for cloud browser control
            browser = await p.chromium.connect_over_cdp(cdp_url)
            try:
                context = browser.contexts[0]
                page = await context.new_page()
                
                await page.goto("https://www.facebook.com/r.php", wait_until="domcontentloaded")
                
                # Fill basic info
                await page.fill('input[name="firstname"]', f_name)
                await page.fill('input[name="lastname"]', l_name)
                await page.fill('input[name="reg_email__"]', email)
                
                try: 
                    await page.wait_for_selector('input[name="reg_email_confirmation__"]', timeout=3000)
                    await page.fill('input[name="reg_email_confirmation__"]', email)
                except: pass

                await page.select_option('#year', str(random.randint(1990, 2005)))
                await page.fill('input[name="reg_passwd__"]', "SoulCracks@90")
                await page.click('input[name="sex"][value="2"]') # Male
                await page.click('button[name="websubmit"]')

                # OTP Polling (Wait for FB to send email)
                otp = None
                for _ in range(15): 
                    if STOP_FLAG: break
                    await asyncio.sleep(10)
                    try:
                        r = requests.get(f"{self.api_base}/check/{token}", timeout=10).json()
                        for m in r.get("emails", []):
                            match = re.search(r"FB-(\d{5})", m.get("body", ""))
                            if match: otp = match.group(1); break
                    except: continue
                    if otp: break
                
                if not otp: return None

                # Confirming Account
                await page.wait_for_selector("#code_in_cliff", timeout=5000)
                await page.fill("#code_in_cliff", otp)
                await page.click('button[name="confirm"]')
                await asyncio.sleep(5)
                
                return {"username": f"{f_name} {l_name}", "email": email, "pass": "SoulCracks@90", "token": token}
            except Exception as e:
                logger.error(f"Automation Error: {e}")
                return None
            finally:
                await browser.close()
                self.steel_client.sessions.release(session.id)

# --- 4. WORKER & LOGGING ---
async def send_logs(context, msg):
    try:
        await context.bot.send_message(chat_id=LOGS_CHANNEL_ID, text=msg, parse_mode=ParseMode.MARKDOWN)
    except: pass

async def worker(update, context, index):
    async with semaphore: # Limits to 20 at a time
        if STOP_FLAG: return
        
        f_names = ["James", "Michael", "Robert", "John", "David", "Richard", "Chris", "Kevin"]
        l_names = ["Smith", "Williams", "Johnson", "Brown", "Garcia", "Miller", "Davis"]
        f_name, l_name = random.choice(f_names), random.choice(l_names)

        auto = FacebookAutomation()
        res = await auto.create_account(f_name, l_name)
        
        ist = pytz.timezone('Asia/Kolkata')
        time_str = datetime.now(ist).strftime("%Y-%m-%d %I:%M:%S %p %Z")

        if res:
            msg = (
                f"✅ Account #{index} Created Successfully!\n\n"
                f"👤 Username: {res['username']}\n"
                f"📧 Email: `{res['email']}`\n"
                f"🔑 Password: `{res['pass']}`\n"
                f"🎫 Mail Token: `{res['token']}`\n"
                f"🕐 Created: {time_str}"
            )
            # Staggered delivery to avoid Telegram flood limits
            await asyncio.sleep(random.uniform(0.1, 1.5))
            await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
            await send_logs(context, f"📊 **NEW ACCOUNT**\n{msg}")
        else:
            err = f"❌ Failed Account #{index} at {time_str}"
            await update.message.reply_text(err)

# --- 5. TELEGRAM HANDLERS ---
async def create_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global STOP_FLAG
    uid = update.effective_user.id
    if uid not in admins and str(uid) not in approved_users:
        return await update.message.reply_text("❌ Not authorized.")

    STOP_FLAG = False
    mode = context.args[0] if context.args else "1"

    if mode.lower() == "all":
        await update.message.reply_text(f"♾️ Infinite Burst Started (Parallel: {PARALLEL_WORKERS})...")
        idx = 1
        while not STOP_FLAG:
            # Create 20 tasks and start them ALL at once
            tasks = [asyncio.create_task(worker(update, context, idx + j)) for j in range(PARALLEL_WORKERS)]
            await asyncio.gather(*tasks)
            idx += PARALLEL_WORKERS
    else:
        try:
            count = int(mode)
        except:
            return await update.message.reply_text("Usage: /create <number> or /create all")

        await update.message.reply_text(f"🚀 Launching {count} sessions in burst mode...")
        
        # This schedules ALL requested accounts to start. 
        # The semaphore inside worker() ensures exactly 20 run at a time.
        all_tasks = [asyncio.create_task(worker(update, context, i)) for i in range(1, count + 1)]
        await asyncio.gather(*all_tasks)
            
        await update.message.reply_text("✅ All accounts in this batch are finished.")

async def stop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global STOP_FLAG
    STOP_FLAG = True
    await update.message.reply_text("🛑 Stopping... Active workers will finish their current task.")

async def admin_manage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    cmd = update.message.text.split()[0][1:]
    target = context.args[0] if context.args else None
    if not target: return await update.message.reply_text("Provide ID.")

    if cmd == "add_admin" and uid == INITIAL_ADMIN:
        admins.append(int(target))
        save_data(ADMINS_FILE, admins)
        await update.message.reply_text(f"👑 Admin Added: {target}")
    elif cmd == "remove_admin" and uid == INITIAL_ADMIN:
        if int(target) in admins: admins.remove(int(target))
        save_data(ADMINS_FILE, admins)
        await update.message.reply_text(f"🗑️ Admin Removed: {target}")
    elif cmd == "approve" and uid in admins:
        approved_users.append(target)
        save_data(USERS_FILE, approved_users)
        await update.message.reply_text(f"✅ Approved: {target}")
    elif cmd == "disapprove" and uid in admins:
        if target in approved_users: approved_users.remove(target)
        save_data(USERS_FILE, approved_users)
        await update.message.reply_text(f"❌ Disapproved: {target}")

# --- 6. MAIN ---
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("create", create_cmd))
    app.add_handler(CommandHandler("stop", stop_cmd))
    app.add_handler(CommandHandler("add_admin", admin_manage))
    app.add_handler(CommandHandler("remove_admin", admin_manage))
    app.add_handler(CommandHandler("approve", admin_manage))
    app.add_handler(CommandHandler("disapprove", admin_manage))
    
    print(f"🚀 Bot Running | Workers: {PARALLEL_WORKERS} | Steel.dev Active")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
