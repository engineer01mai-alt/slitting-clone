# Slitting Inspection – เว็บจำลอง (Test Clone)

จำลองโครงสร้างหน้า "Search" และ "Data Entry" ของระบบ Slitting Inspection
ให้ใช้ **field id/name เดียวกับต้นฉบับทุกตัว** เพื่อให้โปรแกรม/สคริปต์
ที่คุณเขียนเชื่อมต่อ/ทดสอบกรอกข้อมูลได้เหมือนของจริง โดยใช้ฐานข้อมูล
SQLite (ไฟล์เดียว ไม่ต้องติดตั้ง DB server) และไม่มีระบบ login ให้ยุ่งยาก

⚠️ หมายเหตุ: ข้อความ footer/ชื่อบริษัทของต้นฉบับถูกเปลี่ยนเป็นข้อความกลางๆ
("Test Clone Environment") เพื่อไม่ให้ไปใช้ตราสินค้า/ข้อความของบริษัทอื่น
คุณสามารถแก้เป็นชื่อบริษัทของคุณเองได้ที่ `templates/base.html`

## โครงสร้างไฟล์
```
slitting-clone/
├── app.py              # Flask app (routes ทั้งหมด)
├── init_db.py           # สร้าง DB (SQLite) + seed ข้อมูลตัวอย่าง
├── slitting.db           # ไฟล์ฐานข้อมูล (สร้างอัตโนมัติ)
├── templates/
│   ├── base.html         # header/nav/sidebar/footer (เหมือนต้นฉบับ)
│   ├── search.html        # หน้า SlittingInspectionPage1A (Search)
│   └── entry.html         # หน้า SlittingInspectionPage2 (Data Entry)
├── static/style.css
├── selenium_test.py       # สคริปต์ Selenium เปิด Edge + กรอกข้อมูล
└── requirements.txt
```

## 1) รันเว็บบนเครื่องตัวเอง (สำหรับ dev/test)
```bash
cd slitting-clone
pip install -r requirements.txt
python init_db.py          # สร้าง/รีเซ็ต DB + ข้อมูลตัวอย่าง (รันครั้งแรกครั้งเดียว)
python app.py               # เปิดเว็บที่ http://127.0.0.1:5000
```
เปิดด้วย Edge: พิมพ์ `http://127.0.0.1:5000/Inspection/SlittingInspectionPage1A`

Route หลัก:
| Route | ทำหน้าที่ |
|---|---|
| `GET /Inspection/SlittingInspectionPage1A` | หน้าค้นหา/รายการใบงาน (ใส่ query string เพื่อ filter ได้) |
| `GET /Inspection/SlittingInspectionPage2?JobNo=xxx` | หน้ากรอกผลตรวจของใบงานนั้น |
| `POST /Inspection/SlittingInspectionPage2` | บันทึกค่าที่กรอก (ฟอร์ม submit ปุ่ม Submit) |
| `POST /Inspection/Result` | AJAX คืนสถานะสรุปผล (เหมือนต้นฉบับ) |
| `GET /api/jobs` , `GET /api/jobs/<job_no>` | **API แบบ JSON ตรงๆ** ให้โปรแกรมภายนอกอ่านข้อมูลได้ง่าย ไม่ต้อง parse HTML |
| `POST /api/jobs/<job_no>/pieces/<seq_no>` | **API แบบ JSON** ให้โปรแกรมของคุณส่งค่าที่วัดได้เข้ามาบันทึกตรงๆ (ไม่ต้องผ่านฟอร์ม/Selenium ก็ได้) |

ตัวอย่างยิง API ตรง (ไม่ผ่านเว็บ):
```bash
curl -X POST http://127.0.0.1:5000/api/jobs/S270655/pieces/2 \
  -H "Content-Type: application/json" \
  -d '{"top_thickness_actual": 1.936, "top_width_actual": 131.91, "appearance": "OK"}'
```

## 2) ทดสอบด้วย Selenium (เปิด Microsoft Edge อัตโนมัติ)
```bash
pip install selenium
python selenium_test.py --url http://127.0.0.1:5000 --job S270655
```
สคริปต์จะ: เปิด Edge → ไปหน้า Data Entry ของใบงาน S270655 → กรอกค่าตาม
field id เดิม (`TopThicknessActual_2`, `EndWidthActual_2`, `BurrActual_2`, ...)
→ กดปุ่ม Submit → อ่านค่าสถานะที่เปลี่ยนกลับมา

> Selenium เวอร์ชัน 4.6 ขึ้นไป จะดาวน์โหลด `msedgedriver` ให้อัตโนมัติ
> (ผ่าน Selenium Manager) แค่มี Microsoft Edge ติดตั้งอยู่ในเครื่องก็พอ

ถ้าจะเชื่อมกับ "โปรแกรมที่คุณเขียนขึ้นมา": แก้ dict `sample_measurements`
ใน `selenium_test.py` ให้รับค่าจากโปรแกรมของคุณ (เช่นอ่านจากไฟล์/queue/serial
ที่โปรแกรมส่งออกมา) แล้วป้อนเข้า `fill_and_submit()` แทนค่าตัวอย่าง

## 3) โฮสต์ขึ้นเป็นเว็บจริง (ได้ลิงก์สาธารณะ ส่งให้ลูกค้าเปิดจากที่ไหนก็ได้)

โปรเจกต์นี้เตรียมไฟล์ไว้ให้พร้อม deploy แล้ว (`Procfile`, `gunicorn` ใน
`requirements.txt`, และ `app.py` สร้าง DB อัตโนมัติตอนเริ่มรัน) แนะนำ **Render.com**
เพราะฟรี เชื่อมกับ GitHub ได้ตรง และตั้งค่าไม่กี่ขั้นตอน:

### ขั้นตอน (ทำครั้งเดียว)
1. **สร้าง repo บน GitHub**
   - เข้า https://github.com/new → ตั้งชื่อ repo เช่น `slitting-clone` → กด Create repository
   - อย่าเลือก "Add README" (เดี๋ยวไฟล์ชนกับที่มีอยู่แล้ว)

2. **Push โปรเจกต์ขึ้น GitHub** (รันในโฟลเดอร์ `slitting-clone` บนเครื่องคุณ)
   ```bash
   cd path\to\slitting-clone
   git init
   git add .
   git commit -m "initial commit"
   git branch -M main
   git remote add origin https://github.com/<username>/slitting-clone.git
   git push -u origin main
   ```
   (ถ้าเครื่องคุณยังไม่เคย login git มาก่อน จะมี popup ให้ login GitHub ผ่านเบราว์เซอร์ ทำตามนั้นได้เลย)

3. **สมัคร/ล็อกอิน Render**
   - ไปที่ https://render.com → Sign in with GitHub (ใช้บัญชี GitHub เดิม)

4. **สร้าง Web Service**
   - กด **New +** → **Web Service**
   - เลือก repo `slitting-clone` ที่เพิ่ง push ไป
   - ตั้งค่า:
     - **Name**: ตั้งชื่ออะไรก็ได้ เช่น `slitting-clone` (ชื่อนี้จะไปอยู่ในลิงก์)
     - **Runtime**: Python 3
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn app:app`
     - **Instance Type**: Free
   - กด **Create Web Service**

5. รอสัก 1-2 นาที Render จะ build+deploy ให้ เสร็จแล้วจะได้ลิงก์แบบ
   `https://slitting-clone-xxxx.onrender.com` — **ลิงก์นี้แหละที่ส่งให้ลูกค้าเปิดได้เลย
   จากที่ไหนก็ได้ ไม่ต้องเปิดเครื่องคุณทิ้งไว้**

### หลังจากแก้โค้ดในอนาคต
แค่ `git add . && git commit -m "..." && git push` — Render จะ deploy เวอร์ชันใหม่ให้อัตโนมัติ
ไม่ต้องมาตั้งค่าอะไรซ้ำ

### ข้อจำกัดที่ควรรู้ (Free tier ของ Render)
- เซิร์ฟเวอร์จะ "หลับ" ถ้าไม่มีคนเข้าเกิน ~15 นาที พอมีคนเปิดลิงก์ครั้งแรกจะช้าประมาณ 30-50 วิ (คื่นตัว) หลังจากนั้นเร็วปกติ — ถ้าจะโชว์ลูกค้าตามนัด แนะนำเปิดลิงก์ทิ้งไว้ก่อนสัก 1 นาที
- พื้นที่เก็บไฟล์ (รวม `slitting.db`) เป็นแบบชั่วคราว: **ถ้า deploy โค้ดใหม่หรือเซิร์ฟเวอร์รีสตาร์ท ข้อมูลใน DB จะรีเซ็ตกลับเป็นข้อมูลตัวอย่างเดิม** เหมาะกับการ "โชว์/ทดสอบ" แต่ยังไม่เหมาะเก็บข้อมูลจริงระยะยาว — ถ้าต้องการข้อมูลติดถาวรบอกได้ จะเปลี่ยนไปใช้ Render Postgres (ฟรีเช่นกัน) ให้แทน SQLite

### ทางเลือกอื่นที่ใช้โค้ดเดิมได้เหมือนกัน
Railway.app, PythonAnywhere, Fly.io, หรือเครื่อง server ในองค์กรของคุณเอง
(รัน `gunicorn app:app` เหมือนกันหมด เพราะเป็น Flask + SQLite มาตรฐาน ไม่ผูกกับ cloud เจ้าใดเจ้าหนึ่ง)

## หมายเหตุเรื่องข้อมูล
ข้อมูลตัวอย่าง (Job No, Material Spec ฯลฯ) ใน `init_db.py` เป็นข้อมูลจำลอง
ล้อโครงสร้างจากไฟล์ที่คุณอัปโหลดมา ไม่ใช่ข้อมูลจริงของลูกค้า
แก้/เพิ่มข้อมูลเองได้โดยตรงในไฟล์นั้น หรือยิงผ่าน `/api/jobs` เพื่อสร้างจากภายนอก
