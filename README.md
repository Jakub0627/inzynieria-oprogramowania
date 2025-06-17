# Aplikacja do symulacji zarządzania portfelem kryptowalut

Webowa aplikacja pozwalająca użytkownikom na śledzenie, analizę i optymalizację portfela kryptowalut z wykorzystaniem prognoz, alertów i wizualizacji. Dane przechowywane są w Firebase, a dane rynkowe pobierane z CryptoCompare API.

---

## Wymagania

- Python 3.8+
- pip
- środowisko wirtualne (zalecane)
- konto Firebase (Authentication + Firestore)
- konto Gmail (SMTP)
- klucz API z CryptoCompare

---

## Instalacja

```bash
# klonowanie repozytorium
git clone https://github.com/nazwa-uzytkownika/nazwa-repozytorium.git
cd nazwa-repozytorium

# utworzenie środowiska wirtualnego
python -m venv .venv
source .venv/bin/activate  # lub .venv\Scripts\activate na Windows

# instalacja zależności
pip install -r requirements.txt
```

## Wymagane pliki

### `.env`

Plik `.env` zawiera dane środowiskowe używane przez aplikację (np. API key, dane SMTP). Nie powinien być wersjonowany.

####  Wymagane pola:
| Zmienna | Opis |
|--------|------|
| `CRYPTOCOMPARE_API_KEY` | Twój klucz API z serwisu [https://min-api.cryptocompare.com](https://min-api.cryptocompare.com) |
| `EMAIL_USER` | Adres Gmail do wysyłki alertów |
| `EMAIL_PASS` | Hasło aplikacyjne Gmail |
| `SMTP_SERVER` | Adres serwera SMTP|
| `SMTP_PORT` | Port SMTP |

---

###  `firebase-adminsdk.json`

Ten plik zawiera klucz serwisowy Firebase Admin SDK, potrzebny do:
- weryfikacji tokenów JWT z Firebase Authentication,
- połączenia z Firestore (baza danych).

#### Jak go zdobyć:
1. Przejdź do [Firebase Console](https://console.firebase.google.com/)
2. Wybierz projekt
3. Wejdź w: **Ustawienia projektu → Konta serwisowe → Utwórz nowy klucz prywatny**
4. Zapisz plik jako `firebase-adminsdk.json` w katalogu głównym projektu

Wymagane jest również stworzenie odpowiednich kolekcji w Firestore.


