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

# --- KONFIGURACJA ---
KLIKNIECIA_STRZALKI = 8 

def get_target_hours():
    # 0=Pn, 1=Wt, 2=Śr, 3=Cz, 4=Pt, 5=Sb, 6=Nd
    # UWAGA: Skrypt startuje o 21:30, więc sprawdzamy dzień "wieczorny"
    dzien_tygodnia = datetime.now().weekday()
    
    if dzien_tygodnia == 6: # NIEDZIELA 21:30 -> Cel: PONIEDZIAŁEK (+8 dni)
        print("Logika: Niedziela wieczór. Cel: Poniedziałek. Godziny: 16:00, 16:30")
        return ["16:00", "16:30"]
        
    elif dzien_tygodnia == 1: # WTOREK 21:30 -> Cel: ŚRODA (+8 dni)
        print("Logika: Wtorek wieczór. Cel: Środa. Godziny: 19:30, 20:00")
        return ["19:30", "20:00"]
        
    elif dzien_tygodnia == 3: # CZWARTEK 21:30 -> Cel: PIĄTEK (+8 dni)
        print("Logika: Czwartek wieczór. Cel: Piątek. Godziny: 09:00, 09:30")
        return ["09:00", "09:30"]
    
    print("Dzień poza harmonogramem (brak przypisanych godzin).")
    return []

def start_bot():
    TARGET_HOURS = get_target_hours()
    if not TARGET_HOURS:
        return

    print(f"[{datetime.now().strftime('%H:%M:%S')}] URUCHOMIENIE REZERWACJI")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
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
        print("Zalogowano pomyślnie.")

        # 2. PRZECHODZENIE DO DATY (8 kliknięć)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "guru-table")))
        arrow_xpath = "//md-icon[contains(text(), 'keyboard_arrow_right')]/parent::button"
        
        for i in range(KLIKNIECIA_STRZALKI):
            arrow_btn = wait.until(EC.element_to_be_clickable((By.XPATH, arrow_xpath)))
            driver.execute_script("arguments[0].click();", arrow_btn)
            time.sleep(1.5)
        print(f"Przesunięto kalendarz o {KLIKNIECIA_STRZALKI} dni.")

        # 3. REZERWACJA DWÓCH TERMINÓW
        for hour in TARGET_HOURS:
            try:
                print(f"Szukanie godziny: {hour}...")
                xpath_row_btn = f"//tr[contains(., '{hour}')]//button"
                row_btn = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_row_btn)))
                driver.execute_script("arguments[0].click();", row_btn)
                
                # Kliknięcie "Zapisz" w wyskakującym oknie
                confirm_xpath = "//button[contains(@ng-click, 'ctrl.book') and (contains(., 'Zapisz') or contains(., 'ZAPISZ'))]"
                confirm_btn = wait.until(EC.visibility_of_element_located((By.XPATH, confirm_xpath)))
                time.sleep(1.5)
                driver.execute_script("arguments[0].click();", confirm_btn)
                
                print(f"POTWIERDZONO REZERWACJĘ: {hour}")
                time.sleep(3) # Pauza przed szukaniem kolejnej godziny
                
            except Exception as e:
                print(f"Nie udało się zarezerwować {hour} (może brak miejsc lub błąd): {e}")

    except Exception as e:
        print(f"Błąd krytyczny: {e}")
    finally:
        print("Kończenie pracy bota.")
        driver.quit()

if __name__ == "__main__":
    start_bot()
