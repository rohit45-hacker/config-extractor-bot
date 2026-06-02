#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════
  CONFIG EXTRACTOR BOT - Telegram Bot
  Supports: EHI | DARK | OVPN formats
  Modes: NM | HC | WS
  Version: 3.0 | Premium Extractor
  Deploy: Koyeb (FREE), Render, Railway, VPS
═══════════════════════════════════════════════════════════════════
"""

import os
import sys
import base64
import json
import re
import logging
import asyncio
from datetime import datetime
from io import BytesIO

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    ContextTypes, filters
)

# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION - EDIT THESE OR USE ENV VARS
# ═══════════════════════════════════════════════════════════════════

BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
OWNER_NAME = os.environ.get("OWNER_NAME", "DʌʀᴋSᴘᴇᴄɪᴀʟ")
CHANNEL_LINK = os.environ.get("CHANNEL_LINK", "https://t.me/YourChannel")
DEV_USERNAME = os.environ.get("DEV_USERNAME", "@YourDev")
ADMIN_ID = os.environ.get("ADMIN_ID", "8217006573")
OWNER_USERNAME = os.environ.get("OWNER_USERNAME", "@DarkSpecial")

# Deployment settings
PORT = int(os.environ.get("PORT", "8080"))
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")  # For webhook mode
RAILWAY_PUBLIC_DOMAIN = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "")
KOYEB_APP_URL = os.environ.get("KOYEB_APP_URL", "")

# Rate limiting
USER_COOLDOWN = {}
COOLDOWN_SECONDS = 15

# ═══════════════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════════════

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════
# CONFIG EXTRACTOR CLASS
# ═══════════════════════════════════════════════════════════════════

class ConfigExtractor:
    """Premium Config Extractor"""

    def __init__(self):
        self.version = "3.0"

    def detect_format(self, content):
        content_str = content.decode('utf-8', errors='ignore') if isinstance(content, bytes) else content
        content_lower = content_str.lower()

        if 'darktunnel' in content_lower or 'dark' in content_str[:100].lower():
            return 'DARK'
        elif any(x in content_lower for x in ['ehi', 'ssh', 'payload', 'injector']):
            return 'EHI'
        elif 'openvpn' in content_lower or 'ovpn' in content_lower:
            return 'OVPN'
        else:
            return 'UNKNOWN'

    def decode_base64_content(self, content):
        try:
            if isinstance(content, bytes):
                try:
                    return content.decode('utf-8')
                except:
                    try:
                        decoded = base64.b64decode(content)
                        return decoded.decode('utf-8', errors='ignore')
                    except:
                        return content.decode('utf-8', errors='ignore')
            else:
                try:
                    decoded = base64.b64decode(content)
                    return decoded.decode('utf-8', errors='ignore')
                except:
                    return content
        except:
            return content if isinstance(content, str) else content.decode('utf-8', errors='ignore')

    def extract_server_details(self, content):
        content_str = content if isinstance(content, str) else content.decode('utf-8', errors='ignore')

        details = {
            'host': 'Not Found',
            'port': '80',
            'user': 'Not Found',
            'pass': 'Not Found',
            'sni': '',
            'mode': 'NORMAL',
            'payload': '',
            'ssl': False,
            'proxy': '',
            'expiration': '',
            'dns': ''
        }

        # Host extraction
        host_patterns = [
            r'Host[:\\s]+([a-zA-Z0-9][a-zA-Z0-9.-]*\\.[a-zA-Z]{2,})',
            r'Server[:\\s]+([a-zA-Z0-9][a-zA-Z0-9.-]*\\.[a-zA-Z]{2,})',
            r'host[:\\s]+([a-zA-Z0-9][a-zA-Z0-9.-]+)',
            r'remote\\s+([a-zA-Z0-9][a-zA-Z0-9.-]*\\.[a-zA-Z]{2,})',
            r'([a-zA-Z0-9][a-zA-Z0-9.-]*\\.netbill\\.site)',
            r'([a-zA-Z0-9][a-zA-Z0-9.-]*\\.kamatera\\.com)',
            r'([a-zA-Z0-9][a-zA-Z0-9.-]*\\.vultr\\.com)',
            r'([a-zA-Z0-9][a-zA-Z0-9.-]*\\.digitalocean\\.com)',
            r'([a-zA-Z0-9][a-zA-Z0-9.-]*\\.linode\\.com)',
            r'([a-zA-Z0-9][a-zA-Z0-9.-]*\\.aws\\.amazon\\.com)',
            r'([a-zA-Z0-9][a-zA-Z0-9.-]*\\.azure\\.com)',
            r'([a-zA-Z0-9][a-zA-Z0-9.-]*\\.cloud\\.google\\.com)',
        ]

        for pattern in host_patterns:
            match = re.search(pattern, content_str, re.IGNORECASE)
            if match:
                host = match.group(1).strip()
                if len(host) > 3 and '.' in host:
                    details['host'] = host
                    break

        # Port extraction
        port_patterns = [
            r'Port[:\\s]+(\\d{2,5})',
            r'port[:\\s]+(\\d{2,5})',
            r'remote\\s+\\S+\\s+(\\d{2,5})',
        ]

        for pattern in port_patterns:
            match = re.search(pattern, content_str, re.IGNORECASE)
            if match:
                port = match.group(1)
                if 1 <= int(port) <= 65535:
                    details['port'] = port
                    break

        # Default port based on SSL
        if 'ssl' in content_str.lower() or 'tls' in content_str.lower() or details['port'] == '443':
            if details['port'] == '80':
                details['port'] = '443'
            details['ssl'] = True

        # Username/Password
        user_patterns = [
            r'User(?:name)?[:\\s]+(\\S+)',
            r'user[:\\s]+(\\S+)',
        ]

        for pattern in user_patterns:
            match = re.search(pattern, content_str, re.IGNORECASE)
            if match:
                user = match.group(1).strip()
                if user and user.lower() not in ['not', 'found', 'none', 'null']:
                    details['user'] = user
                    break

        pass_patterns = [
            r'Pass(?:word)?[:\\s]+(\\S+)',
            r'pass[:\\s]+(\\S+)',
        ]

        for pattern in pass_patterns:
            match = re.search(pattern, content_str, re.IGNORECASE)
            if match:
                password = match.group(1).strip()
                if password and password.lower() not in ['not', 'found', 'none', 'null']:
                    details['pass'] = password
                    break

        # SNI/SSL
        sni_patterns = [
            r'SNI[:\\s]+([a-zA-Z0-9][a-zA-Z0-9.-]*\\.[a-zA-Z]{2,})',
            r'sni[:\\s]+([a-zA-Z0-9][a-zA-Z0-9.-]*\\.[a-zA-Z]{2,})',
        ]

        for pattern in sni_patterns:
            match = re.search(pattern, content_str, re.IGNORECASE)
            if match:
                details['sni'] = match.group(1).strip()
                details['ssl'] = True
                break

        if details['port'] in ['443', '8443', '9443']:
            details['ssl'] = True

        # Mode detection
        if '[crlf]' in content_str or 'Host:' in content_str or 'User-Agent:' in content_str or 'X-Online-Host:' in content_str:
            details['mode'] = 'HC (Header Custom)'
        elif 'normal' in content_str.lower() or 'direct' in content_str.lower():
            details['mode'] = 'NM (Normal Mode)'
        elif 'ws' in content_str.lower() or 'websocket' in content_str.lower():
            details['mode'] = 'WS (WebSocket)'
        else:
            details['mode'] = 'UNKNOWN'

        # Payload extraction
        payload_section = re.search(r'\\[PAYLOAD\\](.*?)(?:\\[|\\Z)', content_str, re.DOTALL | re.IGNORECASE)
        if payload_section:
            details['payload'] = payload_section.group(1).strip()
        else:
            payload_patterns = [
                r'(GET\\s+\\S+\\s+HTTP/[\\d.]+.*?(?:\\n\\n|\\r\\n\\r\\n|$))',
                r'(POST\\s+\\S+\\s+HTTP/[\\d.]+.*?(?:\\n\\n|\\r\\n\\r\\n|$))',
                r'(CONNECT\\s+\\S+\\s+HTTP/[\\d.]+.*?(?:\\n\\n|\\r\\n\\r\\n|$))',
            ]

            for pattern in payload_patterns:
                match = re.search(pattern, content_str, re.DOTALL | re.IGNORECASE)
                if match:
                    payload = match.group(1).strip()
                    if len(payload) > 20:
                        details['payload'] = payload
                        break

        # Expiration
        exp_match = re.search(r'Expir(?:y|ation|es)[:\\s]+(\\S+)', content_str, re.IGNORECASE)
        if exp_match:
            details['expiration'] = exp_match.group(1)

        # DNS
        dns_match = re.search(r'DNS[:\\s]+(\\S+)', content_str, re.IGNORECASE)
        if dns_match:
            details['dns'] = dns_match.group(1)

        return details

    def generate_import_link(self, details, format_type='DARK'):
        config_data = {
            'v': self.version,
            'host': details['host'],
            'port': details['port'],
            'user': details['user'],
            'pass': details['pass'],
            'sni': details['sni'],
            'mode': details['mode'],
            'ssl': details['ssl'],
            'payload': details['payload'],
            'dns': details['dns'],
            'timestamp': datetime.now().isoformat()
        }

        json_str = json.dumps(config_data, separators=(',', ':'))
        encoded = base64.b64encode(json_str.encode()).decode()

        if format_type == 'DARK':
            return f"darktunnel://{encoded}"
        elif format_type == 'EHI':
            return f"httpinjector://{encoded}"
        elif format_type == 'OVPN':
            return f"openvpn://{encoded}"
        else:
            return f"config://{encoded}"

    def format_payload_display(self, payload, max_lines=8):
        if not payload:
            return "No payload detected"

        display = payload.replace('\\r\\n', '[crlf]').replace('\\n', '[crlf]').replace('\\r', '[crlf]')
        display = display.replace('\r\n', '[crlf]').replace('\n', '[crlf]').replace('\r', '[crlf]')

        lines = display.split('[crlf]')
        lines = [l.strip() for l in lines if l.strip()]

        if len(lines) > max_lines:
            lines = lines[:max_lines]
            lines.append('...')

        return '[crlf]'.join(lines)

    def process_content(self, content, filename="config.txt"):
        try:
            decoded = self.decode_base64_content(content)
            format_type = self.detect_format(decoded)
            details = self.extract_server_details(decoded)
            import_link = self.generate_import_link(details, format_type)

            return {
                'success': True,
                'details': details,
                'import_link': import_link,
                'format': format_type,
                'filename': filename
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# ═══════════════════════════════════════════════════════════════════
# BOT HANDLERS
# ═══════════════════════════════════════════════════════════════════

extractor = ConfigExtractor()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    user = update.effective_user

    welcome_text = f"""
🔷 <b>Welcome to Premium Config Extractor Bot!</b> 🔷

👤 <b>User:</b> {user.first_name}
🆔 <b>ID:</b> <code>{user.id}</code>

📋 <b>How to use:</b>
1️⃣ Send me a config file (.ehi, .dark, .txt)
2️⃣ I'll extract server details automatically
3️⃣ Get styled output + import link

📁 <b>Supported Formats:</b>
• EHI (HTTP Injector)
• DARK (DarkTunnel)
• OVPN (OpenVPN)

⚡ <b>Features:</b>
✅ Auto format detection
✅ NM / HC / WS mode detection
✅ SSL/SNI extraction
✅ Payload parsing
✅ Import link generation

👑 <b>Owner:</b> {OWNER_NAME}
📢 <b>Channel:</b> {CHANNEL_LINK}
👨‍💻 <b>Dev:</b> {DEV_USERNAME}
    """

    keyboard = [
        [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("💬 Support Group", url=f"https://t.me/{DEV_USERNAME[1:]}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        welcome_text,
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command"""
    help_text = f"""
📖 <b>Bot Commands:</b>

/start - Start the bot
/help - Show this help message
/about - About the bot
/status - Check bot status

📁 <b>Send me any config file:</b>
• .ehi files (HTTP Injector)
• .dark files (DarkTunnel)  
• .txt files (Any text config)

⚙️ <b>What I extract:</b>
🎯 Server Host
🔌 Port
👤 Username
🔑 Password
🔒 SSL/SNI status
🚀 Payload details
📥 Import link

⏱️ <b>Rate Limit:</b> {COOLDOWN_SECONDS}s between requests
    """
    await update.message.reply_text(help_text, parse_mode='HTML')

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """About command"""
    about_text = f"""
🔷 <b>About Premium Extractor Bot</b> 🔷

🤖 <b>Bot Name:</b> Config Extractor
📊 <b>Version:</b> 3.0
🛠️ <b>Status:</b> Active ✅

👑 <b>Owner:</b> {OWNER_NAME}
📢 <b>Channel:</b> {CHANNEL_LINK}
👨‍💻 <b>Developer:</b> {DEV_USERNAME}
🆔 <b>Admin ID:</b> <code>{ADMIN_ID}</code>

📋 <b>Features:</b>
• EHI/DARK/OVPN format support
• NM/HC/WS mode detection
• SSL/SNI extraction
• Base64 import links
• Stylish output formatting

⚡ <b>Powered by Python & python-telegram-bot</b>
    """
    await update.message.reply_text(about_text, parse_mode='HTML')

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Status command"""
    user = update.effective_user

    is_admin = str(user.id) == ADMIN_ID
    admin_badge = "👑 ADMIN" if is_admin else "👤 USER"

    status_text = f"""
📊 <b>Bot Status</b> 📊

👤 <b>Your Status:</b> {admin_badge}
🆔 <b>Your ID:</b> <code>{user.id}</code>

🤖 <b>Bot:</b> Active ✅
📡 <b>Uptime:</b> Running
⚡ <b>Version:</b> 3.0

📁 <b>Supported:</b> EHI | DARK | OVPN
🚀 <b>Modes:</b> NM | HC | WS

⏱️ <b>Cooldown:</b> {COOLDOWN_SECONDS} seconds
    """
    await update.message.reply_text(status_text, parse_mode='HTML')

def check_cooldown(user_id):
    import time
    current_time = time.time()

    if str(user_id) == ADMIN_ID:
        return False, 0

    if user_id in USER_COOLDOWN:
        elapsed = current_time - USER_COOLDOWN[user_id]
        if elapsed < COOLDOWN_SECONDS:
            return True, COOLDOWN_SECONDS - int(elapsed)

    USER_COOLDOWN[user_id] = current_time
    return False, 0

async def process_config_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle document/file uploads"""
    user = update.effective_user
    message = update.message

    on_cooldown, remaining = check_cooldown(user.id)
    if on_cooldown:
        await message.reply_text(
            f"⏱️ <b>Please wait {remaining} seconds before next request!</b>\n\n"
            f"💡 <i>Upgrade to premium for no cooldown!</i>",
            parse_mode='HTML'
        )
        return

    if not message.document:
        await message.reply_text("❌ Please send a file!")
        return

    doc = message.document
    filename = doc.file_name or "unknown.txt"

    allowed_ext = ['.ehi', '.dark', '.txt', '.ovpn', '.conf']
    if not any(filename.lower().endswith(ext) for ext in allowed_ext):
        await message.reply_text(
            f"❌ <b>Unsupported file format!</b>\n\n"
            f"📁 <b>Supported:</b> .ehi, .dark, .txt, .ovpn, .conf",
            parse_mode='HTML'
        )
        return

    processing_msg = await message.reply_text(
        f"🔍 <b>Processing:</b> <code>{filename}</code>\n"
        f"⏳ Please wait...",
        parse_mode='HTML'
    )

    try:
        file = await context.bot.get_file(doc.file_id)
        file_bytes = await file.download_as_bytearray()

        result = extractor.process_content(bytes(file_bytes), filename)

        if not result['success']:
            await processing_msg.edit_text(
                f"❌ <b>Error processing file!</b>\n\n"
                f"<code>{result['error']}</code>",
                parse_mode='HTML'
            )
            return

        details = result['details']
        format_type = result['format']
        import_link = result['import_link']

        timestamp = datetime.now().strftime("%I:%M %p")
        ssl_status = f"✅ {details['sni']}" if details['ssl'] and details['sni'] else ("✅ Enabled" if details['ssl'] else "❌ Disabled")
        is_admin = str(user.id) == ADMIN_ID
        admin_tag = "👑 ADMIN" if is_admin else "👤 USER"

        response = f"""
🔷 <b>════[ PREMIUM EXTRACTOR ]════</b> 🔷

📁 <b>Name:</b> <code>{filename[:40]}</code>

🌐 <b>SERVER DETAILS</b> ]—✧
├─ 🎯 <b>Host:</b> <code>{details['host']}</code>
├─ 🔌 <b>Port:</b> <code>{details['port']}</code>
├─ 👤 <b>User:</b> <code>{details['user']}</code>
└─ 🔑 <b>Pass:</b> <code>{details['pass']}</code>

🚀 <b>INJECT DETAILS</b> ]—✧
├─ ⚙️ <b>Mode:</b> <code>{details['mode']}</code>
├─ 🔒 <b>SSL/SNI:</b> {ssl_status}
└─ 📦 <b>Payload:</b>
<pre>{extractor.format_payload_display(details['payload'])[:400]}</pre>

📥 <b>IMPORT LINK</b> (Copy Below)
Format: <code>{format_type}</code>
<code>{import_link[:400]}</code>
{"..." if len(import_link) > 400 else ""}

👤 <b>Requested by:</b> {admin_tag}
├─ 🆔 <code>{user.id}</code>
├─ 👑 {OWNER_NAME}
└─ 📢 {CHANNEL_LINK}

⏰ <code>{timestamp}</code> ✅ <b>Decrypted Successfully</b>
        """

        keyboard = [
            [InlineKeyboardButton("📋 Copy Import Link", callback_data=f"copy_{user.id}")],
            [InlineKeyboardButton("📢 Channel", url=CHANNEL_LINK),
             InlineKeyboardButton("👨‍💻 Dev", url=f"https://t.me/{DEV_USERNAME[1:]}")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await processing_msg.delete()
        await message.reply_text(
            response,
            parse_mode='HTML',
            reply_markup=reply_markup
        )

        await message.reply_text(
            f"📥 <b>Quick Copy Link:</b>\n\n"
            f"<code>{import_link}</code>",
            parse_mode='HTML'
        )

    except Exception as e:
        logger.error(f"Error processing file: {e}")
        await processing_msg.edit_text(
            f"❌ <b>Error:</b> <code>{str(e)}</code>\n\n"
            f"Please try again or contact {DEV_USERNAME}",
            parse_mode='HTML'
        )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages (paste config text)"""
    user = update.effective_user
    message = update.message

    if not message.text:
        return

    text = message.text
    if len(text) < 50:
        return

    on_cooldown, remaining = check_cooldown(user.id)
    if on_cooldown:
        await message.reply_text(
            f"⏱️ <b>Please wait {remaining} seconds!</b>",
            parse_mode='HTML'
        )
        return

    processing_msg = await message.reply_text(
        "🔍 <b>Processing pasted config...</b>\n⏳ Please wait...",
        parse_mode='HTML'
    )

    try:
        result = extractor.process_content(text, "pasted_config.txt")

        if not result['success']:
            await processing_msg.delete()
            return

        details = result['details']
        format_type = result['format']
        import_link = result['import_link']

        ssl_status = f"✅ {details['sni']}" if details['ssl'] and details['sni'] else ("✅ Enabled" if details['ssl'] else "❌ Disabled")
        is_admin = str(user.id) == ADMIN_ID
        admin_tag = "👑 ADMIN" if is_admin else "👤 USER"
        timestamp = datetime.now().strftime("%I:%M %p")

        response = f"""
🔷 <b>════[ PREMIUM EXTRACTOR ]════</b> 🔷

📁 <b>Name:</b> <code>Pasted Config</code>

🌐 <b>SERVER DETAILS</b> ]—✧
├─ 🎯 <b>Host:</b> <code>{details['host']}</code>
├─ 🔌 <b>Port:</b> <code>{details['port']}</code>
├─ 👤 <b>User:</b> <code>{details['user']}</code>
└─ 🔑 <b>Pass:</b> <code>{details['pass']}</code>

🚀 <b>INJECT DETAILS</b> ]—✧
├─ ⚙️ <b>Mode:</b> <code>{details['mode']}</code>
├─ 🔒 <b>SSL/SNI:</b> {ssl_status}
└─ 📦 <b>Payload:</b>
<pre>{extractor.format_payload_display(details['payload'])[:300]}</pre>

📥 <b>IMPORT LINK</b>
Format: <code>{format_type}</code>
<code>{import_link[:300]}</code>
{"..." if len(import_link) > 300 else ""}

👤 <b>Requested by:</b> {admin_tag}
├─ 🆔 <code>{user.id}</code>
└─ 👑 {OWNER_NAME}

⏰ <code>{timestamp}</code> ✅ <b>Decrypted</b>
        """

        keyboard = [
            [InlineKeyboardButton("📢 Channel", url=CHANNEL_LINK)],
            [InlineKeyboardButton("👨‍💻 Dev", url=f"https://t.me/{DEV_USERNAME[1:]}")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await processing_msg.delete()
        await message.reply_text(
            response,
            parse_mode='HTML',
            reply_markup=reply_markup
        )

        await message.reply_text(
            f"📥 <b>Quick Copy:</b>\n<code>{import_link}</code>",
            parse_mode='HTML'
        )

    except Exception as e:
        await processing_msg.delete()
        logger.error(f"Error processing text: {e}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")

    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ <b>An error occurred!</b>\n"
            "Please try again or contact the developer.",
            parse_mode='HTML'
        )

# ═══════════════════════════════════════════════════════════════════
# MAIN FUNCTION - Supports BOTH Polling & Webhook
# ═══════════════════════════════════════════════════════════════════

def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ ERROR: Please set BOT_TOKEN environment variable!")
        print("💡 Get token from @BotFather on Telegram")
        sys.exit(1)

    print("🔥 Starting Premium Config Extractor Bot...")
    print(f"👑 Owner: {OWNER_NAME}")
    print(f"📢 Channel: {CHANNEL_LINK}")
    print(f"👨‍💻 Dev: {DEV_USERNAME}")
    print("=" * 50)

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(MessageHandler(filters.Document.ALL, process_config_file))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_error_handler(error_handler)

    print("✅ Bot is running!")

    # Determine mode: Webhook (for cloud) or Polling (for local)
    webhook_url = WEBHOOK_URL or KOYEB_APP_URL or RAILWAY_PUBLIC_DOMAIN

    if webhook_url:
        # WEBHOOK MODE (for Koyeb, Render, Railway, VPS)
        if not webhook_url.startswith('http'):
            webhook_url = f"https://{webhook_url}"

        webhook_path = f"/webhook/{BOT_TOKEN.split(':')[1]}"
        full_webhook_url = f"{webhook_url}{webhook_path}"

        print(f"🌐 Webhook Mode: {full_webhook_url}")

        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=full_webhook_url,
        )
    else:
        # POLLING MODE (for local testing, Termux)
        print("📡 Polling Mode (Local Testing)")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
