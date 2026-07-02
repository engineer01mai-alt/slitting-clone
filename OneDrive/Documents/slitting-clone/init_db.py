"""
init_db.py
สร้างฐานข้อมูล SQLite แบบง่าย (ไม่ซับซ้อน) สำหรับระบบจำลอง
Slitting Inspection (Data Entry + Search) และใส่ข้อมูลตัวอย่าง

รันครั้งเดียว: python init_db.py
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "slitting.db")

SCHEMA = """
DROP TABLE IF EXISTS pieces;
DROP TABLE IF EXISTS jobs;

-- ตารางหลัก: 1 แถว = 1 ใบงาน (Job)
CREATE TABLE jobs (
    job_no          TEXT PRIMARY KEY,
    production_date TEXT NOT NULL,      -- dd/mm/yyyy
    machine         TEXT NOT NULL,
    material_id     TEXT,
    material_no     TEXT,
    shear_no        TEXT,
    thickness       REAL,
    width           REAL,
    length          TEXT,
    weight          REAL,
    thickness_actual REAL,
    width_actual     REAL,
    output_type     TEXT DEFAULT 'Coil',
    job_objective   TEXT DEFAULT 'For production',
    material_spec   TEXT,
    status          TEXT DEFAULT 'New', -- New / Enter / Submitted / Completed
    remarks         TEXT DEFAULT 'Ready for Inspection'
);

-- ตารางรอง: รายละเอียดแต่ละ "ม้วน/เส้น" ที่ตรวจในใบงานนั้น
CREATE TABLE pieces (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    job_no           TEXT NOT NULL REFERENCES jobs(job_no) ON DELETE CASCADE,
    seq_no           INTEGER NOT NULL,
    standard_no      TEXT,
    cust_code        TEXT,
    part_name        TEXT,
    inventory_no     TEXT,
    size             TEXT,

    process_thick1   REAL, thick_tl1  TEXT, thick_min1 REAL, thick_max1 REAL,
    top_thickness_actual REAL, top_thickness_res TEXT DEFAULT '',

    process_width1   REAL, width_tl1  TEXT, width_min1 REAL, width_max1 REAL,
    top_width_actual REAL, top_width_res TEXT DEFAULT '',

    process_thick2   REAL, thick_tl2  TEXT, thick_min2 REAL, thick_max2 REAL,
    end_thickness_actual REAL, end_thickness_res TEXT DEFAULT '',

    process_width2   REAL, width_tl2  TEXT, width_min2 REAL, width_max2 REAL,
    end_width_actual REAL, end_width_res TEXT DEFAULT '',

    camber_limit     REAL, camber_op TEXT DEFAULT '<=', camber_actual REAL,
    deviation_limit  REAL, deviation_op TEXT DEFAULT '<=', deviation_actual REAL,
    burr_limit       REAL, burr_op TEXT DEFAULT '<=', burr_actual REAL,

    appearance       TEXT DEFAULT 'OK',
    overall_result   TEXT DEFAULT ''
);
"""

SEED_JOBS = [
    # job_no, production_date, machine, material_id, material_no, shear_no,
    # thickness, width, length, weight, thickness_actual, width_actual,
    # output_type, job_objective, material_spec, status
    ("S270789", "15/07/2022", "S1", "1/1", "ET10001       1", "1/1", 2.0, 1219.0, "C", 3200.0, None, None, "Coil", "For production", "MSM-CC-D-ZC-K18", "Completed"),
    ("S270655", "15/07/2022", "S1", "1/1", "ET10840       1", "1/1", 2.0, 1219.0, "C", 3271.0, 1.93, 1222.0, "Coil", "For production", "SECC-VNX E16/E16(ROHS)", "Submitted"),
    ("S270641", "14/07/2022", "S1", "1/1", "ET10700       1", "1/1", 2.0, 1219.0, "C", 3150.0, None, None, "Coil", "For production", "MSM-CC-D-ZC-K18", "Submitted"),
    ("S270609", "15/07/2022", "S1", "1/1", "ET10555       1", "1/1", 1.6, 1000.0, "C", 2800.0, None, None, "Coil", "For production", "SECC-VNX E16/E16(ROHS)", "Submitted"),
    ("S270607", "15/07/2022", "S1", "1/1", "ET10432       1", "1/1", 1.6, 1000.0, "C", 2750.0, 1.58, 1002.0, "Coil", "For production", "SECC-VNX E16/E16(ROHS)", "Completed"),
    ("S270573", "15/07/2022", "S1", "1/1", "ET10300       1", "1/1", 2.3, 1250.0, "C", 3400.0, 2.28, 1252.0, "Coil", "For production", "SECC-VNX E16/E16(ROHS)", "Completed"),
    ("S270570", "15/07/2022", "S1", "1/1", "ET10250       1", "1/1", 2.3, 1250.0, "C", 3390.0, 2.29, 1249.0, "Coil", "For production", "SECC-VNX E16/E16(ROHS)", "Completed"),
    ("S270537", "14/07/2022", "S1", "1/1", "ET10120       1", "1/1", 2.0, 1219.0, "C", 3100.0, None, None, "Coil", "For production", "SECC-VNX E16/E16(ROHS)", "Submitted"),
    ("S270463", "15/07/2022", "S1", "1/1", "ET10050       1", "1/1", 1.8, 1100.0, "C", 2900.0, 1.79, 1098.0, "Coil", "For production", "MSM-CC-D-ZC-K18", "Completed"),
    ("S5Z0993", "20/12/2025", "S5", "1/1", "ET20993       1", "1/1", 0.8, 900.0, "C", 1500.0, None, None, "Coil", "For production", "SGCC-ZSNCX-Z08", "Completed"),
]

import random

# จำนวน piece (ม้วน/เส้นที่ตรวจ) ต่อใบงาน สำหรับข้อมูลตัวอย่าง
PIECES_PER_JOB = 3


def generate_pieces_for_job(job_row: dict, rng: random.Random):
    """
    สร้างข้อมูล piece ตัวอย่างให้ใบงานหนึ่งใบ โดยอ้างอิง thickness/width จริงของใบงานนั้น
    - ใบงานสถานะ Completed        -> กรอกผลครบทุก piece
    - ใบงานสถานะ Submitted/New    -> กรอกผลบางส่วน (เหมือนงานที่ตรวจค้างอยู่จริง)
    """
    job_no = job_row["job_no"]
    thick = job_row["thickness"] or 2.0
    width = job_row["width"] or 1000.0
    status = job_row["status"]

    thick_tl, width_tl = 0.140, 0.50
    thick_min = round(thick - thick_tl, 3)
    thick_max = round(thick + thick_tl, 3)
    width_min = round(width - width_tl, 2)
    width_max = round(width + width_tl, 2)

    pieces = []
    for i in range(1, PIECES_PER_JOB + 1):
        if status == "Completed":
            entered = True
        elif status == "Submitted":
            entered = i <= 2                 # กรอกไปแล้ว 2 ใน 3 เหลืองาน 1 piece รอตรวจ
        else:                                  # New / Enter
            entered = False

        if entered:
            dt = round(rng.uniform(-0.03, 0.03), 3)
            dw = round(rng.uniform(-0.15, 0.15), 2)
            top_thick = round(thick + dt, 3)
            top_width = round(width + dw, 2)
            end_thick = round(thick + dt + rng.uniform(-0.01, 0.01), 3)
            end_width = round(width + dw + rng.uniform(-0.05, 0.05), 2)
            burr = round(rng.uniform(0.005, 0.03), 3)
        else:
            top_thick = top_width = end_thick = end_width = burr = None

        pieces.append(dict(
            seq_no=i,
            standard_no=f"T05001/{500 + i}",
            cust_code="TSK",
            part_name="",
            inventory_no=f"{job_no}{i:03d}",
            size=f"{thick:.3f}*{width:.3f}",
            process_thick1=thick, thick_tl1=f"-{thick_tl:.3f},+{thick_tl:.3f}",
            thick_min1=thick_min, thick_max1=thick_max, top_thickness_actual=top_thick,
            process_width1=width, width_tl1=f"-{width_tl:.2f},+{width_tl:.2f}",
            width_min1=width_min, width_max1=width_max, top_width_actual=top_width,
            process_thick2=thick, thick_tl2=f"-{thick_tl:.3f},+{thick_tl:.3f}",
            thick_min2=thick_min, thick_max2=thick_max, end_thickness_actual=end_thick,
            process_width2=width, width_tl2=f"-{width_tl:.2f},+{width_tl:.2f}",
            width_min2=width_min, width_max2=width_max, end_width_actual=end_width,
            camber_limit=None, camber_actual=None,
            deviation_limit=None, deviation_actual=None,
            burr_limit=0.100, burr_actual=burr,
            appearance="OK",
        ))

    # ตัวอย่าง NG แบบตั้งใจ 1 จุด (เพื่อทดสอบว่าสีแดง/NG แสดงถูกต้อง) -> เฉพาะ S270789 piece แรก
    if job_no == "S270789" and pieces:
        pieces[0]["top_width_actual"] = round(width_max + 0.8, 2)  # เกินสเปกโดยตั้งใจ

    return pieces


def checkpoint(tl, actual, op):
    """เหมือนฟังก์ชัน checkpoint() ใน JS ต้นฉบับ: เทียบ actual กับ TL ตาม operator"""
    if tl is None:
        return True
    if actual is None:
        return False
    try:
        a, t = float(actual), float(tl)
    except (TypeError, ValueError):
        return False
    return {"<=": a <= t, ">=": a >= t, "<": a < t, ">": a > t}.get(op, False)


def calc_result(actual, vmin, vmax):
    if actual is None or vmin is None or vmax is None:
        return ""
    return "OK" if vmin <= actual <= vmax else "NG"


def calc_overall(p: dict) -> str:
    """จำลอง CheckOverPattern(): ต้องกรอกครบทุกช่องที่มีสเปกกำหนด และทุกช่องต้อง OK"""
    checks = []
    if p.get("process_thick1") is not None:
        checks.append(calc_result(p.get("top_thickness_actual"), p.get("thick_min1"), p.get("thick_max1")))
    if p.get("process_width1") is not None:
        checks.append(calc_result(p.get("top_width_actual"), p.get("width_min1"), p.get("width_max1")))
    if p.get("process_thick2") is not None:
        checks.append(calc_result(p.get("end_thickness_actual"), p.get("thick_min2"), p.get("thick_max2")))
    if p.get("process_width2") is not None:
        checks.append(calc_result(p.get("end_width_actual"), p.get("width_min2"), p.get("width_max2")))
    if p.get("camber_limit") is not None:
        checks.append("OK" if checkpoint(p.get("camber_limit"), p.get("camber_actual"), p.get("camber_op", "<=")) else "NG")
    if p.get("deviation_limit") is not None:
        checks.append("OK" if checkpoint(p.get("deviation_limit"), p.get("deviation_actual"), p.get("deviation_op", "<=")) else "NG")
    if p.get("burr_limit") is not None:
        checks.append("OK" if checkpoint(p.get("burr_limit"), p.get("burr_actual"), p.get("burr_op", "<=")) else "NG")

    if "" in checks:          # ยังกรอกไม่ครบ -> ยังไม่มีผล (เหมือนต้นฉบับเว้นว่างไว้)
        return ""
    if p.get("appearance") == "NG":
        return "NG"
    return "NG" if "NG" in checks else "OK"


def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)

    conn.executemany(
        """INSERT INTO jobs (job_no, production_date, machine, material_id, material_no, shear_no,
                              thickness, width, length, weight, thickness_actual, width_actual,
                              output_type, job_objective, material_spec, status)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        SEED_JOBS,
    )

    # สร้าง piece ตัวอย่างให้ "ทุกใบงาน" (ใช้ seed คงที่ ผลลัพธ์เดิมทุกครั้งที่รันใหม่)
    rng = random.Random(42)
    job_cols = [
        "job_no", "production_date", "machine", "material_id", "material_no", "shear_no",
        "thickness", "width", "length", "weight", "thickness_actual", "width_actual",
        "output_type", "job_objective", "material_spec", "status",
    ]
    for job_tuple in SEED_JOBS:
        job_row = dict(zip(job_cols, job_tuple))
        pieces = generate_pieces_for_job(job_row, rng)
        for p in pieces:
            p["top_thickness_res"] = calc_result(p["top_thickness_actual"], p["thick_min1"], p["thick_max1"])
            p["top_width_res"] = calc_result(p["top_width_actual"], p["width_min1"], p["width_max1"])
            p["end_thickness_res"] = calc_result(p["end_thickness_actual"], p["thick_min2"], p["thick_max2"])
            p["end_width_res"] = calc_result(p["end_width_actual"], p["width_min2"], p["width_max2"])
            p["overall_result"] = calc_overall(p)
            cols = ",".join(p.keys())
            placeholders = ",".join("?" * len(p))
            conn.execute(
                f"INSERT INTO pieces (job_no, {cols}) VALUES (?, {placeholders})",
                [job_row["job_no"]] + list(p.values()),
            )

    conn.commit()
    conn.close()
    print(f"สร้างฐานข้อมูลเรียบร้อย: {DB_PATH}")


if __name__ == "__main__":
    main()
