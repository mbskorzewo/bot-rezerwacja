import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

EMAIL = os.getenv("WODGURU_EMAIL")
HASLO = os.getenv("WODGURU_PASSWORD")
KLIKNIECIA_STRZALKI = 8

def get_target_hours():
    dzien = datetime.now().weekday()
    if dzien == 6: return ["16:00", "16:30"]  # Nd -> Pn
    if dzien == 1: return ["19:30", "20:00"]  # Wt -> Śr
    if dzien == 3: return ["09:00", "09:30"]  # Cz -> Pt
    return []

def build_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1280,900")
    chrome_options.page_load_strategy = "eager"
    
    # Optymalizacja prędkości
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)

    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def start_bot():
    hours = get_target_hours()
    if not hours: return

    driver = build_driver()
    wait = WebDriverWait(driver, 15)

    try:
        # 1. Logowanie (robimy to o 21:28-21:29)
        driver.get("https://healtbox.wod.guru/user/login")
        wait.until(EC.presence_of_element_located((By.NAME, "identity"))).send_keys(EMAIL)
        driver.find_element(By.NAME, "credential").send_keys(HASLO)
        driver.execute_script("arguments[0].click();", wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))))

        # 2. Przejście do kalendarza i ustawienie daty
        driver.get("https://healtbox.wod.guru/user/calendar")
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "guru-table")))
        
        arrow_xpath = "//md-icon[contains(text(), 'keyboard_arrow_right')]/parent::button"
        for _ in range(KLIKNIECIA_STRZALKI):
            btn = wait.until(EC.element_to_be_clickable((By.XPATH, arrow_xpath)))
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(0.8) # Krótka pauza na przeładowanie tabeli

        # 3. Pętla Turbo-Zapisy
        for hour in hours:
            print(f"Czekam na aktywację godziny {hour}...")
            xpath_row = f"//tr[contains(., '{hour}')]//button"
            
            # Pętla sprawdzająca przycisk (próbuje przez maksymalnie 3 minuty)
            start_wait = time.time()
            while time.time() - start_wait < 180:
                try:
                    slot_btn = driver.find_element(By.XPATH, xpath_row)
                    # Sprawdzamy czy przycisk NIE jest wyszarzony (disabled)
                    if slot_btn.is_enabled() and "disabled" not in slot_btn.get_attribute("class"):
                        driver.execute_script("arguments[0].click();", slot_btn)
                        
                        # Potwierdzenie w oknie modalnym
                        confirm_xpath = "//button[contains(@ng-click, 'ctrl.book') and (contains(., 'Zapisz') or contains(., 'ZAPISZ'))]"
                        confirm_btn = wait.until(EC.element_to_be_clickable((By.XPATH, confirm_xpath)))
                        driver.execute_script("arguments[0].click();", confirm_btn)
                        
                        print(f"SUKCES: Zapisano na {hour} o {datetime.now().strftime('%H:%M:%S')}")
                        break
                except:
                    pass
                time.sleep(0.2) # Sprawdzaj co 200ms
            
            # Po udanym zapisie dajemy chwilę na zamknięcie modala przed kolejną godziną
            time.sleep(1)

    finally:
        driver.quit()

if __name__ == "__main__":
    start_bot()
