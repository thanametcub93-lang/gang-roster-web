import os
import sys
import json
import socket
import urllib.parse
import urllib.request
import datetime
import time
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
        if clean_path in ["", "/gang", "/index.html"]:
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
