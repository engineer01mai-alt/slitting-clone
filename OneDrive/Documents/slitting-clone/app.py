"""
app.py
เว็บแอปจำลองโครงสร้าง "Slitting Inspection" (Search + Data Entry) แบบง่าย
สำหรับใช้ทดสอบเชื่อมข้อมูลกับโปรแกรม/สคริปต์ Selenium ของคุณ

รัน:  python app.py
เปิด: http://127.0.0.1:5000/Inspection/SlittingInspectionPage1A
"""
from flask import Flask, request, render_template, redirect, url_for, jsonify
import sqlite3
import os
from init_db import checkpoint, calc_result, calc_overall

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "slitting.db")

# สร้าง DB อัตโนมัติตอน import โมดูล (ทำงานทั้งตอนรันด้วย `python app.py`
# และตอนรันบน hosting จริงผ่าน gunicorn ซึ่งไม่ได้ผ่าน __main__)
if not os.path.exists(DB_PATH):
    import init_db as _init
    _init.main()

app = Flask(__name__)


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
# หน้า SEARCH (คล้าย search_page.txt) -> /Inspection/SlittingInspectionPage1A
# ---------------------------------------------------------------------------
@app.route("/Inspection/SlittingInspectionPage1A", methods=["GET"])
def search_page():
    q_date = request.args.get("ProductionDate", "").strip()
    q_material = request.args.get("MaterialSpec", "").strip()
    q_jobno = request.args.get("JobNo", "").strip()
    q_objective = request.args.get("JobObjective", "").strip()
    q_machine = request.args.get("Machine", "").strip()
    q_status = request.args.get("Status", "").strip()

    sql = "SELECT * FROM jobs WHERE 1=1"
    params = []
    if q_date:
        sql += " AND production_date = ?"; params.append(q_date)
    if q_material:
        sql += " AND material_spec LIKE ?"; params.append(f"%{q_material}%")
    if q_jobno:
        sql += " AND job_no LIKE ?"; params.append(f"%{q_jobno}%")
    if q_objective and q_objective != "Select All":
        sql += " AND job_objective = ?"; params.append(q_objective)
    if q_machine:
        sql += " AND machine LIKE ?"; params.append(f"%{q_machine}%")
    if q_status and q_status not in ("", "All"):
        sql += " AND status = ?"; params.append(q_status)
    sql += " ORDER BY production_date DESC, job_no DESC"

    conn = get_conn()
    rows = conn.execute(sql, params).fetchall()
    conn.close()

    return render_template(
        "search.html",
        rows=rows,
        q_date=q_date, q_material=q_material, q_jobno=q_jobno,
        q_objective=q_objective, q_machine=q_machine, q_status=q_status,
    )


# AJAX: คืนค่าสถานะสรุปผลของงาน (เดิม /Inspection/Result) -> "checked/total_OK|NG"
@app.route("/Inspection/Result", methods=["POST"])
def ajax_result():
    job_no = request.form.get("jobNo", "").strip()
    conn = get_conn()
    pieces = conn.execute("SELECT overall_result FROM pieces WHERE job_no=?", (job_no,)).fetchall()
    conn.close()
    total = len(pieces)
    checked = sum(1 for p in pieces if p["overall_result"] != "")
    ng = sum(1 for p in pieces if p["overall_result"] == "NG")
    result1 = f"{checked}/{total}"
    result2 = "NG" if ng > 0 else ("OK" if checked == total and total > 0 else "")
    return f"{result1}_{result2}"


# AJAX: เช็คสิทธิ์ก่อนเปิดหน้ากรอกผล (เดิม /Inspection/getJobNoByRowTable)
@app.route("/Inspection/getJobNoByRowTable", methods=["GET"])
def ajax_get_jobno_by_row():
    job_no = request.args.get("colValue", "").strip()
    conn = get_conn()
    job = conn.execute("SELECT * FROM jobs WHERE job_no=?", (job_no,)).fetchone()
    conn.close()
    if job is None:
        return jsonify(None)
    return jsonify({"jobNo": job["job_no"], "ok": True})


# AJAX เดิมของปุ่ม Search (เดิม /Inspection/getString) - เก็บไว้เพื่อความเข้ากันได้
@app.route("/Inspection/getString", methods=["GET"])
def ajax_get_string():
    return jsonify({"status": "ok"})


# ---------------------------------------------------------------------------
# หน้า DATA ENTRY (คล้าย data_entry_page.txt) -> /Inspection/SlittingInspectionPage2
# ---------------------------------------------------------------------------
@app.route("/Inspection/SlittingInspectionPage2", methods=["GET"])
def entry_page():
    job_no = request.args.get("JobNo") or request.args.get("jobNo") or ""
    conn = get_conn()
    job = conn.execute("SELECT * FROM jobs WHERE job_no=?", (job_no,)).fetchone()
    if job is None:
        # ถ้าไม่ได้ระบุ/ไม่พบ ให้ใช้ใบงานแรกที่ยังไม่ Completed เป็นตัวอย่าง
        job = conn.execute("SELECT * FROM jobs WHERE status!='Completed' ORDER BY job_no LIMIT 1").fetchone()
        job_no = job["job_no"] if job else ""
    pieces = conn.execute(
        "SELECT * FROM pieces WHERE job_no=? ORDER BY seq_no", (job_no,)
    ).fetchall()
    conn.close()
    return render_template("entry.html", job=job, pieces=pieces)


# บันทึกค่าที่กรอกในหน้า Data Entry (ทั้งหัวใบงาน และตารางแต่ละ piece)
@app.route("/Inspection/SlittingInspectionPage2", methods=["POST"])
def entry_page_save():
    job_no = request.form.get("JobNo", "").strip()
    conn = get_conn()

    # อัปเดตค่าที่หัวใบงาน (ThicknessActual / WidthActual)
    thickness_actual = request.form.get("ThicknessActual")
    width_actual = request.form.get("WidthActual")
    if thickness_actual or width_actual:
        conn.execute(
            "UPDATE jobs SET thickness_actual=?, width_actual=? WHERE job_no=?",
            (thickness_actual or None, width_actual or None, job_no),
        )

    # อัปเดตค่าที่กรอกในตารางแต่ละ piece (คีย์เป็น field_<seq_no>)
    pieces = conn.execute("SELECT * FROM pieces WHERE job_no=? ORDER BY seq_no", (job_no,)).fetchall()
    for piece in pieces:
        seq = piece["seq_no"]

        def f(name):
            v = request.form.get(f"{name}_{seq}")
            return float(v) if v not in (None, "",) else None

        p = dict(piece)
        p["top_thickness_actual"] = f("TopThicknessActual") if f"TopThicknessActual_{seq}" in request.form else piece["top_thickness_actual"]
        p["top_width_actual"] = f("TopWidthActual") if f"TopWidthActual_{seq}" in request.form else piece["top_width_actual"]
        p["end_thickness_actual"] = f("EndThicknessActual") if f"EndThicknessActual_{seq}" in request.form else piece["end_thickness_actual"]
        p["end_width_actual"] = f("EndWidthActual") if f"EndWidthActual_{seq}" in request.form else piece["end_width_actual"]
        p["camber_actual"] = f("CamActual") if f"CamActual_{seq}" in request.form else piece["camber_actual"]
        p["deviation_actual"] = f("DevActual") if f"DevActual_{seq}" in request.form else piece["deviation_actual"]
        p["burr_actual"] = f("BurrActual") if f"BurrActual_{seq}" in request.form else piece["burr_actual"]
        p["appearance"] = request.form.get(f"Appreance_{seq}", piece["appearance"])

        p["top_thickness_res"] = calc_result(p["top_thickness_actual"], p["thick_min1"], p["thick_max1"])
        p["top_width_res"] = calc_result(p["top_width_actual"], p["width_min1"], p["width_max1"])
        p["end_thickness_res"] = calc_result(p["end_thickness_actual"], p["thick_min2"], p["thick_max2"])
        p["end_width_res"] = calc_result(p["end_width_actual"], p["width_min2"], p["width_max2"])
        p["overall_result"] = calc_overall(p)

        conn.execute(
            """UPDATE pieces SET top_thickness_actual=?, top_thickness_res=?,
                                  top_width_actual=?, top_width_res=?,
                                  end_thickness_actual=?, end_thickness_res=?,
                                  end_width_actual=?, end_width_res=?,
                                  camber_actual=?, deviation_actual=?, burr_actual=?,
                                  appearance=?, overall_result=?
               WHERE id=?""",
            (p["top_thickness_actual"], p["top_thickness_res"],
             p["top_width_actual"], p["top_width_res"],
             p["end_thickness_actual"], p["end_thickness_res"],
             p["end_width_actual"], p["end_width_res"],
             p["camber_actual"], p["deviation_actual"], p["burr_actual"],
             p["appearance"], p["overall_result"], piece["id"]),
        )

    # ถ้ากดปุ่ม Submit -> เปลี่ยนสถานะใบงานเป็น Submitted
    if request.form.get("btnSubmit") is not None:
        conn.execute("UPDATE jobs SET status='Submitted' WHERE job_no=?", (job_no,))
    if request.form.get("btnNotUse") is not None:
        conn.execute("UPDATE jobs SET status='New' WHERE job_no=?", (job_no,))

    conn.commit()
    conn.close()
    return redirect(url_for("entry_page", JobNo=job_no))


# ---------------------------------------------------------------------------
# API แบบ JSON ล้วน สำหรับให้ "โปรแกรมที่คุณเขียน" เชื่อมต่อ/ทดสอบข้อมูลตรงๆ
# (ไม่ต้องผ่านหน้าเว็บ/ฟอร์ม)
# ---------------------------------------------------------------------------
@app.route("/api/jobs", methods=["GET"])
def api_jobs():
    conn = get_conn()
    rows = [dict(r) for r in conn.execute("SELECT * FROM jobs ORDER BY job_no").fetchall()]
    conn.close()
    return jsonify(rows)


@app.route("/api/jobs/<job_no>", methods=["GET"])
def api_job_detail(job_no):
    conn = get_conn()
    job = conn.execute("SELECT * FROM jobs WHERE job_no=?", (job_no,)).fetchone()
    pieces = conn.execute("SELECT * FROM pieces WHERE job_no=? ORDER BY seq_no", (job_no,)).fetchall()
    conn.close()
    if job is None:
        return jsonify({"error": "job not found"}), 404
    return jsonify({"job": dict(job), "pieces": [dict(p) for p in pieces]})


@app.route("/api/jobs/<job_no>/pieces/<int:seq_no>", methods=["POST"])
def api_update_piece(job_no, seq_no):
    """ให้โปรแกรมภายนอกยิงค่าที่วัดได้เข้ามาตรงๆ เป็น JSON แทนการกรอกผ่านฟอร์ม"""
    data = request.get_json(force=True) or {}
    conn = get_conn()
    piece = conn.execute(
        "SELECT * FROM pieces WHERE job_no=? AND seq_no=?", (job_no, seq_no)
    ).fetchone()
    if piece is None:
        conn.close()
        return jsonify({"error": "piece not found"}), 404

    p = dict(piece)
    for key in ("top_thickness_actual", "top_width_actual", "end_thickness_actual",
                "end_width_actual", "camber_actual", "deviation_actual", "burr_actual"):
        if key in data:
            p[key] = data[key]
    if "appearance" in data:
        p["appearance"] = data["appearance"]

    p["top_thickness_res"] = calc_result(p["top_thickness_actual"], p["thick_min1"], p["thick_max1"])
    p["top_width_res"] = calc_result(p["top_width_actual"], p["width_min1"], p["width_max1"])
    p["end_thickness_res"] = calc_result(p["end_thickness_actual"], p["thick_min2"], p["thick_max2"])
    p["end_width_res"] = calc_result(p["end_width_actual"], p["width_min2"], p["width_max2"])
    p["overall_result"] = calc_overall(p)

    conn.execute(
        """UPDATE pieces SET top_thickness_actual=?, top_thickness_res=?,
                              top_width_actual=?, top_width_res=?,
                              end_thickness_actual=?, end_thickness_res=?,
                              end_width_actual=?, end_width_res=?,
                              camber_actual=?, deviation_actual=?, burr_actual=?,
                              appearance=?, overall_result=?
           WHERE id=?""",
        (p["top_thickness_actual"], p["top_thickness_res"],
         p["top_width_actual"], p["top_width_res"],
         p["end_thickness_actual"], p["end_thickness_res"],
         p["end_width_actual"], p["end_width_res"],
         p["camber_actual"], p["deviation_actual"], p["burr_actual"],
         p["appearance"], p["overall_result"], piece["id"]),
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "overall_result": p["overall_result"]})


@app.route("/", methods=["GET"])
def index():
    return redirect(url_for("search_page"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
