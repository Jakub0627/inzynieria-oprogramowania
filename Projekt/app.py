from flask import Flask, render_template, request, redirect, url_for, jsonify
from portfolio import Portfolio
import os
import io
import base64
import json
from dotenv import load_dotenv
from matplotlib.figure import Figure
import firebase_admin
from firebase_admin import credentials, firestore, auth as firebase_auth
import numpy as np
from scipy.optimize import minimize
from apscheduler.schedulers.background import BackgroundScheduler
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr

# Inicjalizacja Firebase Admin SDK
cred = credentials.Certificate("firebase-adminsdk.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Wczytanie API key i zmiennych środowiskowych
load_dotenv()
CRYPTOCOMPARE_API_KEY = os.getenv("CRYPTOCOMPARE_API_KEY")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

if not EMAIL_USER or not EMAIL_PASS:
    raise RuntimeError("Brakuje EMAIL_USER lub EMAIL_PASS w pliku .env")

app = Flask(__name__)

# Pobiera UID użytkownika z tokenu JWT
def get_user_id():
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        id_token = auth_header.split('Bearer ')[1]
        try:
            decoded_token = firebase_auth.verify_id_token(id_token)
            return decoded_token['uid']
        except Exception as e:
            print("Błąd weryfikacji tokenu:", e)
    return None

# Wysyłanie e-maila SMTP
def send_email(to, subject, body):
    msg = MIMEText(f"""
Cześć,

Twój alert cenowy został właśnie aktywowany.

{body}

Pozdrawiamy,
Zespół Twojej aplikacji
""".strip())

    msg["Subject"] = subject
    msg["From"] = formataddr(("Alerty Krypto", EMAIL_USER))
    msg["To"] = to
    msg["Reply-To"] = EMAIL_USER

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
            print(f"✅ E-mail wysłany do {to}")
    except smtplib.SMTPAuthenticationError as auth_err:
        print("❌ Błąd autoryzacji SMTP:", auth_err)
    except smtplib.SMTPException as smtp_err:
        print("❌ Błąd SMTP:", smtp_err)
    except Exception as e:
        print(f"❌ Inny błąd wysyłki e-maila do {to}:", e)

# Tworzenie alertu
def create_alert(uid, message):
    db.collection("alerts").add({
        "uid": uid,
        "message": message,
        "timestamp": firestore.SERVER_TIMESTAMP,
        "sent": False
    })

# Wysyłanie alertów oczekujących
def process_pending_alerts():
    print("🔄 Sprawdzanie oczekujących alertów...")

    try:
        alerts = db.collection("alerts").where("sent", "==", False).stream()
    except Exception as e:
        print("❌ Błąd podczas pobierania alertów z Firestore:", e)
        return

    for alert in alerts:
        try:
            data = alert.to_dict()
            uid = data.get("uid")
            symbol = data.get("symbol")
            target = data.get("target")
            message = data.get("message")

            print(f"➡ Alert: {symbol} > {target} USD (UID: {uid})")

            # Pobierz dane użytkownika
            user_doc = db.collection("users").document(uid).get()
            if not user_doc.exists:
                print("⚠️ Użytkownik nie znaleziony:", uid)
                continue

            email = user_doc.to_dict().get("email")
            if not email:
                print("⚠️ Użytkownik nie ma przypisanego maila:", uid)
                continue

            # Pobierz aktualną cenę
            current_price = Portfolio.get_current_price(symbol, CRYPTOCOMPARE_API_KEY)
            print(f"💰 Cena {symbol}: {current_price} USD")

            if current_price is None:
                print(f"⚠️ Brak ceny dla {symbol}, pomijam.")
                continue

            # Warunek: cena aktualna > próg
            if current_price > target:
                print(f"📈 Cena przekroczyła próg: {current_price} > {target}")

                send_email(email, "🔔 Alert cenowy", message)
                db.collection("alerts").document(alert.id).update({"sent": True})
                print("✅ Alert wysłany i zaktualizowany.")
            else:
                print(f"ℹ️ Cena poniżej progu: {current_price} <= {target}")

        except Exception as e:
            print("❌ Błąd przetwarzania alertu:", e)



scheduler = BackgroundScheduler()
scheduler.add_job(process_pending_alerts, "interval", minutes=1)
scheduler.start()

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/")
def dashboard():
    return render_template("dashboard.html")

@app.route("/analysis")
def analysis_view():
    return render_template("analysis.html")

@app.route("/chart", methods=["GET", "POST"])
def chart_redirect():
    if request.method == "POST":
        symbol = request.form.get("crypto").upper()
        return redirect(url_for("chart_view", symbol=symbol))
    return render_template("chart_form.html")

@app.route("/chart/<symbol>")
def chart_view(symbol):
    dates, prices = Portfolio.get_historical_data(symbol, CRYPTOCOMPARE_API_KEY, limit=30)
    if not prices:
        return f"Nie udało się pobrać danych dla {symbol}"

    fig = Figure()
    ax = fig.subplots()
    ax.plot(dates, prices, label="Cena", color="skyblue")

    sma = Portfolio.calculate_moving_average(prices, window=7)
    ax.plot(dates, sma, label="SMA 7", linestyle="--", color="darkred")

    predicted, conf_int = Portfolio.forecast_prices(prices, days=7)
    if predicted is not None:
        future_dates = [dates[-1] + (i + 1) * (dates[1] - dates[0]) for i in range(len(predicted))]
        ax.plot(future_dates, predicted, label="Prognoza", linestyle="--", color="gray")
        ax.fill_between(future_dates, conf_int[:, 0], conf_int[:, 1], color="lightblue", alpha=0.4)

    ax.set_title(f"Wykres cen dla {symbol}")
    ax.set_xlabel("Data")
    ax.set_ylabel("Cena USD")
    ax.legend()
    ax.grid(True)
    fig.autofmt_xdate()

    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode("utf-8")
    buf.close()

    return jsonify({
        "symbol": symbol,
        "image_base64": image_base64
    })

# API endpoints

@app.route("/api/add", methods=["POST"])
def api_add_crypto():
    uid = get_user_id()
    if not uid:
        return "Unauthorized", 401

    data = request.json
    symbol = data.get("crypto", "").upper()
    amount = float(data.get("amount"))
    price = Portfolio.get_current_price(symbol, CRYPTOCOMPARE_API_KEY)

    doc_ref = db.collection("portfolios").document(uid).collection("assets").document(symbol)
    existing = doc_ref.get()

    if existing.exists:
        prev = existing.to_dict()
        total_amount = prev["amount"] + amount
        avg_price = ((prev["amount"] * prev["price"]) + (amount * price)) / total_amount
        doc_ref.set({"amount": total_amount, "price": avg_price})
    else:
        doc_ref.set({"amount": amount, "price": price})

    return jsonify({"status": "added"})

@app.route("/api/delete/<symbol>", methods=["DELETE"])
def api_delete_crypto(symbol):
    uid = get_user_id()
    if not uid:
        return "Unauthorized", 401

    try:
        data = json.loads(request.data)
        amount_to_remove = float(data.get("amount", 0))
    except Exception as e:
        return f"Błąd danych wejściowych: {e}", 400

    doc_ref = db.collection("portfolios").document(uid).collection("assets").document(symbol)
    doc = doc_ref.get()

    if not doc.exists:
        return "Not Found", 404

    current_data = doc.to_dict()
    current_amount = current_data.get("amount", 0)

    if amount_to_remove >= current_amount:
        doc_ref.delete()
    else:
        new_amount = current_amount - amount_to_remove
        doc_ref.update({"amount": new_amount})

    return jsonify({"status": "updated"})

@app.route("/api/portfolio")
def api_portfolio():
    uid = get_user_id()
    if not uid:
        return "Unauthorized", 401

    assets = []
    total_value = 0

    docs = db.collection("portfolios").document(uid).collection("assets").stream()
    for doc in docs:
        data = doc.to_dict()
        value = data["amount"] * data["price"]
        assets.append({
            "crypto_name": doc.id,
            "amount": data["amount"],
            "price": data["price"],
            "value": value
        })
        total_value += value

    return jsonify({"assets": assets, "total_value": total_value})

@app.route("/api/forecast")
def api_forecast():
    uid = get_user_id()
    if not uid:
        return jsonify({"error": "unauthorized"}), 401

    docs = db.collection("portfolios").document(uid).collection("assets").stream()
    total_value = sum(doc.to_dict()["amount"] * doc.to_dict()["price"] for doc in docs)

    forecast = [{"days": d, "value": total_value * (1 + 0.01 * d)} for d in [1, 7, 30]]
    return jsonify({"forecast": forecast})

@app.route("/api/optimize", methods=["POST"])
def api_optimize():
    uid = get_user_id()
    if not uid:
        return jsonify({"error": "unauthorized"}), 401

    docs = db.collection("portfolios").document(uid).collection("assets").stream()
    assets = {doc.id: (doc.to_dict()["price"], doc.to_dict()["amount"]) for doc in docs}

    if not assets:
        return jsonify({"suggestions": ["Portfel jest pusty."]})

    try:
        symbols = list(assets.keys())
        prices = np.array([Portfolio.get_historical_data(s, CRYPTOCOMPARE_API_KEY, limit=100)[1] for s in symbols])
        returns = np.diff(prices, axis=1) / prices[:, :-1]
        mean_returns = np.mean(returns, axis=1)

        def neg_return(weights): return -np.dot(weights, mean_returns)
        result = minimize(neg_return, np.ones(len(symbols)) / len(symbols), bounds=[(0, 1)]*len(symbols), constraints={"type": "eq", "fun": lambda w: np.sum(w) - 1})
        if not result.success:
            raise Exception("Niepowodzenie optymalizacji")

        suggestions = []
        total_val = sum(p * a for p, a in assets.values())
        for i, s in enumerate(symbols):
            current_val = assets[s][0] * assets[s][1]
            current_w = current_val / total_val
            target_w = result.x[i]
            delta = target_w - current_w
            if abs(delta) > 0.02:
                action = "Zwiększ" if delta > 0 else "Zmniejsz"
                suggestions.append(f"{action} udział {s} do {target_w*100:.2f}% (obecnie {current_w*100:.2f}%)")

        if not suggestions:
            suggestions.append("Portfel jest już zoptymalizowany.")

        return jsonify({"suggestions": suggestions})

    except Exception as e:
        return jsonify({"suggestions": [f"Błąd: {str(e)}"]})

@app.route("/api/alerts", methods=["GET", "POST"])
def api_alerts():
    uid = get_user_id()
    if not uid:
        return jsonify({"error": "unauthorized"}), 401

    if request.method == "POST":
        data = request.get_json()
        symbol = data.get("symbol")
        target = data.get("threshold")
        if not symbol or target is None:
            return jsonify({"error": "Brakuje danych"}), 400

        db.collection("alerts").add({
            "uid": uid,
            "symbol": symbol,
            "target": float(target),
            "timestamp": firestore.SERVER_TIMESTAMP,
            "sent": False,
            "message": f"{symbol} przekroczył próg {target} USD!"
        })

        return jsonify({"status": "added"}), 201

    else:  # GET
        alerts = db.collection("alerts").where("uid", "==", uid).order_by("timestamp", direction=firestore.Query.DESCENDING).stream()
        return jsonify({
            "alerts": [
                {**a.to_dict(), "id": a.id}
                for a in alerts
            ]
        })

@app.route("/api/alerts/<alert_id>", methods=["DELETE"])
def delete_alert(alert_id):
    uid = get_user_id()
    if not uid:
        return jsonify({"error": "unauthorized"}), 401

    doc_ref = db.collection("alerts").document(alert_id)
    doc = doc_ref.get()

    if not doc.exists:
        return jsonify({"error": "alert not found"}), 404

    if doc.to_dict().get("uid") != uid:
        return jsonify({"error": "forbidden"}), 403

    doc_ref.delete()
    return jsonify({"status": "deleted"})


# Widoki HTML
@app.route("/forecast")
def forecast_view():
    return render_template("forecast.html")

@app.route("/optimize")
def optimize_view():
    return render_template("optimize.html")

@app.route("/alerts")
def alerts_view():
    return render_template("alerts.html")

if __name__ == "__main__":
    app.run(debug=True)
