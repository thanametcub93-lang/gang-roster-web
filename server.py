import os
import sys
import json
import socket
import urllib.parse
import urllib.request
import datetime
import time
import threading
import uuid
import http.cookies
from collections import defaultdict
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

# Fix Windows console encoding
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PORT = int(os.environ.get("PORT", 8080))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "gang_data.json")

def get_local_ip() -> str:
    return "127.0.0.1"

def load_gang_data():
    if not os.path.exists(DATA_FILE):
        default_data = {
            "gang_name": "SPONGEBOB",
            "gang_tag": "577",
            "slogan": "NEW GEN",
            "announcement": "ยินดีต้อนรับสู่เว็ปรายชื่อแก๊ง SPONGEBOB [577] อย่างเป็นทางการ",
            "logo_url": "https://cdn.discordapp.com/embed/avatars/0.png",
            "banner_url": "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?w=1600&auto=format&fit=crop&q=80",
            "theme_color": "#e11d48",
            "song_url": "https://www.youtube.com/watch?v=tQz93eTCpSA",
            "song_title": "Lana Del Rey - Cinnamon Girl",
            "song_autoplay": True,
            "passcode": "gang123",
            "roles": [
                {"name": "👑 หัวหน้าแก๊ง (Leader)", "color": "#f59e0b", "priority": 1},
                {"name": "⚔️ รองหัวหน้า (Co-Leader)", "color": "#ef4444", "priority": 2},
                {"name": "🛡️ เสนาธิการ (Officer)", "color": "#a855f7", "priority": 3},
                {"name": "🔫 มือปืนประจำแก๊ง (Shooter)", "color": "#3b82f6", "priority": 4},
                {"name": "🚗 พลขับ / จัดการยานพาหนะ (Driver)", "color": "#10b981", "priority": 5},
                {"name": "🔰 สมาชิกทดลองงาน (Trainee)", "color": "#64748b", "priority": 6}
            ],
            "members": [
                {
                    "id": "1",
                    "name": "SPONGEBOB Leader",
                    "nickname": "บอส",
                    "rank": "👑 หัวหน้าแก๊ง (Leader)",
                    "phone": "577-999-9999",
                    "discord_id": "1499880829055144107",
                    "avatar": "https://cdn.discordapp.com/embed/avatars/0.png",
                    "role_desc": "ผู้บัญชาการสูงสุด SPONGEBOB 577",
                    "status": "online",
                    "joined_date": "2026-01-01",
                    "weapon": "Heavy Rifle"
                }
            ]
        }
        save_gang_data(default_data)
        return default_data
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[!] Error loading {DATA_FILE}: {e}")
        return {}

def save_gang_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[!] Error saving {DATA_FILE}: {e}")

ATTENDANCE_FILE = os.path.join(BASE_DIR, "attendance_logs.json")

def load_attendance_logs():
    if not os.path.exists(ATTENDANCE_FILE):
        return []
    try:
        with open(ATTENDANCE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[!] Error loading {ATTENDANCE_FILE}: {e}")
        return []

def save_attendance_logs(logs):
    try:
        with open(ATTENDANCE_FILE, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[!] Error saving {ATTENDANCE_FILE}: {e}")

# ==============================================================================
# 🍪 VISITOR COOKIE STORE & NOCAPTCHA VERIFICATION
# ==============================================================================
VISITOR_COOKIES_FILE = os.path.join(BASE_DIR, "visitor_cookies.json")
VISITOR_LOCK = threading.Lock()

def load_visitor_cookies():
    if not os.path.exists(VISITOR_COOKIES_FILE):
        return {}
    try:
        with open(VISITOR_COOKIES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[!] Error loading {VISITOR_COOKIES_FILE}: {e}")
        return {}

def save_visitor_cookies(data):
    with VISITOR_LOCK:
        try:
            with open(VISITOR_COOKIES_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[!] Error saving {VISITOR_COOKIES_FILE}: {e}")

def track_and_get_visitor(handler):
    raw_cookie = handler.headers.get("Cookie", "")
    cookie = http.cookies.SimpleCookie()
    if raw_cookie:
        try:
            cookie.load(raw_cookie)
        except Exception:
            pass

    visitor_id = None
    is_new = False
    if "gang_visitor_id" in cookie:
        visitor_id = cookie["gang_visitor_id"].value

    if not visitor_id or len(visitor_id) < 8:
        visitor_id = f"vis_{uuid.uuid4().hex[:16]}"
        is_new = True

    is_verified = False
    if "gang_human_verified" in cookie and cookie["gang_human_verified"].value == "1":
        is_verified = True

    visitor_name = ""
    visitor_email = ""
    if "gang_visitor_name" in cookie:
        try:
            visitor_name = urllib.parse.unquote(cookie["gang_visitor_name"].value).strip()
        except Exception:
            pass
    if "gang_visitor_email" in cookie:
        try:
            visitor_email = urllib.parse.unquote(cookie["gang_visitor_email"].value).strip()
        except Exception:
            pass

    has_valid_account = bool(visitor_email and "@" in visitor_email and visitor_name and visitor_name != "รอยืนยันตัวตน")
    is_verified = bool(is_verified and has_valid_account)

    visitors = load_visitor_cookies()
    user_agent = handler.headers.get("User-Agent", "Unknown")
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if visitor_id not in visitors:
        visitors[visitor_id] = {
            "visitor_id": visitor_id,
            "name": visitor_name or "รอยืนยันตัวตน",
            "email": visitor_email or "-",
            "user_agent": user_agent,
            "verified_human": is_verified,
            "first_seen": now_str,
            "last_seen": now_str,
            "visit_count": 1
        }
    else:
        visitors[visitor_id]["last_seen"] = now_str
        visitors[visitor_id]["visit_count"] = visitors[visitor_id].get("visit_count", 1) + 1
        visitors[visitor_id]["user_agent"] = user_agent
        if visitor_name:
            visitors[visitor_id]["name"] = visitor_name
        if visitor_email:
            visitors[visitor_id]["email"] = visitor_email
        visitors[visitor_id]["verified_human"] = is_verified

    save_visitor_cookies(visitors)
    return visitor_id, is_new, is_verified

def trigger_discord_webhook(title, description, fields=None, color=0xe11d48):
    try:
        gdata = load_gang_data()
        webhook_url = gdata.get("discord_webhook") or os.environ.get("DISCORD_WEBHOOK_URL")
        if not webhook_url or not str(webhook_url).startswith("http"):
            return
        payload = {
            "embeds": [
                {
                    "title": title,
                    "description": description,
                    "color": color,
                    "fields": fields or [],
                    "footer": {"text": "SPONGEBOB 577 • Attendance Log"},
                    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
                }
            ]
        }
        req = urllib.request.Request(
            webhook_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
        )
        urllib.request.urlopen(req, timeout=4)
    except Exception as e:
        print(f"[!] Discord webhook delivery failed: {e}")

DISCORD_CACHE = {}

def format_discord_user(data):
    uid = str(data.get("id"))
    username = data.get("username", "")
    global_name = data.get("global_name") or username
    avatar_hash = data.get("avatar")

    if avatar_hash:
        ext = "gif" if avatar_hash.startswith("a_") else "png"
        avatar_url = f"https://cdn.discordapp.com/avatars/{uid}/{avatar_hash}.{ext}?size=512"
    else:
        try:
            idx = (int(uid) >> 22) % 6
        except Exception:
            idx = 0
        avatar_url = f"https://cdn.discordapp.com/embed/avatars/{idx}.png"

    return {
        "id": uid,
        "username": username,
        "global_name": global_name,
        "display_name": global_name or username,
        "avatar": avatar_url
    }

def fetch_discord_user(user_id, bot_token=None):
    user_id = str(user_id).strip()
    if not user_id.isdigit():
        return {"success": False, "error": "Discord ID ต้องประกอบด้วยตัวเลขเท่านั้น"}

    if user_id in DISCORD_CACHE:
        return {"success": True, "cached": True, **DISCORD_CACHE[user_id]}

    # Check bot token from gang_data or environment
    if not bot_token:
        try:
            gdata = load_gang_data()
            bot_token = gdata.get("discord_bot_token") or os.environ.get("DISCORD_BOT_TOKEN")
        except Exception:
            pass

    # 1. Try Discord Official API if bot token available
    if bot_token:
        try:
            req = urllib.request.Request(
                f"https://discord.com/api/v10/users/{user_id}",
                headers={"Authorization": f"Bot {bot_token}", "User-Agent": "GangRoster/1.0"}
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                d = json.loads(resp.read().decode("utf-8"))
                res = format_discord_user(d)
                DISCORD_CACHE[user_id] = res
                return {"success": True, **res}
        except Exception as e:
            print(f"[!] Official Bot API lookup failed for {user_id}: {e}")

    # 2. Try japi.rest free proxy
    try:
        req = urllib.request.Request(
            f"https://japi.rest/discord/v1/user/{user_id}",
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if "data" in data and "id" in data["data"]:
                res = format_discord_user(data["data"])
                DISCORD_CACHE[user_id] = res
                return {"success": True, **res}
            elif "data" in data and "message" in data["data"]:
                return {"success": False, "error": f"ไม่พบข้อมูลผู้ใช้ใน Discord ({data['data']['message']})"}
    except Exception as e:
        print(f"[!] japi lookup failed for {user_id}: {e}")

    return {"success": False, "error": "ไม่สามารถดึงข้อมูล Discord ได้ กรุณาตรวจสอบ Discord ID หรือลองใหม่อีกครั้ง"}

# ==============================================================================
# 🛡️ ANTI-DDOS, ANTI-BOT & RATE LIMITING SHIELD
# ==============================================================================
class SecurityShield:
    def __init__(self):
        self.lock = threading.Lock()
        self.requests = defaultdict(list)
        self.auth_requests = defaultdict(list)
        self.banned_ips = {}
        
        # Configuration Thresholds
        self.WINDOW_SECONDS = 5
        self.MAX_PAGE_REQS = 50        # Max 50 reqs / 5s for normal page / static asset loading
        self.MAX_API_REQS = 20         # Max 20 reqs / 5s for API endpoints
        self.MAX_AUTH_REQS = 6         # Max 6 auth reqs / 10s (prevents brute force)
        self.BAN_FLOOD_THRESHOLD = 85  # Over 85 reqs in 5s triggers 3-minute temporary jail
        self.BAN_DURATION = 180        # 180 seconds ban

        # Malicious Attack Scanner / Bot User-Agents
        self.MALICIOUS_UA = [
            "sqlmap", "nikto", "masscan", "nmap", "gobuster", 
            "dirbuster", "wpscan", "havij", "zgrab", "attack"
        ]

        # Whitelisted Social / Search Crawlers (Never blocked so embeds always work)
        self.WHITELISTED_CRAWLERS = [
            "discordbot", "facebookexternalhit", "twitterbot",
            "googlebot", "bingbot", "slackbot", "line"
        ]

    def get_real_ip(self, handler) -> str:
        # 1. Cloudflare Client IP (Highest priority when proxied through Cloudflare)
        cf_ip = handler.headers.get("CF-Connecting-IP")
        if cf_ip and cf_ip.strip():
            return cf_ip.strip()
        # 2. X-Forwarded-For (Render / Proxy)
        xff = handler.headers.get("X-Forwarded-For")
        if xff and xff.strip():
            return xff.split(",")[0].strip()
        # 3. Direct socket IP
        try:
            return handler.client_address[0]
        except Exception:
            return "127.0.0.1"

    def is_crawler(self, user_agent: str) -> bool:
        ua = (user_agent or "").lower()
        return any(c in ua for c in self.WHITELISTED_CRAWLERS)

    def is_malicious(self, user_agent: str) -> bool:
        ua = (user_agent or "").lower()
        return any(m in ua for m in self.MALICIOUS_UA)

    def verify(self, handler, is_api=False, is_auth=False):
        ua = handler.headers.get("User-Agent", "")
        # Social crawlers bypass limits so link preview cards in Discord always render
        if self.is_crawler(ua):
            return True, 200, None, 0

        # Block known vulnerability scanners & flood tools immediately
        if self.is_malicious(ua):
            return False, 403, "Forbidden: Security policy violation (Blocked Bot)", 0

        ip = self.get_real_ip(handler)
        now = time.time()

        with self.lock:
            # 1. Check if IP is currently banned/jailed
            ban_until = self.banned_ips.get(ip, 0)
            if now < ban_until:
                remaining = max(1, int(ban_until - now))
                return False, 429, f"🚨 IP ของคุณถูกระงับชั่วคราวเนื่องจากตรวจพบการโจมตีหรือส่งคำขอถี่เกินไป (เหลือ {remaining} วิ)", remaining
            elif ip in self.banned_ips:
                del self.banned_ips[ip]

            # 2. General request tracking
            cutoff = now - self.WINDOW_SECONDS
            self.requests[ip] = [t for t in self.requests[ip] if t > cutoff]
            self.requests[ip].append(now)
            req_count = len(self.requests[ip])

            # 3. Check for massive flood -> Auto-Jail for 3 minutes
            if req_count > self.BAN_FLOOD_THRESHOLD:
                self.banned_ips[ip] = now + self.BAN_DURATION
                print(f"[SECURITY SHIELD] 🚨 IP {ip} BANNED for {self.BAN_DURATION}s (Sent {req_count} reqs in {self.WINDOW_SECONDS}s)", flush=True)
                return False, 429, "🚨 ตรวจพบพฤติกรรมโจมตีระบบ (HTTP Flood Attack) IP ถูกบล็อกชั่วคราว 3 นาที", self.BAN_DURATION

            # 4. Check normal rate limit
            limit = self.MAX_API_REQS if is_api else self.MAX_PAGE_REQS
            if req_count > limit:
                return False, 429, "⚠️ ส่งคำขอถี่เกินไป กรุณารอสักครู่ (Rate Limited)", 5

            # 5. Check auth rate limit (anti-brute force)
            if is_auth:
                auth_cutoff = now - 10
                self.auth_requests[ip] = [t for t in self.auth_requests[ip] if t > auth_cutoff]
                self.auth_requests[ip].append(now)
                if len(self.auth_requests[ip]) > self.MAX_AUTH_REQS:
                    return False, 429, "⚠️ ป้อนรหัสผ่านถี่เกินไป กรุณารอ 15 วินาที", 15

        return True, 200, None, 0

shield = SecurityShield()

class GangRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.new_visitor_cookie = None
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def end_headers(self):
        if hasattr(self, "new_visitor_cookie") and self.new_visitor_cookie:
            self.send_header("Set-Cookie", self.new_visitor_cookie)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("X-XSS-Protection", "1; mode=block")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_HEAD(self):
        vis_id, is_new, is_ver = track_and_get_visitor(self)
        if is_new:
            self.new_visitor_cookie = f"gang_visitor_id={vis_id}; Path=/; Max-Age=31536000; SameSite=Lax"
        allowed, status, err_msg, retry = shield.verify(self, is_api=False, is_auth=False)
        if not allowed:
            self.send_response(status)
            self.send_header("Retry-After", str(retry))
            self.end_headers()
            return
        return super().do_HEAD()

    def send_shield_page(self, retry_seconds, msg):
        self.send_response(429)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Retry-After", str(retry_seconds))
        self.end_headers()
        html = f"""<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>429 • SPONGEBOB SHIELD ACTIVE</title>
  <link rel="icon" type="image/x-icon" href="/favicon.ico">
  <style>
    body {{ background: #060709; color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Kanit", sans-serif; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; padding: 20px; box-sizing: border-box; text-align: center; }}
    .shield-card {{ background: rgba(15, 18, 26, 0.96); border: 1.5px solid rgba(225, 29, 72, 0.5); box-shadow: 0 0 50px rgba(225, 29, 72, 0.25), 0 20px 60px rgba(0, 0, 0, 0.95); border-radius: 18px; max-width: 500px; padding: 42px 32px; animation: shieldPulse 2s infinite alternate; }}
    @keyframes shieldPulse {{ from {{ box-shadow: 0 0 30px rgba(225, 29, 72, 0.2); }} to {{ box-shadow: 0 0 60px rgba(225, 29, 72, 0.45); }} }}
    .icon {{ font-size: 58px; margin-bottom: 16px; filter: drop-shadow(0 0 20px rgba(225, 29, 72, 0.6)); }}
    h1 {{ font-size: 1.6rem; color: #ff3b68; margin-bottom: 12px; letter-spacing: 1px; font-weight: 800; }}
    p {{ color: #94a3b8; font-size: 0.95rem; line-height: 1.6; margin-bottom: 24px; }}
    .countdown-box {{ font-size: 2.2rem; font-weight: 900; color: #f59e0b; margin-bottom: 20px; font-family: monospace; background: rgba(0,0,0,0.6); padding: 14px; border-radius: 12px; border: 1px solid rgba(245, 158, 11, 0.35); }}
    .brand {{ font-size: 0.8rem; color: #64748b; letter-spacing: 2px; text-transform: uppercase; }}
  </style>
</head>
<body>
  <div class="shield-card">
    <div class="icon">🛡️</div>
    <h1>ANTI-DDOS & BOT SHIELD</h1>
    <p>{msg}</p>
    <div class="countdown-box" id="timer">{retry_seconds}s</div>
    <div class="brand">SPONGEBOB 577 • SECURITY SYSTEM</div>
  </div>
  <script>
    let sec = {retry_seconds};
    const t = document.getElementById("timer");
    const iv = setInterval(() => {{
      sec--;
      if (sec <= 0) {{
        clearInterval(iv);
        window.location.reload();
      }} else {{
        t.innerText = sec + "s";
      }}
    }}, 1000);
  </script>
</body>
</html>"""
        self.wfile.write(html.encode("utf-8"))

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        clean_path = parsed.path.rstrip("/")
        is_api = clean_path.startswith("/api/")

        # Track visitor cookie and persistence
        vis_id, is_new, is_ver = track_and_get_visitor(self)
        if is_new:
            self.new_visitor_cookie = f"gang_visitor_id={vis_id}; Path=/; Max-Age=31536000; SameSite=Lax"

        # Security & Rate Limiting Check
        allowed, status, err_msg, retry = shield.verify(self, is_api=is_api, is_auth=False)
        if not allowed:
            if is_api:
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Retry-After", str(retry))
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": err_msg, "retry_after": retry}, ensure_ascii=False).encode("utf-8"))
                return
            else:
                self.send_shield_page(retry, err_msg)
                return

        if clean_path in ["/reset-captcha", "/test-captcha"]:
            self.send_response(302)
            self.send_header("Set-Cookie", "gang_human_verified=; Path=/; Max-Age=0")
            self.send_header("Location", "/verify.html")
            self.end_headers()
            return

        # Standalone NoCAPTCHA verification page route
        if clean_path in ["/verify", "/verify.html"]:
            try:
                verify_path = os.path.join(BASE_DIR, "verify.html")
                with open(verify_path, "r", encoding="utf-8") as f:
                    v_html = f.read()
                content = v_html.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return
            except Exception as e:
                print(f"[!] Error serving verify.html: {e}")
                self.path = "/verify.html"
                return super().do_GET()

        if clean_path in ["", "/gang", "/index.html"]:
            # If not a crawler and not yet verified by NoCAPTCHA, redirect to /verify.html
            ua = self.headers.get("User-Agent", "")
            if not shield.is_crawler(ua):
                if not is_ver:
                    self.send_response(302)
                    self.send_header("Location", "/verify.html")
                    self.end_headers()
                    return

            try:
                html_path = os.path.join(BASE_DIR, "index.html")
                with open(html_path, "r", encoding="utf-8") as f:
                    html = f.read()

                # Determine host and protocol for crawler-compatible absolute URLs
                host = self.headers.get("Host") or f"localhost:{PORT}"
                proto = self.headers.get("X-Forwarded-Proto") or ("https" if "onrender.com" in host or "herokuapp.com" in host else "http")
                base_url = f"{proto}://{host}"

                gdata = load_gang_data()
                gname = gdata.get("gang_name", "SPONGEBOB")
                gtag = gdata.get("gang_tag", "577")
                gslogan = gdata.get("slogan", "NEW GEN")
                
                banner_url = gdata.get("banner_url", "/gang_banner.jpg")
                if not banner_url.startswith("http://") and not banner_url.startswith("https://"):
                    if not banner_url.startswith("/"):
                        banner_url = "/" + banner_url
                    banner_url = f"{base_url}{banner_url}"

                tag_display = f" [{gtag}]" if (gtag and gtag.strip() and gtag.strip() != ".") else ""
                og_title = f"{gname}{tag_display} • GANG ROSTER"
                og_desc = "LIST SPONGEBOB NEWGEN"

                html = html.replace("__BASE_URL__", base_url)
                html = html.replace("__OG_IMAGE__", banner_url)
                html = html.replace("__OG_TITLE__", og_title)
                html = html.replace("__OG_DESC__", og_desc)

                content = html.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return
            except Exception as e:
                print(f"[!] Error serving dynamic index.html: {e}")
                self.path = "/index.html"
                return super().do_GET()
        elif clean_path in ["/admin", "/manage", "/dashboard"]:
            self.path = "/admin.html"
            return super().do_GET()
        
        elif clean_path == "/api/gang/data":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            data = load_gang_data()
            sanitized = dict(data)
            sanitized.pop("passcode", None)
            self.wfile.write(json.dumps({"success": True, "data": sanitized}, ensure_ascii=False).encode("utf-8"))
            return

        elif clean_path == "/api/discord/user":
            query = urllib.parse.parse_qs(parsed.query)
            user_id = query.get("id", [""])[0].strip()
            if not user_id:
                self.send_json_response(400, {"success": False, "error": "กรุณาระบุ Discord ID ในพารามิเตอร์ ?id="})
                return
            res = fetch_discord_user(user_id)
            code = 200 if res.get("success") else 400
            self.send_json_response(code, res)
            return

        elif clean_path == "/api/gang/attendance":
            self.send_json_response(200, {
                "success": True,
                "logs": load_attendance_logs()
            })
            return

        elif clean_path == "/api/admin/visitors":
            query = urllib.parse.parse_qs(parsed.query)
            passcode = query.get("passcode", [""])[0].strip()
            data = load_gang_data()
            if not passcode or passcode != data.get("passcode", "gang123"):
                self.send_json_response(401, {"success": False, "error": "รหัสผ่านไม่ถูกต้อง ไม่มีสิทธิ์เข้าถึงข้อมูล Cookies"})
                return
            visitors = load_visitor_cookies()
            
            v_list = sorted(list(visitors.values()), key=lambda x: x.get("last_seen", ""), reverse=True)
            self.send_json_response(200, {
                "success": True,
                "total_visitors": len(visitors),
                "verified_humans": sum(1 for v in visitors.values() if v.get("verified_human") and v.get("email") and v.get("email") != "-" and v.get("name") and v.get("name") != "รอยืนยันตัวตน"),
                "visitors": v_list
            })
            return

        elif clean_path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
            return

        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        clean_path = parsed.path.rstrip("/")
        is_auth = clean_path in ["/api/gang/auth", "/api/gang/change_pass"]

        # Security & Rate Limiting Check for POST requests
        allowed, status, err_msg, retry = shield.verify(self, is_api=True, is_auth=is_auth)
        if not allowed:
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Retry-After", str(retry))
            self.end_headers()
            self.wfile.write(json.dumps({"success": False, "error": err_msg, "retry_after": retry}, ensure_ascii=False).encode("utf-8"))
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_length) if content_length > 0 else b""
        try:
            body = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
        except Exception:
            body = {}

        if clean_path == "/api/security/verify_human":
            telemetry = body.get("telemetry", {})
            name = str(body.get("name", "")).strip()
            email = str(body.get("email", body.get("gmail", ""))).strip()

            if not name:
                self.send_json_response(400, {"success": False, "error": "กรุณากรอกชื่อของคุณเพื่อยืนยันตัวตน"})
                return
            if not email or "@" not in email:
                self.send_json_response(400, {"success": False, "error": "กรุณากรอกบัญชี Gmail / อีเมลให้ถูกต้อง"})
                return

            is_webdriver = telemetry.get("webdriver", False)
            if is_webdriver:
                self.send_json_response(403, {"success": False, "error": "ตรวจพบบอทอัตโนมัติ (Automated Bot Blocked)"})
                return

            raw_cookie = self.headers.get("Cookie", "")
            cookie = http.cookies.SimpleCookie()
            if raw_cookie:
                try: cookie.load(raw_cookie)
                except Exception: pass

            vis_id = cookie["gang_visitor_id"].value if "gang_visitor_id" in cookie else f"vis_{uuid.uuid4().hex[:16]}"

            visitors = load_visitor_cookies()
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if vis_id in visitors:
                visitors[vis_id]["name"] = name
                visitors[vis_id]["email"] = email
                visitors[vis_id]["verified_human"] = True
                visitors[vis_id]["last_seen"] = now_str
                if telemetry.get("screen"):
                    visitors[vis_id]["screen"] = telemetry.get("screen")
                if telemetry.get("language"):
                    visitors[vis_id]["language"] = telemetry.get("language")
            else:
                visitors[vis_id] = {
                    "visitor_id": vis_id,
                    "name": name,
                    "email": email,
                    "screen": telemetry.get("screen"),
                    "language": telemetry.get("language"),
                    "user_agent": self.headers.get("User-Agent", "Unknown"),
                    "verified_human": True,
                    "first_seen": now_str,
                    "last_seen": now_str,
                    "visit_count": 1
                }
            save_visitor_cookies(visitors)

            encoded_name = urllib.parse.quote(name)
            encoded_email = urllib.parse.quote(email)

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Set-Cookie", f"gang_visitor_id={vis_id}; Path=/; Max-Age=31536000; SameSite=Lax")
            self.send_header("Set-Cookie", "gang_human_verified=1; Path=/; Max-Age=604800; SameSite=Lax")
            self.send_header("Set-Cookie", f"gang_visitor_name={encoded_name}; Path=/; Max-Age=31536000; SameSite=Lax")
            self.send_header("Set-Cookie", f"gang_visitor_email={encoded_email}; Path=/; Max-Age=31536000; SameSite=Lax")
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True, 
                "message": f"ยืนยันตัวตนสำเร็จ ยินดีต้อนรับ {name} ({email})", 
                "name": name,
                "email": email,
                "visitor_id": vis_id
            }, ensure_ascii=False).encode("utf-8"))
            return

        elif clean_path == "/api/gang/auth":
            input_pass = str(body.get("passcode", "")).strip()
            data = load_gang_data()
            correct_pass = str(data.get("passcode", "gang123")).strip()
            if input_pass and input_pass == correct_pass:
                self.send_json_response(200, {"success": True, "is_admin": True, "message": "ยืนยันสิทธิ์ Admin สูงสุดเรียบร้อย"})
            else:
                self.send_json_response(401, {"success": False, "error": "รหัสผ่าน Admin ไม่ถูกต้อง คุณไม่มีสิทธิ์เข้าถึงระบบนี้"})
            return

        elif clean_path == "/api/gang/update":
            input_pass = str(body.get("passcode", "")).strip()
            data = load_gang_data()
            correct_pass = str(data.get("passcode", "gang123")).strip()
            
            if not input_pass or input_pass != correct_pass:
                self.send_json_response(401, {"success": False, "error": "รหัสผ่านไม่ถูกต้อง คุณไม่มีสิทธิ์แก้ไขข้อมูล"})
                return

            updated_data = body.get("gang_data", {})
            if "passcode" not in updated_data or not updated_data["passcode"]:
                updated_data["passcode"] = correct_pass

            save_gang_data(updated_data)
            self.send_json_response(200, {"success": True, "message": "บันทึกข้อมูลทำเนียบแก๊งเรียบร้อยแล้ว!"})
            return

        elif clean_path == "/api/gang/change_pass":
            old_pass = str(body.get("old_passcode", "")).strip()
            new_pass = str(body.get("new_passcode", "")).strip()
            data = load_gang_data()
            correct_pass = str(data.get("passcode", "gang123")).strip()

            if not old_pass or old_pass != correct_pass:
                self.send_json_response(401, {"success": False, "error": "รหัสผ่านเดิมไม่ถูกต้อง"})
                return

            if not new_pass or len(new_pass) < 3:
                self.send_json_response(400, {"success": False, "error": "รหัสผ่านใหม่ต้องมีความยาวอย่างน้อย 3 ตัวอักษร"})
                return

            data["passcode"] = new_pass
            save_gang_data(data)
            self.send_json_response(200, {"success": True, "message": "เปลี่ยนรหัสผ่านสำหรับปรับแต่งข้อมูลสำเร็จเรียบร้อย!"})
            return

        elif clean_path == "/api/gang/attendance/checkin":
            mode = body.get("type", "single")
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logs = load_attendance_logs()

            if mode == "batch":
                event_name = body.get("event_type", "รวมพลแก๊ง").strip()
                checked_by = body.get("checked_by", "หัวหน้าแก๊ง").strip()
                records = body.get("records", [])
                added_count = 0
                for r in records:
                    log_item = {
                        "id": f"att_{int(time.time() * 1000)}_{added_count}",
                        "timestamp": now_str,
                        "member_id": str(r.get("member_id", "")),
                        "member_name": str(r.get("member_name", "")),
                        "nickname": str(r.get("nickname", "")),
                        "rank": str(r.get("rank", "")),
                        "event_type": event_name,
                        "status": str(r.get("status", "present")),
                        "note": str(r.get("note", "")),
                        "checked_by": checked_by
                    }
                    logs.insert(0, log_item)
                    added_count += 1
                
                logs = logs[:500]
                save_attendance_logs(logs)

                present_count = sum(1 for r in records if r.get("status") == "present")
                late_count = sum(1 for r in records if r.get("status") == "late")
                leave_count = sum(1 for r in records if r.get("status") == "leave")
                absent_count = sum(1 for r in records if r.get("status") == "absent")

                trigger_discord_webhook(
                    title=f"📋 บันทึกการรวมพล: {event_name}",
                    description=f"ผู้บันทึก: **{checked_by}** | วันที่: `{now_str}`",
                    fields=[
                        {"name": "🟢 มาตรงเวลา", "value": f"{present_count} คน", "inline": True},
                        {"name": "🟡 มาสาย", "value": f"{late_count} คน", "inline": True},
                        {"name": "🔵 ลา", "value": f"{leave_count} คน", "inline": True},
                        {"name": "🔴 ขาด", "value": f"{absent_count} คน", "inline": True}
                    ],
                    color=0x22c55e if present_count >= absent_count else 0xef4444
                )

                self.send_json_response(200, {
                    "success": True,
                    "message": f"บันทึกประวัติการรวมพลสำเร็จ ({added_count} รายการ)",
                    "logs": logs
                })
                return

            else:
                member_name = body.get("member_name", "").strip()
                nickname = body.get("nickname", "").strip()
                rank = body.get("rank", "").strip()
                event_name = body.get("event_type", "เข้าเวร / รวมพลทั่วไป").strip()
                status = body.get("status", "present").strip()
                note = body.get("note", "").strip()
                checked_by = member_name or nickname or "สมาชิกแก๊ง"

                if not member_name and not nickname:
                    self.send_json_response(400, {"success": False, "error": "กรุณาเลือกสมาชิกหรือระบุชื่อ"})
                    return

                log_item = {
                    "id": f"att_{int(time.time() * 1000)}",
                    "timestamp": now_str,
                    "member_id": str(body.get("member_id", "")),
                    "member_name": member_name,
                    "nickname": nickname,
                    "rank": rank,
                    "event_type": event_name,
                    "status": status,
                    "note": note,
                    "checked_by": checked_by
                }
                logs.insert(0, log_item)
                logs = logs[:500]
                save_attendance_logs(logs)

                status_map = {
                    "present": "🟢 มาตรงเวลา",
                    "late": "🟡 มาสาย",
                    "leave": "🔵 ลาภารกิจ",
                    "absent": "🔴 ขาด"
                }

                trigger_discord_webhook(
                    title=f"✅ สมาชิกเช็คชื่อ: {nickname or member_name}",
                    description=f"ยศ: `{rank}` | กิจกรรม: **{event_name}**",
                    fields=[
                        {"name": "สถานะ", "value": status_map.get(status, status), "inline": True},
                        {"name": "เวลา", "value": f"`{now_str}`", "inline": True},
                        {"name": "หมายเหตุ", "value": note or "-", "inline": False}
                    ],
                    color=0x22c55e if status == "present" else 0xf59e0b
                )

                self.send_json_response(200, {
                    "success": True,
                    "message": f"เช็คชื่อสำเร็จ: {nickname or member_name} ({event_name})",
                    "log": log_item,
                    "logs": logs
                })
                return

        elif clean_path == "/api/gang/attendance/delete":
            input_pass = str(body.get("passcode", "")).strip()
            data = load_gang_data()
            correct_pass = str(data.get("passcode", "gang123")).strip()
            if not input_pass or input_pass != correct_pass:
                self.send_json_response(401, {"success": False, "error": "เฉพาะ Admin สูงสุดเท่านั้นที่มีสิทธิ์ลบประวัติ Log"})
                return

            log_id = body.get("log_id", "")
            logs = load_attendance_logs()
            if log_id == "all":
                logs = []
                save_attendance_logs(logs)
                self.send_json_response(200, {"success": True, "message": "ล้างประวัติ Log ทั้งหมดเรียบร้อยแล้ว", "logs": []})
                return
            elif log_id:
                logs = [l for l in logs if l.get("id") != log_id]
                save_attendance_logs(logs)
                self.send_json_response(200, {"success": True, "message": "ลบรายการ Log เรียบร้อยแล้ว", "logs": logs})
                return

            self.send_json_response(400, {"success": False, "error": "ไม่พบ Log ID"})
            return

        self.send_json_response(404, {"success": False, "error": "Endpoint not found"})

    def send_json_response(self, code, payload):
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))

    def log_message(self, format, *args):
        # Clean logging format
        print(f"[{self.log_date_time_string()}] {self.address_string()} - {format % args}")

if __name__ == "__main__":
    load_gang_data()
    server_address = ("0.0.0.0", PORT)
    httpd = ThreadingHTTPServer(server_address, GangRequestHandler)
    print("=" * 60, flush=True)
    print(f"🚀 GANG ROSTER WEB SERVER ONLINE ON PORT {PORT}", flush=True)
    print("=" * 60, flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Server stopped", flush=True)
        httpd.server_close()
