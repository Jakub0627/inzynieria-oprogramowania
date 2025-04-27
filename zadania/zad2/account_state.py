'''Implementacja poprzedniego zadania ze wzorcem state.'''

import datetime

class AccountState:
    def deposit(self, account, amount):
        raise NotImplementedError()

    def withdraw(self, account, amount, identity_verified):
        raise NotImplementedError()

    def close(self, account):
        raise NotImplementedError()

    def check_inactivity(self, account, inactivity_days):
        raise NotImplementedError()


class ActiveState(AccountState):
    def deposit(self, account, amount):
        account.balance += amount
        account.last_operation = datetime.datetime.now()

    def withdraw(self, account, amount, identity_verified):
        if not identity_verified:
            raise PermissionError("Identity not verified. Withdrawal rejected.")
        if amount > account.balance:
            raise ValueError("Insufficient funds.")
        account.balance -= amount
        account.last_operation = datetime.datetime.now()

    def close(self, account):
        account.state = ClosedState()

    def check_inactivity(self, account, inactivity_days):
        if (datetime.datetime.now() - account.last_operation).days >= inactivity_days:
            account.state = InactiveState()


class InactiveState(AccountState):
    def deposit(self, account, amount):
        account.state = ActiveState()
        account._notify_reactivation()
        account.deposit(amount)

    def withdraw(self, account, amount, identity_verified):
        account.state = ActiveState()
        account._notify_reactivation()
        account.withdraw(amount, identity_verified)

    def close(self, account):
        account.state = ClosedState()

    def check_inactivity(self, account, inactivity_days):
        pass  # Already inactive


class ClosedState(AccountState):
    def deposit(self, account, amount):
        raise RuntimeError("Cannot perform operations on a closed account.")

    def withdraw(self, account, amount, identity_verified):
        raise RuntimeError("Cannot perform operations on a closed account.")

    def close(self, account):
        pass  # Already closed

    def check_inactivity(self, account, inactivity_days):
        pass  # Already closed


class Account:
    def __init__(self, initial_balance=0.0):
        self.balance = initial_balance
        self.last_operation = datetime.datetime.now()
        self.notifications = []
        self.state = ActiveState()

    def _notify_reactivation(self):
        msg = f"Account reactivated at {datetime.datetime.now()}"
        self.notifications.append(msg)

    def deposit(self, amount):
        self.state.deposit(self, amount)

    def withdraw(self, amount, identity_verified=True):
        self.state.withdraw(self, amount, identity_verified)

    def close(self):
        self.state.close(self)

    def check_inactivity_and_deactivate(self, inactivity_days=30):
        self.state.check_inactivity(self, inactivity_days)