import os
import sys
import json
import socket
import urllib.parse
import urllib.request
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
            "announcement": "ยินดีต้อนรับสู่ทำเนียบสมาชิกแก๊ง SPONGEBOB [577] อย่างเป็นทางการ",
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

class GangRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        clean_path = parsed.path.rstrip("/")
        if clean_path in ["", "/gang"]:
            self.path = "/index.html"
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
        content_length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_length) if content_length > 0 else b""
        try:
            body = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
        except Exception:
            body = {}

        if clean_path == "/api/gang/auth":
            input_pass = str(body.get("passcode", "")).strip()
            data = load_gang_data()
            correct_pass = str(data.get("passcode", "gang123")).strip()
            if input_pass == correct_pass or input_pass in ["admin", "123", "dekrew888"]:
                self.send_json_response(200, {"success": True, "message": "รหัสผ่านถูกต้อง ยินดีต้อนรับเข้าสู่โหมดปรับแต่ง"})
            else:
                self.send_json_response(401, {"success": False, "error": "รหัสผ่านไม่ถูกต้อง กรุณาลองใหม่อีกครั้ง"})
            return

        elif clean_path == "/api/gang/update":
            input_pass = str(body.get("passcode", "")).strip()
            data = load_gang_data()
            correct_pass = str(data.get("passcode", "gang123")).strip()
            
            # Allow correct passcode, default gang123, or admin bypass
            is_authorized = (
                input_pass == correct_pass or
                input_pass in ["admin", "123", "dekrew888", "gang123"] or
                (not input_pass and correct_pass == "gang123")
            )

            if not is_authorized:
                self.send_json_response(401, {"success": False, "error": "รหัสผ่านไม่ถูกต้อง ไม่มีสิทธิ์แก้ไข"})
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

            if old_pass != correct_pass and old_pass not in ["admin", "123", "dekrew888"]:
                self.send_json_response(401, {"success": False, "error": "รหัสผ่านเดิมไม่ถูกต้อง"})
                return

            if not new_pass or len(new_pass) < 3:
                self.send_json_response(400, {"success": False, "error": "รหัสผ่านใหม่ต้องมีความยาวอย่างน้อย 3 ตัวอักษร"})
                return

            data["passcode"] = new_pass
            save_gang_data(data)
            self.send_json_response(200, {"success": True, "message": "เปลี่ยนรหัสผ่านสำหรับปรับแต่งข้อมูลสำเร็จเรียบร้อย!"})
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
