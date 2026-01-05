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
    
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)

    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def start_bot():
    hours = get_target_hours()
    if not hours: 
        print("Brak zaplanowanych godzin na dziś.")
        return

    driver = build_driver()
    # Zwiększamy domyślny czas oczekiwania do 40s dla stabilności serwera
    wait = WebDriverWait(driver, 40)

    try:
        # 1. Logowanie
        print("Logowanie...")
        driver.get("https://healtbox.wod.guru/user/login")
        wait.until(EC.presence_of_element_located((By.NAME, "identity"))).send_keys(EMAIL)
        driver.find_element(By.NAME, "credential").send_keys(HASLO)
        driver.execute_script("arguments[0].click();", wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))))

        # 2. Przejście do kalendarza z mechanizmem Retry (rozwiązuje problem z Timeoutem)
        print("Przejście do kalendarza...")
        success_load = False
        for attempt in range(3):
            try:
                driver.get("https://healtbox.wod.guru/user/calendar")
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "guru-table")))
                success_load = True
                break
            except Exception:
                print(f"Próba {attempt+1} nieudana (Timeout). Odświeżam stronę...")
                driver.refresh()
                time.sleep(2)

        if not success_load:
            print("Nie udało się załadować tabeli po 3 próbach. Kończę.")
            return

        # 3. Ustawienie daty (+8 dni)
        arrow_xpath = "//md-icon[contains(text(), 'keyboard_arrow_right')]/parent::button"
        for i in range(KLIKNIECIA_STRZALKI):
            btn = wait.until(EC.element_to_be_clickable((By.XPATH, arrow_xpath)))
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(1.0) # Bezpieczna pauza na przeładowanie Angulara

        # 4. Pętla Turbo-Zapisy (Czekanie na otwarcie o 21:30)
        for hour in hours:
            print(f"Monitorowanie godziny {hour}...")
            xpath_row = f"//tr[contains(., '{hour}')]//button"
            
            start_wait = time.time()
            # Bot bije w przycisk przez max 4 minuty
            while time.time() - start_wait < 240:
                try:
                    slot_btn = driver.find_element(By.XPATH, xpath_row)
                    # Sprawdzenie czy przycisk jest aktywny
                    if slot_btn.is_enabled() and "disabled" not in slot_btn.get_attribute("class"):
                        driver.execute_script("arguments[0].click();", slot_btn)
                        
                        confirm_xpath = "//button[contains(@ng-click, 'ctrl.book') and (contains(., 'Zapisz') or contains(., 'ZAPISZ'))]"
                        confirm_btn = wait.until(EC.element_to_be_clickable((By.XPATH, confirm_xpath)))
                        driver.execute_script("arguments[0].click();", confirm_btn)
                        
                        print(f"SUKCES: Zapisano na {hour} o {datetime.now().strftime('%H:%M:%S')}")
                        break
                except:
                    pass
                time.sleep(0.3) # Sprawdzaj co 300ms
            
            time.sleep(1.5)

    except Exception as e:
        print(f"Wystąpił błąd ogólny: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    start_bot()
