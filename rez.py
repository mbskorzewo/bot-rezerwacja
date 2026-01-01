import time
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- POBIERANIE DANYCH Z GITHUB SECRETS ---
EMAIL = os.getenv("WODGURU_EMAIL")
HASLO = os.getenv("WODGURU_PASSWORD")
TARGET_HOURS = ["23:00", "23:30"]
KLIKNIECIA_STRZALKI = 8 

def start_bot():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] START BOTA W CHMURZE")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Serwer nie ma ekranu
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    wait = WebDriverWait(driver, 25)

    try:
        # 1. LOGOWANIE
        driver.get("https://healtbox.wod.guru/user/login")
        wait.until(EC.presence_of_element_located((By.NAME, "identity"))).send_keys(EMAIL)
        driver.find_element(By.NAME, "credential").send_keys(HASLO)
        login_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
        driver.execute_script("arguments[0].click();", login_btn)
        print("Zalogowano.")

        # 2. PRZECHODZENIE DO DATY
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "guru-table")))
        arrow_xpath = "//md-icon[contains(text(), 'keyboard_arrow_right')]/parent::button"
        
        for i in range(KLIKNIECIA_STRZALKI):
            arrow_btn = wait.until(EC.element_to_be_clickable((By.XPATH, arrow_xpath)))
            driver.execute_script("arguments[0].click();", arrow_btn)
            time.sleep(1.5)

        # 3. REZERWACJA
        found = False
        for hour in TARGET_HOURS:
            try:
                xpath_row_btn = f"//tr[contains(., '{hour}')]//button"
                row_btn = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_row_btn)))
                driver.execute_script("arguments[0].click();", row_btn)
                
                confirm_xpath = "//button[contains(@ng-click, 'ctrl.book') and (contains(., 'Zapisz') or contains(., 'ZAPISZ'))]"
                confirm_btn = wait.until(EC.visibility_of_element_located((By.XPATH, confirm_xpath)))
                time.sleep(1)
                driver.execute_script("arguments[0].click();", confirm_btn)
                print(f"!!! SUKCES: ZAREZERWOWANO {hour} !!!")
                found = True
                break
            except:
                continue

        if not found:
            print("Nie znaleziono terminu.")

    except Exception as e:
        print(f"Błąd: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    start_bot()