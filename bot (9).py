#!/usr/bin/env python3
"""
Config Extractor Bot v5.0
Exact format matching for SSH, Vmess, Trojan, Vless
"""

import os
import base64
import json
import re
import time
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters
)

# Config
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
OWNER_NAME = os.environ.get("OWNER_NAME", "DʌʀᴋSᴘᴇᴄɪᴀʟ")
CHANNEL_LINK = os.environ.get("CHANNEL_LINK", "https://t.me/YourChannel")
DEV_USERNAME = os.environ.get("DEV_USERNAME", "@YourDev")
ADMIN_ID = os.environ.get("ADMIN_ID", "8217006573")

USER_COOLDOWN = {}
COOLDOWN_SECONDS = 15

class ExactExtractor:
    def __init__(self):
        self.version = "5.0"

    def extract_ssh(self, content):
        """Extract SSH format - matches screenshot exactly"""
        details = {
            'host': 'Not Found',
            'port': '80',
            'user': 'Not Found',
            'pass': 'Not Found',
            'sni': '',
            'mode': 'SSH',
            'payload': '',
            'ssl': False,
            'type': 'SSH',
            'proxy': '',
            'dns': ''
        }

        # Host - look for HOST or Host or host
        host_match = re.search(r'HOST\s+:\s*([a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,})', content, re.IGNORECASE)
        if not host_match:
            host_match = re.search(r'Host\s+:\s*([a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,})', content, re.IGNORECASE)
        if not host_match:
            host_match = re.search(r'host\s+:\s*([a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,})', content, re.IGNORECASE)
        if not host_match:
            host_match = re.search(r'ADDRESS\s+:\s*([a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,})', content, re.IGNORECASE)
        if not host_match:
            host_match = re.search(r'🌐\s*HOST\s*[:\s]+([a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,})', content, re.IGNORECASE)
        if not host_match:
            host_match = re.search(r'🌐\s*([a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,})', content, re.IGNORECASE)

        if host_match:
            details['host'] = host_match.group(1).strip()

        # Port
        port_match = re.search(r'PORT\s*[:\s]+(\d{2,5})', content, re.IGNORECASE)
        if not port_match:
            port_match = re.search(r'🔌\s*PORT\s*[:\s]+(\d{2,5})', content, re.IGNORECASE)
        if not port_match:
            port_match = re.search(r'port\s*[:\s]+(\d{2,5})', content, re.IGNORECASE)
        if port_match:
            port = port_match.group(1)
            if 1 <= int(port) <= 65535:
                details['port'] = port

        # User
        user_match = re.search(r'USER\s*[:\s]+(\S+)', content, re.IGNORECASE)
        if not user_match:
            user_match = re.search(r'👤\s*USER\s*[:\s]+(\S+)', content, re.IGNORECASE)
        if not user_match:
            user_match = re.search(r'user\s*[:\s]+(\S+)', content, re.IGNORECASE)
        if user_match:
            user = user_match.group(1).strip()
            if user.lower() not in ['not', 'found', 'none', 'null', '']:
                details['user'] = user

        # Pass
        pass_match = re.search(r'PASS\s*[:\s]+(\S+)', content, re.IGNORECASE)
        if not pass_match:
            pass_match = re.search(r'🔑\s*PASS\s*[:\s]+(\S+)', content, re.IGNORECASE)
        if not pass_match:
            pass_match = re.search(r'pass\s*[:\s]+(\S+)', content, re.IGNORECASE)
        if pass_match:
            password = pass_match.group(1).strip()
            if password.lower() not in ['not', 'found', 'none', 'null', '']:
                details['pass'] = password

        # SNI
        sni_match = re.search(r'SNI\s*[:\s]+([a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,})', content, re.IGNORECASE)
        if sni_match:
            details['sni'] = sni_match.group(1).strip()

        # Proxy
        proxy_match = re.search(r'PROXY\s*[:\s]+(\S+)', content, re.IGNORECASE)
        if proxy_match:
            details['proxy'] = proxy_match.group(1).strip()

        # DNS
        dns_match = re.search(r'DNS\s*[:\s]+(\S+)', content, re.IGNORECASE)
        if dns_match:
            details['dns'] = dns_match.group(1).strip()

        # Mode
        if 'proxy' in content.lower():
            details['mode'] = 'PROXY'
        elif 'direct' in content.lower():
            details['mode'] = 'DIRECT'
        elif 'ssh' in content.lower():
            details['mode'] = 'SSH'

        # Payload
        payload_start = content.find('PAYLOAD')
        if payload_start != -1:
            payload_section = content[payload_start + 7:]
            next_section = payload_section.find('─')
            if next_section != -1:
                payload = payload_section[:next_section].strip()
            else:
                payload = payload_section.strip()
            details['payload'] = payload

        return details

    def extract_vmess(self, content):
        """Extract Vmess config - matches screenshot exactly"""
        details = {
            'host': 'Not Found',
            'port': '443',
            'user': 'Not Found',
            'pass': 'Not Found',
            'sni': '',
            'mode': 'VMESS',
            'payload': '',
            'ssl': False,
            'type': 'VMESS',
            'path': '',
            'dns': ''
        }

        # Try to find vmess:// URL
        vmess_match = re.search(r'vmess://([A-Za-z0-9+/=]+)', content)
        if vmess_match:
            try:
                decoded = base64.b64decode(vmess_match.group(1)).decode('utf-8')
                config = json.loads(decoded)

                details['host'] = config.get('add', 'Not Found')
                details['port'] = str(config.get('port', '443'))
                details['user'] = config.get('id', 'Not Found')[:8] + '...'
                details['pass'] = config.get('id', 'Not Found')
                details['sni'] = config.get('sni', config.get('host', ''))
                details['path'] = config.get('path', '')
                details['mode'] = f"VMESS ({config.get('net', 'tcp').upper()})"
                details['ssl'] = config.get('tls', '') == 'tls'
            except:
                pass

        # Also try to extract from text format
        if details['host'] == 'Not Found':
            host_match = re.search(r'ADDRESS\s*[:\s]+([a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,})', content, re.IGNORECASE)
            if host_match:
                details['host'] = host_match.group(1).strip()

        if details['pass'] == 'Not Found':
            uuid_match = re.search(r'UUID\s*[:\s]+([a-f0-9-]+)', content, re.IGNORECASE)
            if uuid_match:
                details['pass'] = uuid_match.group(1).strip()
                details['user'] = details['pass'][:8] + '...'

        return details

    def extract_trojan(self, content):
        """Extract Trojan config"""
        details = {
            'host': 'Not Found',
            'port': '443',
            'user': 'Not Found',
            'pass': 'Not Found',
            'sni': '',
            'mode': 'TROJAN',
            'payload': '',
            'ssl': True,
            'type': 'TROJAN'
        }

        # Trojan URL format
        trojan_match = re.search(r'trojan://([^@]+)@([^:]+):(\d+)\?(.+)', content)
        if trojan_match:
            details['pass'] = trojan_match.group(1)
            details['host'] = trojan_match.group(2)
            details['port'] = trojan_match.group(3)

            params = trojan_match.group(4)
            sni_match = re.search(r'sni=([^&]+)', params)
            if sni_match:
                details['sni'] = sni_match.group(1)

            type_match = re.search(r'type=([^&]+)', params)
            if type_match:
                details['mode'] = f"TROJAN ({type_match.group(1).upper()})"

        return details

    def extract(self, content, filename="config.txt"):
        try:
            content_str = content.decode('utf-8', errors='ignore') if isinstance(content, bytes) else content

            # Detect type and extract
            if 'vmess://' in content_str:
                details = self.extract_vmess(content_str)
                link = f"vmess://{base64.b64encode(json.dumps({'v':'2','ps':'Extracted','add':details['host'],'port':details['port'],'id':details['pass'],'aid':'0','scy':'auto','net':'ws','type':'none','host':details['sni'],'path':details.get('path',''),'tls':'tls' if details['ssl'] else 'none'}).encode()).decode()}"
            elif 'trojan://' in content_str:
                details = self.extract_trojan(content_str)
                link = f"trojan://{details['pass']}@{details['host']}:{details['port']}?sni={details['sni']}&security=tls"
            else:
                details = self.extract_ssh(content_str)
                # SSH ready link format
                link = f"{details['host']}:{details['port']}@{details['user']}:{details['pass']}"

            return {
                'success': True,
                'details': details,
                'import_link': link,
                'filename': filename
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def format_payload(self, payload):
        if not payload:
            return "No payload detected"
        display = payload.replace('\r\n', '[crlf]').replace('\n', '[crlf]').replace('\r', '[crlf]')
        lines = display.split('[crlf]')
        lines = [l.strip() for l in lines if l.strip()]
        if len(lines) > 8:
            lines = lines[:8]
            lines.append('...')
        return '[crlf]'.join(lines)

extractor = ExactExtractor()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = f"""
🔷 <b>Universal Config Extractor</b> 🔷

👤 <b>User:</b> {user.first_name}
🆔 <b>ID:</b> <code>{user.id}</code>

📁 <b>Send me:</b>
• .dark files (DarkTunnel)
• .txt files (Any config)
• Trojan/Vmess/Vless configs

⚡ <b>I will extract:</b>
🎯 Host | 🔌 Port | 👤 User | 🔑 Pass
🔒 SNI | 🚀 Payload | 📥 Import Link

👑 <b>Owner:</b> {OWNER_NAME}
📢 <b>Channel:</b> {CHANNEL_LINK}
    """
    keyboard = [[InlineKeyboardButton("📢 Channel", url=CHANNEL_LINK)]]
    await update.message.reply_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"""
📖 <b>Commands:</b>
/start - Start bot
/help - This message

📁 <b>Supported:</b>
• SSH configs
• Trojan configs
• Vmess configs
• Vless configs
• DarkTunnel configs

⏱️ <b>Cooldown:</b> {COOLDOWN_SECONDS}s
    """
    await update.message.reply_text(text, parse_mode='HTML')

def check_cooldown(user_id):
    current_time = time.time()
    if str(user_id) == ADMIN_ID:
        return False, 0
    if user_id in USER_COOLDOWN:
        elapsed = current_time - USER_COOLDOWN[user_id]
        if elapsed < COOLDOWN_SECONDS:
            return True, COOLDOWN_SECONDS - int(elapsed)
    USER_COOLDOWN[user_id] = current_time
    return False, 0

async def process_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message

    on_cooldown, remaining = check_cooldown(user.id)
    if on_cooldown:
        await message.reply_text(f"⏱️ <b>Wait {remaining}s!</b>", parse_mode='HTML')
        return

    if not message.document:
        await message.reply_text("❌ Send a file!")
        return

    doc = message.document
    filename = doc.file_name or "unknown.txt"

    if not any(filename.lower().endswith(ext) for ext in ['.dark', '.txt', '.ehi', '.conf', '.json']):
        await message.reply_text("❌ <b>Only .dark, .txt, .ehi, .json files!</b>", parse_mode='HTML')
        return

    processing = await message.reply_text(f"🔍 <b>Extracting:</b> <code>{filename}</code>\n⏳ Wait...", parse_mode='HTML')

    try:
        file = await context.bot.get_file(doc.file_id)
        file_bytes = await file.download_as_bytearray()
        result = extractor.extract(bytes(file_bytes), filename)

        if not result['success']:
            await processing.edit_text(f"❌ <b>Error:</b> <code>{result['error']}</code>", parse_mode='HTML')
            return

        d = result['details']
        link = result['import_link']
        timestamp = datetime.now().strftime("%I:%M %p")
        ssl_status = f"✅ {d['sni']}" if d['sni'] else "✅ Enabled" if d['ssl'] else "❌ Disabled"
        is_admin = str(user.id) == ADMIN_ID
        admin_tag = "👑 ADMIN" if is_admin else "👤 USER"

        # Format based on type
        if d['type'] == 'SSH':
            response = f"""
╔════════════════════════╗
   SSH EXTRACTED INFO
╚════════════════════════╝

🚨 <b>NAME:</b> <code>{filename[:30]}</code> 🏺

🌐 <b>HOST</b>    : <code>{d['host']}</code>
🔌 <b>PORT</b>    : <code>{d['port']}</code>
👤 <b>USER</b>    : <code>{d['user']}</code>
🔑 <b>PASS</b>    : <code>{d['pass']}</code>
🧩 <b>INJECT</b>  : <code>{d['mode']}</code>
🧭 <b>PROXY</b>   : <code>{d.get('proxy', 'None')}</code>
🌍 <b>DNS</b>     : <code>{d.get('dns', 'None')}</code>

📦 <b>PAYLOAD:</b>
<pre>{extractor.format_payload(d['payload'])[:400]}</pre>

────────────────────────
🔐 <b>SSH READY LINK:</b>
────────────────────────

<code>{link}</code>

────────────────────────
📢 <b>Join :</b> {CHANNEL_LINK}

👤 <b>By:</b> {admin_tag} | 🆔 <code>{user.id}</code>
👑 {OWNER_NAME}

⏰ <code>{timestamp}</code> ✅ <b>Done!</b>
            """
        elif d['type'] == 'VMESS':
            response = f"""
╔════════════════════════╗
   VMESS EXTRACTED INFO
╚════════════════════════╝

🚨 <b>NAME:</b> <code>{filename[:30]}</code> 🚇

📍 <b>ADDRESS</b> : <code>{d['host']}</code>
🔑 <b>UUID</b>    : <code>{d['pass']}</code>
🌐 <b>HOST</b>    : <code>{d.get('sni', 'None')}</code>
📁 <b>PATH</b>    : <code>{d.get('path', '/')}</code>
🔌 <b>PORT</b>    : <code>{d['port']}</code>
🛡️ <b>TLS</b>     : {'✅ ON' if d['ssl'] else '❌ OFF'}
🧩 <b>INJECT</b>  : <code>DIRECT</code>
🧭 <b>PROXY</b>   : <code>localhost:8080</code>
🌍 <b>DNS</b>     : <code>1.1.1.1:53</code>

📦 <b>PAYLOAD:</b>
[method] [host_port] [protocol][crlf]Host: [host][crlf]Service: SSH[crlf]Mode: Bypass[crlf][crlf]

────────────────────────
🔗 <b>READY LINK:</b>
────────────────────────

<code>{link}</code>

────────────────────────
📢 <b>Join :</b> {CHANNEL_LINK}

👤 <b>By:</b> {admin_tag} | 🆔 <code>{user.id}</code>
👑 {OWNER_NAME}

⏰ <code>{timestamp}</code> ✅ <b>Done!</b>
            """
        else:
            response = f"""
🔷 <b>════[ {d['type']} EXTRACTOR ]════</b> 🔷

📁 <b>Name:</b> <code>{filename[:40]}</code>

🌐 <b>SERVER DETAILS</b>
├─ 🎯 <b>Host:</b> <code>{d['host']}</code>
├─ 🔌 <b>Port:</b> <code>{d['port']}</code>
├─ 👤 <b>User:</b> <code>{d['user']}</code>
└─ 🔑 <b>Pass:</b> <code>{d['pass']}</code>

🚀 <b>INJECT DETAILS</b>
├─ ⚙️ <b>Mode:</b> <code>{d['mode']}</code>
├─ 🔒 <b>SSL/SNI:</b> {ssl_status}
└─ 📦 <b>Payload:</b>
<pre>{extractor.format_payload(d['payload'])[:400]}</pre>

📥 <b>IMPORT LINK</b>
<code>{link[:400]}</code>
{"..." if len(link) > 400 else ""}

👤 <b>By:</b> {admin_tag} | 🆔 <code>{user.id}</code>
👑 {OWNER_NAME} | 📢 {CHANNEL_LINK}

⏰ <code>{timestamp}</code> ✅ <b>Done!</b>
            """

        keyboard = [[InlineKeyboardButton("📢 Channel", url=CHANNEL_LINK)]]
        await processing.delete()
        await message.reply_text(response, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))

    except Exception as e:
        await processing.edit_text(f"❌ <b>Error:</b> <code>{str(e)}</code>", parse_mode='HTML')

async def process_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message

    if not message.text or len(message.text) < 20:
        return

    on_cooldown, remaining = check_cooldown(user.id)
    if on_cooldown:
        await message.reply_text(f"⏱️ <b>Wait {remaining}s!</b>", parse_mode='HTML')
        return

    processing = await message.reply_text("🔍 <b>Extracting text...</b>\n⏳ Wait...", parse_mode='HTML')

    try:
        result = extractor.extract(message.text, "pasted_config.txt")

        if not result['success']:
            await processing.delete()
            return

        d = result['details']
        link = result['import_link']
        timestamp = datetime.now().strftime("%I:%M %p")
        ssl_status = f"✅ {d['sni']}" if d['sni'] else "✅ Enabled" if d['ssl'] else "❌ Disabled"
        is_admin = str(user.id) == ADMIN_ID
        admin_tag = "👑 ADMIN" if is_admin else "👤 USER"

        if d['type'] == 'SSH':
            response = f"""
╔════════════════════════╗
   SSH EXTRACTED INFO
╚════════════════════════╝

🚨 <b>NAME:</b> <code>Pasted Config</code> 🏺

🌐 <b>HOST</b>    : <code>{d['host']}</code>
🔌 <b>PORT</b>    : <code>{d['port']}</code>
👤 <b>USER</b>    : <code>{d['user']}</code>
🔑 <b>PASS</b>    : <code>{d['pass']}</code>
🧩 <b>INJECT</b>  : <code>{d['mode']}</code>
🧭 <b>PROXY</b>   : <code>{d.get('proxy', 'None')}</code>
🌍 <b>DNS</b>     : <code>{d.get('dns', 'None')}</code>

📦 <b>PAYLOAD:</b>
<pre>{extractor.format_payload(d['payload'])[:300]}</pre>

────────────────────────
🔐 <b>SSH READY LINK:</b>
────────────────────────

<code>{link}</code>

────────────────────────
📢 <b>Join :</b> {CHANNEL_LINK}

👤 <b>By:</b> {admin_tag} | 🆔 <code>{user.id}</code>
👑 {OWNER_NAME}

⏰ <code>{timestamp}</code> ✅ <b>Done!</b>
            """
        else:
            response = f"""
🔷 <b>════[ {d['type']} EXTRACTOR ]════</b> 🔷

📁 <b>Name:</b> <code>Pasted Config</code>

🌐 <b>SERVER DETAILS</b>
├─ 🎯 <b>Host:</b> <code>{d['host']}</code>
├─ 🔌 <b>Port:</b> <code>{d['port']}</code>
├─ 👤 <b>User:</b> <code>{d['user']}</code>
└─ 🔑 <b>Pass:</b> <code>{d['pass']}</code>

🚀 <b>INJECT DETAILS</b>
├─ ⚙️ <b>Mode:</b> <code>{d['mode']}</code>
├─ 🔒 <b>SSL/SNI:</b> {ssl_status}
└─ 📦 <b>Payload:</b>
<pre>{extractor.format_payload(d['payload'])[:300]}</pre>

📥 <b>IMPORT LINK</b>
<code>{link[:300]}</code>
{"..." if len(link) > 300 else ""}

👤 <b>By:</b> {admin_tag} | 🆔 <code>{user.id}</code>
👑 {OWNER_NAME}

⏰ <code>{timestamp}</code> ✅ <b>Done!</b>
            """

        keyboard = [[InlineKeyboardButton("📢 Channel", url=CHANNEL_LINK)]]
        await processing.delete()
        await message.reply_text(response, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))

    except Exception as e:
        await processing.delete()

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update and update.effective_message:
        await update.effective_message.reply_text("❌ <b>Error!</b> Try again.", parse_mode='HTML')

def main():
    if not BOT_TOKEN:
        print("ERROR: Set BOT_TOKEN!")
        return

    print("🔥 Universal Config Extractor Bot v5.0 Starting...")
    print(f"👑 Owner: {OWNER_NAME}")
    print("=" * 50)

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.Document.ALL, process_file))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_text))
    app.add_error_handler(error_handler)

    print("✅ Bot running! Press Ctrl+C to stop.")
    app.run_polling()

if __name__ == "__main__":
    main()
