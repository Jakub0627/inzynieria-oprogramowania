import unittest
from unittest.mock import patch, MagicMock
from app import app as flask_app

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

if __name__ == "__main__":
    unittest.main()
