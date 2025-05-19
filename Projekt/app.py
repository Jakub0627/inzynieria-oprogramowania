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


# Inicjalizacja Firebase Admin SDK
cred = credentials.Certificate("firebase-adminsdk.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Wczytanie API key
load_dotenv()
CRYPTOCOMPARE_API_KEY = os.getenv("CRYPTOCOMPARE_API_KEY")

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

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/")
def dashboard():
    return render_template("dashboard.html")

# Dodawanie kryptowaluty
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

# Usuwanie częściowej ilości kryptowaluty
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

# Zwraca cały portfel użytkownika
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

# Wybór kryptowaluty do wykresu
@app.route("/chart", methods=["GET", "POST"])
def chart_redirect():
    if request.method == "POST":
        symbol = request.form.get("crypto").upper()
        return redirect(url_for("chart_view", symbol=symbol))
    return render_template("chart_form.html")

# Wykres cenowy z predykcją
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
        ax.fill_between(future_dates, conf_int[:, 0], conf_int[:, 1], color="lightblue", alpha=0.4, label="Przedział ufności")

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

    return render_template("chart.html", symbol=symbol, image_base64=image_base64)

# Strony pozostałe
@app.route("/api/optimize", methods=["POST"])
def api_optimize():
    uid = get_user_id()
    if not uid:
        return jsonify({"error": "unauthorized"}), 401

    docs = db.collection("portfolios").document(uid).collection("assets").stream()
    assets = {}
    for doc in docs:
        data = doc.to_dict()
        assets[doc.id] = data["price"], data["amount"]

    if not assets:
        return jsonify({"suggestions": ["Portfel jest pusty. Nie można przeprowadzić optymalizacji."]})

    # Pobierz historyczne dane
    historical_data = {}
    for symbol in assets:
        _, prices = Portfolio.get_historical_data(symbol, CRYPTOCOMPARE_API_KEY, limit=100)
        if not prices or len(prices) < 2:
            return jsonify({"suggestions": [f"Brak wystarczających danych dla {symbol}"]})
        historical_data[symbol] = prices

    # Optymalizacja Markowitza
    try:
        symbols = list(historical_data.keys())
        prices = np.array([historical_data[s] for s in symbols])
        returns = np.diff(prices, axis=1) / prices[:, :-1]
        mean_returns = np.mean(returns, axis=1)
        cov_matrix = np.cov(returns)

        def neg_return(weights): return -np.dot(weights, mean_returns)
        constraints = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}
        bounds = tuple((0, 1) for _ in symbols)
        initial = np.ones(len(symbols)) / len(symbols)

        result = minimize(neg_return, initial, bounds=bounds, constraints=constraints)
        if not result.success:
            raise Exception("Niepowodzenie optymalizacji")

        optimized_weights = result.x
        total_val = sum(assets[s][0] * assets[s][1] for s in symbols)
        suggestions = []
        for i, s in enumerate(symbols):
            current_val = assets[s][0] * assets[s][1]
            current_weight = current_val / total_val
            diff = optimized_weights[i] - current_weight
            if diff > 0.02:
                suggestions.append(f"Zwiększ udział {s} do {optimized_weights[i]*100:.2f}% (obecnie {current_weight*100:.2f}%).")
            elif diff < -0.02:
                suggestions.append(f"Zmniejsz udział {s} do {optimized_weights[i]*100:.2f}% (obecnie {current_weight*100:.2f}%).")

        if not suggestions:
            suggestions.append("Portfel jest zoptymalizowany zgodnie z modelem Markowitza.")

        return jsonify({"suggestions": suggestions})

    except Exception as e:
        return jsonify({"suggestions": [f"Błąd podczas optymalizacji: {str(e)}"]})


@app.route("/api/forecast")
def api_forecast():
    uid = get_user_id()
    if not uid:
        return jsonify({"error": "unauthorized"}), 401

    docs = db.collection("portfolios").document(uid).collection("assets").stream()
    total_value = 0
    for doc in docs:
        asset = doc.to_dict()
        total_value += asset["amount"] * asset["price"]

    forecast = []
    for days in [1, 7, 30]:
        predicted = total_value * (1 + 0.01 * days)
        forecast.append({
            "days": days,
            "value": predicted
        })

    return jsonify({"forecast": forecast})

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
