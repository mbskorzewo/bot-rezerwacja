name: Rezerwacja Treningu (Pn-Sr-Pt)

on:
  schedule:
    # 20:28 UTC = 21:28 czasu polskiego (w zimie)
    # Dni tygodnia: 0 (Nd), 2 (Wt), 4 (Cz)
    # Startujemy 2 minuty wcześniej, aby skrypt zdążył się zalogować i czekać na przycisk
    - cron: '28 20 * * 0,2,4'
  
  workflow_dispatch: # Pozwala na ręczne uruchomienie w dowolnym momencie

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Pobranie kodu z repozytorium
        uses: actions/checkout@v3

      - name: Konfiguracja Pythona
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Instalacja potrzebnych bibliotek
        run: |
          pip install -r requirements.txt

      - name: Uruchomienie skryptu rezerwacji
        env:
          WODGURU_EMAIL: ${{ secrets.WODGURU_EMAIL }}
          WODGURU_PASSWORD: ${{ secrets.WODGURU_PASSWORD }}
        run: python rez.py
