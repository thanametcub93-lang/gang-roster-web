# ⚔️ Gang Roster Web (เว็บทำเนียบรายชื่อแก๊งแยกอิสระ)

โปรเจกต์เว็บทำเนียบรายชื่อแก๊งแบบ **Standalone (แยกเป็นอิสระ 100%)** ไม่ขึ้นกับบอท Discord ใดๆ ทั้งสิ้น พร้อมระบบใส่รหัสผ่านเพื่อปรับแต่ง/เพิ่ม/ลบ/จัดอันดับสมาชิกแก๊ง

---

## 🚀 วิธีเปิดใช้งาน

### 1. เปิดรันในเครื่อง (Local)
- ดับเบิ้ลคลิกไฟล์ `run.bat` หรือรันคำสั่ง:
  ```bash
  python server.py
  ```
- เปิดเบราว์เซอร์เข้าไปที่: `http://localhost:8080`

### 2. นำขึ้นโฮสติ้ง / คลาวด์ (Render / Railway / VPS)
- ตัวเว็บใช้ **Pure Python Standard Library** ไม่มี dependencies ภายนอก ไม่ต้อง `pip install` ใดๆ ทั้งสิ้น
- สามารถ Deploy บน Render (สร้างเป็น New Web Service -> เชื่อม GitHub หรือใช้ `Procfile` / Start command `python server.py`)
- ผูก Custom Domain ของคุณ เช่น `gang.dekrew.online` หรือ `dekrew.online` ได้ตามต้องการ

---

## 🔐 ข้อมูลรหัสผ่านผู้ดูแล (Editor Passcode)
- **รหัสผ่านเริ่มต้น:** `gang123`
- สามารถกดปุ่ม **"ใส่รหัสปรับแต่ง"** ที่มุมขวาบน เพื่อปลดล็อคแถบเครื่องมือ
- ปรับแต่ง/เพิ่ม/ลบสมาชิก และเปลี่ยนรหัสผ่านใหม่ได้ที่เมนู **"ตั้งค่าแก๊ง & รหัส"**

---

## 📁 โครงสร้างไฟล์ในโปรเจกต์
- `server.py` - เว็บเซิร์ฟเวอร์ความเร็วสูง (Pure Python Built-in, รองรับ Multi-threading & JSON API)
- `index.html` - หน้าเว็บทำเนียบแก๊ง ดีไซน์ Cyberpunk / FiveM สุดพรีเมียม
- `gang_data.json` - ฐานข้อมูลสมาชิก ยศ สโลแกน และรหัสผ่าน
- `run.bat` - สคริปต์เปิดรันเซิร์ฟเวอร์ในคลิกเดียว
- `Procfile` - สำหรับการ Deploy ขึ้น Cloud Web Service
