'''python -m unittest tests/test_bank.py'''
import datetime
import unittest
from zad1.bank import BankAccount

class TestBankAccount(unittest.TestCase):

    def test_initial_balance(self):
        account = BankAccount(initial_balance=100.0)
        self.assertEqual(account.balance, 100.0)
        self.assertTrue(account.active)

    def test_deposit_increases_balance(self):
        account = BankAccount(initial_balance=50.0)
        account.deposit(25.0)
        self.assertEqual(account.balance, 75.0)

    def test_withdraw_valid(self):
        account = BankAccount(initial_balance=80.0)
        account.withdraw(30.0, identity_verified=True)
        self.assertEqual(account.balance, 50.0)

    def test_withdraw_without_identity(self):
        account = BankAccount(initial_balance=80.0)
        with self.assertRaises(PermissionError):
            account.withdraw(30.0, identity_verified=False)

    def test_withdraw_insufficient_funds(self):
        account = BankAccount(initial_balance=40.0)
        with self.assertRaises(ValueError):
            account.withdraw(50.0, identity_verified=True)

    def test_close_account_prevents_deposit(self):
        account = BankAccount(initial_balance=100.0)
        account.close()
        with self.assertRaises(RuntimeError):
            account.deposit(20.0)

    def test_close_account_prevents_withdraw(self):
        account = BankAccount(initial_balance=100.0)
        account.close()
        with self.assertRaises(RuntimeError):
            account.withdraw(20.0, identity_verified=True)

    def test_inactivity_deactivates_account(self):
        account = BankAccount(initial_balance=100.0)
        account.last_operation = datetime.datetime.now() - datetime.timedelta(days=31)
        account.check_inactivity_and_deactivate(inactivity_days=30)
        self.assertFalse(account.active)

    def test_deposit_reactivates_and_notifies(self):
        account = BankAccount(initial_balance=50.0)
        account.active = False
        account.deposit(10.0)
        self.assertTrue(account.active)
        self.assertEqual(len(account.notifications), 1)
        self.assertIn("Account reactivated at", account.notifications[0])

    def test_withdraw_reactivates_and_notifies(self):
        account = BankAccount(initial_balance=100.0)
        account.active = False
        account.withdraw(20.0, identity_verified=True)
        self.assertTrue(account.active)
        self.assertEqual(len(account.notifications), 1)
        self.assertIn("Account reactivated at", account.notifications[0])

    def test_reactivation_updates_last_operation(self):
        account = BankAccount(initial_balance=30.0)
        account.active = False
        old = account.last_operation
        account.deposit(5.0)
        new = account.last_operation
        self.assertGreater(new, old)

if __name__ == '__main__':
    unittest.main()