import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime
load_dotenv()

def lambda_handler(event, context):
    session = requests.Session()

    # STEP 1: Login
    # Setup headless Chrome
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=options)
    try:
        now = datetime.now()
        date_time = now.strftime("%Y-%m-%d %H:%M:%S")
        print(date_time)
        send_telegram('Bot aktif di tanggal ' + str(date_time))
        dashboard_url = os.getenv('DASHBOARD_URL')
        email = os.getenv('EMAIL')
        password = os.getenv('PASSWORD')  
        driver.get(dashboard_url)

        # Tunggu halaman login muncul
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))

        # Screenshot untuk debugging
        # driver.save_screenshot("after_login.png")

        # Isi email
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@placeholder='SOCO Email']"))
        )
        email_input.clear()
        email_input.send_keys(email)

        # Isi password
        password_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='password']"))
        )
        password_input.clear()
        password_input.send_keys(password)

        # Tombol Login — tunggu sampai bisa diklik
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Login')]"))
        )

        # Gunakan script click untuk jaga-jaga
        driver.execute_script("arguments[0].click();", login_button)
        # driver.save_screenshot("after_login.png")
        # Tunggu tambahan 30 detik jika diperlukan
        time.sleep(10)
        
        send_telegram('Proses login')
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//p[contains(text(), 'Dikdik Kusdinar')]"))
            )
            print("✅ Login berhasil dan elemen user muncul.")            
            # Ambil screenshot setelah login berhasil dan halaman utama muncul
            # driver.save_screenshot("after_login_success.png")
            print("📸 Screenshot disimpan.")
            # --- MULAI PROSES CHECK OUT ---
            attendance_buttons = driver.find_elements(By.CLASS_NAME, "btn-attendance")
            check_out_button = None

            for btn in attendance_buttons:                
                text = btn.text.strip().lower()
                if "check out" in text:
                    check_out_button = btn
                    break
            send_telegram('Login berhasil')
            if check_out_button:
                print("🟢 Tombol Check Out ditemukan, klik sekarang...")
                check_out_button.click()
                time.sleep(3)  # tunggu animasi atau pop-up
                # driver.save_screenshot("after_checkout_clicked.png")
                print("📸 Screenshot setelah klik Check Out disimpan.")
                try:
                    print('Check pop up confirmation')
                    WebDriverWait(driver,10).until(
                        EC.presence_of_element_located(
                            (By.XPATH,"//h4[contains(text(), 'Confirmation')]")
                        )
                    )
                    print("✅ Popup konfirmasi muncul.")
                    modal_button = driver.find_elements(By.XPATH,"//section//button[@class='btn']")
                    send_telegram('Pop up confirmation')
                    confirm_btn = None 
                    for _btn in modal_button:
                        if "check out" in _btn.text.strip().lower():
                            confirm_btn = _btn
                            break                    
                    
                    if confirm_btn:
                        confirm_btn.click()                        
                        print('Button check out diklik')
                        time.sleep(1)
                        send_telegram('Check out berhasil dilakukan')
                        # driver.save_screenshot('check_out_success.png')
                    else:
                        print('Button check out gagal diklik')
                        time.sleep(1)
                        send_telegram('Button check out gagal diklik')
                        # driver.save_screenshot('check_out_failed.png')
                    
                except Exception as e_confirm:
                    print(e_confirm)
                    send_telegram(str(e_confirm))
                
            else:
                print("⚪ Tidak ada tombol Check Out hari ini.")
                send_telegram("Tidak ada tombol Check Out hari ini.")
                # driver.save_screenshot("no_checkout_button.png")
        except Exception as e_login:
            print("⚪ Tidak ada tombol Check Out hari ini.")
            print(e_login)
            send_telegram(str(e_login))
            # driver.save_screenshot("no_checkout_button.png")         
        
    except Exception as e:
        print("❗Terjadi error:", str(e))      
        send_telegram(str(e))  
        # driver.save_screenshot("login_fail_debug.png")
    finally:
        driver.quit()

def send_telegram(message):
    try:
        token = os.getenv("TELE_TOKEN")
        # print(token)
        chatid = os.getenv("TELE_CHATID")
        # print(chatid)
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {        
            "chat_id":chatid,
            "text":message,
            "parse_mode":'HTML'
        }
        response = requests.post(url,data=payload)
    except Exception as e:        
        print('Telegram response' + str(e))
    
