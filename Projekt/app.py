from flask import Flask, render_template, request, redirect, url_for
from portfolio import Portfolio
import os
import io
from dotenv import load_dotenv
import base64
from matplotlib.figure import Figure
from flask import jsonify

load_dotenv()
CRYPTOCOMPARE_API_KEY = os.getenv("CRYPTOCOMPARE_API_KEY")

app = Flask(__name__)
portfolio = Portfolio()

@app.route("/", methods=["GET", "POST"])
def dashboard():
    crypto_list = Portfolio.get_crypto_list(CRYPTOCOMPARE_API_KEY)

    if request.method == "POST":
        symbol = request.form.get("crypto").upper()
        amount = float(request.form.get("amount"))
        price = Portfolio.get_current_price(symbol, CRYPTOCOMPARE_API_KEY)
        portfolio.add_asset(symbol, amount, price)
        return redirect(url_for("dashboard"))

    return render_template("dashboard.html", assets=portfolio.assets, total_value=portfolio.total_value, crypto_list=crypto_list)


@app.route("/delete/<symbol>", methods=["POST"])
def delete_asset(symbol):
    try:
        amount = float(request.form.get("amount"))
        portfolio.remove_asset(symbol.upper(), amount)
    except (ValueError, TypeError):
        pass
    return redirect(url_for("portfolio_view"))

@app.route("/portfolio")
def portfolio_view():
    return render_template("portfolio.html", assets=portfolio.assets, total_value=portfolio.total_value)

@app.route("/chart", methods=["GET", "POST"])
def chart_redirect():
    if request.method == "POST":
        symbol = request.form.get("crypto").upper()
        return redirect(url_for("chart_view", symbol=symbol))
    symbols_in_portfolio = [asset['crypto_name'] for asset in portfolio.assets]
    return render_template("chart_form.html", symbols=symbols_in_portfolio)


@app.route("/chart/<symbol>")
def chart_view(symbol):
    dates, prices = Portfolio.get_historical_data(symbol, CRYPTOCOMPARE_API_KEY, limit=30)
    if not prices:
        return f"Nie udało się pobrać danych dla {symbol}"

    fig = Figure()
    ax = fig.subplots()

    ax.plot(dates, prices, label="Cena", color="skyblue")

    # Średnia krocząca
    sma = Portfolio.calculate_moving_average(prices, window=7)
    ax.plot(dates, sma, label="SMA 7", linestyle="--", color="darkred")

    # Prognoza
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

    # Konwersja do Base64
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode("utf-8")
    buf.close()

    return render_template("chart.html", symbol=symbol, image_base64=image_base64)

@app.route("/optimize")
def optimize_view():
    suggestions = portfolio.optimize_portfolio()
    return render_template("optimize.html", suggestions=suggestions)

@app.route("/forecast")
def forecast_view():
    predicted = portfolio.predict_portfolio_value(days=30)

    forecast = []
    for days in [1, 7, 30]:
        if len(predicted) >= days:
            forecast.append({
                "days": days,
                "value": predicted[days - 1]
            })

    return render_template("forecast.html", forecast=forecast)

@app.route("/alerts", methods=["GET", "POST"])
def alerts_view():
    message = None
    if request.method == "POST":
        symbol = request.form.get("crypto").upper()
        try:
            threshold = float(request.form.get("threshold"))
            price = Portfolio.get_current_price(symbol, CRYPTOCOMPARE_API_KEY)
            if price > threshold:
                body = f"Cena {symbol} przekroczyła {threshold} USD i wynosi {price:.2f} USD."
                sent = Portfolio.send_email_alert(f"Alert cenowy: {symbol}", body)
                message = f"✅ {body} E-mail {'wysłany' if sent else 'nie wysłano'}."
            else:
                message = f"ℹ️ Cena {symbol} jest poniżej progu {threshold} USD (obecnie {price:.2f} USD)."
        except ValueError:
            message = "⚠️ Nieprawidłowy próg cenowy. Wprowadź liczbę."

    return render_template("alerts.html", message=message)


if __name__ == "__main__":
    app.run(debug=True)