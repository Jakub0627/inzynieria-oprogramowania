import unittest
from unittest.mock import patch, MagicMock
from app import app as flask_app
import numpy as np

class TestAPI(unittest.TestCase):

    def setUp(self):
        flask_app.config["TESTING"] = True
        self.client = flask_app.test_client()

        patcher_auth = patch("firebase_admin.auth.verify_id_token", return_value={"uid": "mocked_user"})
        self.mock_verify_token = patcher_auth.start()
        self.addCleanup(patcher_auth.stop)

        self.mock_db = MagicMock()
        patcher_db = patch("app.db", self.mock_db)
        patcher_db.start()
        self.addCleanup(patcher_db.stop)

    def test_add_crypto_mocked(self):
        mock_assets = (
            self.mock_db
            .collection.return_value
            .document.return_value
            .collection.return_value
            .document.return_value
        )
        mock_assets.get.return_value.exists = False

        response = self.client.post(
            "/api/add",
            headers={"Authorization": "Bearer test"},
            json={"crypto": "BTC", "amount": 0.01}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "added")

    def test_alert_creation_mocked(self):
        alerts_collection = self.mock_db.collection.return_value
        alerts_collection.add.return_value = ("mocked_doc", None)

        response = self.client.post(
            "/api/alerts",
            headers={"Authorization": "Bearer test"},
            json={"symbol": "ETH", "threshold": 12345}
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["status"], "added")

    def test_forecast_mocked(self):
        asset_mock = MagicMock()
        asset_mock.to_dict.return_value = {"amount": 1, "price": 1000}

        self.mock_db.collection.return_value.document.return_value.collection.return_value.stream.return_value = [asset_mock]

        response = self.client.get("/api/forecast", headers={"Authorization": "Bearer test"})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("forecast", data)
        self.assertEqual(len(data["forecast"]), 3)

    def test_optimize_empty_mocked(self):
        self.mock_db.collection.return_value.document.return_value.collection.return_value.stream.return_value = []

        response = self.client.post("/api/optimize", headers={"Authorization": "Bearer test"})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("suggestions", data)

    def test_delete_crypto_partial(self):
        symbol = "BTC"
        mock_doc = (
            self.mock_db
            .collection.return_value
            .document.return_value
            .collection.return_value
            .document.return_value
        )
        mock_doc.get.return_value.exists = True
        mock_doc.get.return_value.to_dict.return_value = {"amount": 1.0, "price": 10000}

        response = self.client.delete(
            f"/api/delete/{symbol}",
            headers={"Authorization": "Bearer test"},
            json={"amount": 0.5}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "updated")

    def test_get_alerts_list(self):
        mock_alert = MagicMock()
        mock_alert.id = "alert123"
        mock_alert.to_dict.return_value = {
            "symbol": "ETH",
            "threshold": 1234,
            "sent": False,
            "timestamp": {"seconds": 1234567890}
        }
        self.mock_db.collection.return_value.where.return_value.order_by.return_value.stream.return_value = [mock_alert]

        response = self.client.get("/api/alerts", headers={"Authorization": "Bearer test"})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("alerts", data)
        self.assertEqual(data["alerts"][0]["id"], "alert123")

    def test_delete_alert(self):
        alert_id = "mock_alert"
        alert_doc = MagicMock()
        alert_doc.exists = True
        alert_doc.to_dict.return_value = {"uid": "mocked_user"}

        self.mock_db.collection.return_value.document.return_value.get.return_value = alert_doc

        response = self.client.delete(f"/api/alerts/{alert_id}", headers={"Authorization": "Bearer test"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "deleted")

    def test_get_portfolio(self):
        mock_asset = MagicMock()
        mock_asset.id = "BTC"
        mock_asset.to_dict.return_value = {"amount": 1.5, "price": 30000}

        self.mock_db.collection.return_value.document.return_value.collection.return_value.stream.return_value = [
            mock_asset]

        response = self.client.get("/api/portfolio", headers={"Authorization": "Bearer test"})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("assets", data)
        self.assertEqual(data["assets"][0]["crypto_name"], "BTC")

    @patch("portfolio.Portfolio.get_historical_data")
    @patch("portfolio.Portfolio.calculate_moving_average", return_value=[1] * 30)
    @patch("portfolio.Portfolio.forecast_prices", return_value=([10] * 7, np.array([[8, 12]] * 7)))
    def test_chart_symbol_view(self, mock_forecast, mock_sma, mock_hist):
        mock_hist.return_value = ([1] * 30, [100 + i for i in range(30)])

        response = self.client.get("/chart/BTC", headers={"Authorization": "Bearer test"})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("image_base64", data)
        self.assertEqual(data["symbol"], "BTC")

if __name__ == "__main__":
    unittest.main()
