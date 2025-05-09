import requests
from statsmodels.tsa.statespace.sarimax import SARIMAX
import numpy as np
import datetime
from scipy.optimize import minimize
from dotenv import load_dotenv
import os

load_dotenv()
CRYPTOCOMPARE_API_KEY = os.getenv("CRYPTOCOMPARE_API_KEY")

class Portfolio:
    def __init__(self):
        self.assets = []
        self.total_value = 0

    def add_asset(self, crypto_name, amount, price):
        for asset in self.assets:
            if asset['crypto_name'] == crypto_name:
                total_amount = asset['amount'] + amount
                asset['price'] = ((asset['amount'] * asset['price']) + (amount * price)) / total_amount
                asset['amount'] = total_amount
                self.calculate_total_value()
                return
        self.assets.append({
            'crypto_name': crypto_name,
            'amount': amount,
            'price': price
        })
        self.calculate_total_value()

    def remove_asset(self, crypto_name, amount=None):
        updated_assets = []
        for asset in self.assets:
            if asset['crypto_name'] == crypto_name:
                if amount is None or amount >= asset['amount']:
                    continue
                else:
                    asset['amount'] -= amount
                    updated_assets.append(asset)
            else:
                updated_assets.append(asset)
        self.assets = updated_assets
        self.calculate_total_value()

    def calculate_total_value(self):
        self.total_value = sum(asset['amount'] * asset['price'] for asset in self.assets)

    def update_prices(self):
        for asset in self.assets:
            asset['price'] = Portfolio.get_current_price(asset['crypto_name'], CRYPTOCOMPARE_API_KEY)

    def predict_portfolio_value(self, days):
        total_value = self.total_value
        return list(map(lambda day: total_value * (1 + 0.01 * day), range(1, days + 1)))

    def optimize_portfolio(self):
        if not self.assets:
            return ["Portfel jest pusty. Nie można przeprowadzić optymalizacji."]

        historical_data = {}
        for asset in self.assets:
            dates, prices = Portfolio.get_historical_data(asset['crypto_name'], CRYPTOCOMPARE_API_KEY, limit=100)
            if not prices or len(prices) < 2:
                return [f"Brak wystarczających danych historycznych dla {asset['crypto_name']}."]
            historical_data[asset['crypto_name']] = prices

        if not historical_data:
            return ["Brak danych do optymalizacji."]

        try:
            optimized_weights = self.markowitz_optimization(historical_data)
            if optimized_weights is not None:
                suggestions = self.generate_markowitz_suggestions(optimized_weights)
            else:
                suggestions = ["Nie można zoptymalizować portfela. Błąd podczas obliczeń."]
        except Exception as e:
            suggestions = [f"Nie można zoptymalizować portfela. Błąd: {e}"]

        return suggestions

    def markowitz_optimization(self, historical_data):
        prices = np.array(list(historical_data.values()))
        returns = np.diff(prices, axis=1) / prices[:, :-1]
        mean_returns = np.array(list(map(np.mean, returns)))
        covariance_matrix = np.cov(returns)

        num_assets = len(self.assets)

        def neg_portfolio_return(weights):
            return -np.dot(weights.T, mean_returns)

        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
        bounds = tuple((0, 1) for _ in range(num_assets))
        initial_weights = np.array([1/num_assets] * num_assets)

        optimized_result = minimize(
            neg_portfolio_return,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        return optimized_result.x if optimized_result.success else None

    def generate_markowitz_suggestions(self, optimized_weights):
        suggestions = []
        for i, asset in enumerate(self.assets):
            current_weight = asset['amount'] * asset['price'] / self.total_value if self.total_value > 0 else 0
            optimized_weight = optimized_weights[i]
            difference = optimized_weight - current_weight
            if difference > 0.02:
                suggestions.append(
                    f"Zwiększ udział {asset['crypto_name']} do {optimized_weight * 100:.2f}% (z obecnych {current_weight * 100:.2f}%)."
                )
            elif difference < -0.02:
                suggestions.append(
                    f"Zmniejsz udział {asset['crypto_name']} do {optimized_weight * 100:.2f}% (z obecnych {current_weight * 100:.2f}%)."
                )
        if not suggestions:
            suggestions.append("Portfel jest zoptymalizowany zgodnie z modelem Markowitza.")
        return suggestions

    @staticmethod
    def get_crypto_list(api_key):
        url = 'https://min-api.cryptocompare.com/data/all/coinlist'
        try:
            response = requests.get(url, params={'api_key': api_key})
            response.raise_for_status()
            data = response.json()
            return sorted(coin['Symbol'] for coin in data['Data'].values())
        except requests.exceptions.RequestException:
            return []

    @staticmethod
    def get_current_price(symbol, api_key):
        url = 'https://min-api.cryptocompare.com/data/price'
        params = {'fsym': symbol, 'tsyms': 'USD', 'api_key': api_key}
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json().get('USD', 0)
        except requests.exceptions.RequestException:
            return 0

    @staticmethod
    def get_historical_data(symbol, api_key, limit=30):
        url = 'https://min-api.cryptocompare.com/data/v2/histoday'
        params = {'fsym': symbol, 'tsym': 'USD', 'limit': limit, 'api_key': api_key}
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json().get('Data', {}).get('Data', [])
            dates = [datetime.datetime.fromtimestamp(item['time']) for item in data]
            prices = [item['close'] for item in data]
            return dates, prices
        except requests.exceptions.RequestException:
            return [], []

    @staticmethod
    def forecast_prices(prices, days=7):
        try:
            model = SARIMAX(prices, order=(1, 1, 1), seasonal_order=(1, 1, 1, 7), enforce_stationarity=False,
                            enforce_invertibility=False)
            model_fit = model.fit(disp=False)
            forecast = model_fit.get_forecast(steps=days)
            predicted_mean = forecast.predicted_mean
            conf_int = forecast.conf_int()
            return predicted_mean, conf_int
        except Exception:
            return None, None

    @staticmethod
    def calculate_moving_average(prices, window=7):
        if len(prices) < window:
            return [np.nan] * len(prices)
        moving_average = np.convolve(prices, np.ones(window), 'valid') / window
        padding = [np.nan] * (window - 1)
        return padding + list(moving_average)
