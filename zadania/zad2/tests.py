import datetime
import unittest
from account_state import Account, ActiveState, InactiveState, ClosedState

class TestAccount(unittest.TestCase):

    def test_initial_balance(self):
        account = Account(initial_balance=100.0)
        self.assertEqual(account.balance, 100.0)
        self.assertIsInstance(account.state, ActiveState)

    def test_deposit_increases_balance(self):
        account = Account(initial_balance=50.0)
        account.deposit(25.0)
        self.assertEqual(account.balance, 75.0)

    def test_withdraw_valid(self):
        account = Account(initial_balance=80.0)
        account.withdraw(30.0, identity_verified=True)
        self.assertEqual(account.balance, 50.0)

    def test_withdraw_without_identity(self):
        account = Account(initial_balance=80.0)
        with self.assertRaises(PermissionError):
            account.withdraw(30.0, identity_verified=False)

    def test_withdraw_insufficient_funds(self):
        account = Account(initial_balance=40.0)
        with self.assertRaises(ValueError):
            account.withdraw(50.0, identity_verified=True)

    def test_close_account(self):
        account = Account(initial_balance=100.0)
        account.close()
        self.assertIsInstance(account.state, ClosedState)
        with self.assertRaises(RuntimeError):
            account.deposit(20.0)

    def test_inactivity_deactivates_account(self):
        account = Account(initial_balance=100.0)
        account.last_operation = datetime.datetime.now() - datetime.timedelta(days=31)
        account.check_inactivity_and_deactivate(inactivity_days=30)
        self.assertIsInstance(account.state, InactiveState)

    def test_deposit_reactivates_account(self):
        account = Account(initial_balance=50.0)
        account.state = InactiveState()
        account.deposit(10.0)
        self.assertIsInstance(account.state, ActiveState)
        self.assertEqual(len(account.notifications), 1)

    def test_withdraw_reactivates_account(self):
        account = Account(initial_balance=100.0)
        account.state = InactiveState()
        account.withdraw(20.0, identity_verified=True)
        self.assertIsInstance(account.state, ActiveState)
        self.assertEqual(len(account.notifications), 1)

if __name__ == '__main__':
    unittest.main()
