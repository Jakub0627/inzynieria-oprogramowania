import unittest
from unittest.mock import patch, MagicMock
from portfolio import Portfolio
import numpy as np

class TestPortfolio(unittest.TestCase):

    def setUp(self):
        self.portfolio = Portfolio()
        self.portfolio.add_asset("BTC", 1, 50000)
        self.portfolio.add_asset("ETH", 2, 3000)

    def test_add_asset_existing(self):
        self.portfolio.add_asset("BTC", 1, 60000)
        btc = next(asset for asset in self.portfolio.assets if asset["crypto_name"] == "BTC")
        self.assertAlmostEqual(btc["amount"], 2)
        self.assertTrue(50000 < btc["price"] < 60000)

    def test_remove_asset_partial(self):
        self.portfolio.remove_asset("ETH", 1)
        eth = next(asset for asset in self.portfolio.assets if asset["crypto_name"] == "ETH")
        self.assertEqual(eth["amount"], 1)

    def test_remove_asset_full(self):
        self.portfolio.remove_asset("ETH")
        self.assertFalse(any(asset["crypto_name"] == "ETH" for asset in self.portfolio.assets))

    @patch("portfolio.Portfolio.get_current_price", return_value=60000)
    def test_update_prices(self, mock_price):
        self.portfolio.update_prices()
        for asset in self.portfolio.assets:
            self.assertEqual(asset["price"], 60000)

    def test_predict_portfolio_value(self):
        predicted = self.portfolio.predict_portfolio_value(3)
        self.assertEqual(len(predicted), 3)
        self.assertGreater(predicted[1], predicted[0])

    @patch("portfolio.Portfolio.get_historical_data")
    def test_optimize_portfolio(self, mock_hist):
        mock_hist.return_value = (
            [1]*100,
            np.linspace(100, 200, 101).tolist()
        )
        result = self.portfolio.optimize_portfolio()
        self.assertIsInstance(result, list)
        self.assertTrue(any("Zwiększ" in r or "Zmniejsz" in r for r in result) or "zoptymalizowany" in result[0])

    def test_calculate_moving_average(self):
        prices = list(range(10))
        ma = self.portfolio.calculate_moving_average(prices, window=3)
        self.assertEqual(len(ma), 10)
        self.assertAlmostEqual(ma[2], 1.0)
        self.assertTrue(np.isnan(ma[0]))

    @patch("portfolio.SARIMAX")
    def test_forecast_prices(self, mock_model):
        instance = MagicMock()
        forecast = MagicMock()
        forecast.predicted_mean = [1, 2, 3]
        forecast.conf_int.return_value = [[0.5, 1.5], [1.5, 2.5], [2.5, 3.5]]
        instance.fit.return_value.get_forecast.return_value = forecast
        mock_model.return_value = instance

        pred, conf = self.portfolio.forecast_prices([1, 2, 3, 4, 5])
        self.assertEqual(list(pred), [1, 2, 3])

    @patch("portfolio.smtplib.SMTP")
    def test_send_email_alert(self, mock_smtp):
        mock_smtp.return_value.__enter__.return_value.sendmail.return_value = True
        result = self.portfolio.send_email_alert("Test", "Body")
        self.assertTrue(result)

if __name__ == "__main__":
    unittest.main()