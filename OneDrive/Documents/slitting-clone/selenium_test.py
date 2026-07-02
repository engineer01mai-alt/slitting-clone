"""
selenium_test.py
สคริปต์ทดสอบเชื่อมข้อมูล: เปิดเว็บด้วย Microsoft Edge ผ่าน Selenium
แล้วกรอกข้อมูลลงหน้า "Data Entry" โดยอ้างอิง field id/name เดียวกับ
โครงสร้างเว็บต้นฉบับ (data_entry_page.txt) เพื่อจำลองการที่โปรแกรมของคุณ
ป้อนค่าที่วัดได้เข้าเว็บแบบอัตโนมัติ

ติดตั้งก่อนใช้งาน:
    pip install selenium

ต้องมี Microsoft Edge ติดตั้งอยู่ในเครื่อง และ msedgedriver
(Selenium 4.6+ จะดาวน์โหลด driver ให้อัตโนมัติผ่าน Selenium Manager
 ไม่ต้องตั้งค่า PATH เอง)

วิธีรัน:
    1) รันเว็บแอปก่อน:  python app.py
    2) รันสคริปต์นี้:   python selenium_test.py --job S270655 --url http://127.0.0.1:5000
"""
import argparse
import time
from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def build_driver(headless: bool = False):
    options = EdgeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--start-maximized")
    # Selenium Manager (selenium>=4.6) จะจัดการดาวน์โหลด msedgedriver ที่ตรงเวอร์ชันให้เอง
    driver = webdriver.Edge(options=options)
    return driver


def fill_and_submit(driver, base_url: str, job_no: str, measurements: dict, wait_seconds: int = 10):
    """
    measurements: dict ของค่าที่ 'โปรแกรมที่คุณเขียน' วัดได้ ตัวอย่าง:
    {
        2: {  # seq_no ของ piece ในตาราง
            "TopThicknessActual": "1.936",
            "TopWidthActual": "131.91",
            "EndThicknessActual": "1.937",
            "EndWidthActual": "131.88",
            "BurrActual": "0.011",
            "Appreance": "OK",
        },
        ...
    }
    """
    wait = WebDriverWait(driver, wait_seconds)

    # 1) เปิดหน้า Data Entry ของใบงานที่ต้องการ (อ้างอิงโครงสร้าง /Inspection/SlittingInspectionPage2)
    entry_url = f"{base_url}/Inspection/SlittingInspectionPage2?JobNo={job_no}"
    driver.get(entry_url)
    wait.until(EC.presence_of_element_located((By.ID, "JobNo")))

    print(f"เปิดหน้ากรอกผลของใบงาน: {job_no}")
    print("JobNo (readonly):", driver.find_element(By.ID, "JobNo").get_attribute("value"))
    print("Material Spec  :", driver.find_element(By.ID, "MaterialSpec").get_attribute("value"))

    # 2) กรอกค่าที่หัวใบงาน (ตัวอย่าง ThicknessActual / WidthActual) ถ้ามีในชุดข้อมูล
    header = measurements.get("header", {})
    if "ThicknessActual" in header:
        el = driver.find_element(By.ID, "ThicknessActual")
        el.clear()
        el.send_keys(str(header["ThicknessActual"]))
    if "WidthActual" in header:
        el = driver.find_element(By.ID, "WidthActual")
        el.clear()
        el.send_keys(str(header["WidthActual"]))

    # 3) กรอกค่าในตารางแต่ละ piece ตาม seq_no โดยอ้างอิง id เดิม เช่น TopThicknessActual_2
    for seq_no, values in measurements.items():
        if seq_no == "header":
            continue
        for field, value in values.items():
            field_id = f"{field}_{seq_no}"
            try:
                el = driver.find_element(By.ID, field_id)
            except Exception:
                print(f"  [!] ไม่พบฟิลด์ {field_id} (ข้ามไป)")
                continue

            tag = el.tag_name.lower()
            if tag == "select":
                from selenium.webdriver.support.ui import Select
                Select(el).select_by_value(str(value))
            else:
                el.clear()
                el.send_keys(str(value))
            print(f"  กรอก {field_id} = {value}")

    time.sleep(0.5)  # ให้เวลา JS คำนวณผล OK/NG ฝั่ง client (ถ้ามี) ก่อน submit

    # 4) กดปุ่ม Submit เพื่อบันทึกลงฐานข้อมูล (ฟอร์ม POST ไป /Inspection/SlittingInspectionPage2)
    submit_btn = driver.find_element(By.ID, "btnSubmit")
    submit_btn.click()

    wait.until(EC.presence_of_element_located((By.ID, "JobNo")))
    print("บันทึกผลเรียบร้อย สถานะปัจจุบัน:", driver.find_element(By.ID, "Status").get_attribute("value"))


def main():
    parser = argparse.ArgumentParser(description="Selenium Edge test - เชื่อมข้อมูลกับเว็บจำลอง Slitting Inspection")
    parser.add_argument("--url", default="http://127.0.0.1:5000", help="Base URL ของเว็บที่จะทดสอบ (เว็บที่ hosted จริงก็ใส่ได้)")
    parser.add_argument("--job", default="S270655", help="Job No ที่จะเปิดกรอกผล")
    parser.add_argument("--headless", action="store_true", help="รันแบบไม่แสดงหน้าต่างเบราว์เซอร์")
    args = parser.parse_args()

    driver = build_driver(headless=args.headless)
    try:
        # ตัวอย่างข้อมูลที่ "โปรแกรมของคุณ" วัดได้ แล้วส่งเข้ามากรอกในเว็บ
        sample_measurements = {
            "header": {"ThicknessActual": "1.934", "WidthActual": "1221.0"},
            2: {
                "TopThicknessActual": "1.936",
                "TopWidthActual": "131.91",
                "EndThicknessActual": "1.937",
                "EndWidthActual": "131.88",
                "BurrActual": "0.011",
                "Appreance": "OK",
            },
            3: {
                "TopThicknessActual": "1.940",
                "TopWidthActual": "131.95",
                "EndThicknessActual": "1.941",
                "EndWidthActual": "131.90",
                "BurrActual": "0.012",
                "Appreance": "OK",
            },
        }
        fill_and_submit(driver, args.url, args.job, sample_measurements)
    finally:
        time.sleep(3)  # เผื่อเวลาให้ดูผลบนหน้าจอก่อนปิด
        driver.quit()


if __name__ == "__main__":
    main()
