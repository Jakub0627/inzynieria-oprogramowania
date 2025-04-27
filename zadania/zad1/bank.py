'''
Treść zadania: (ZADANIE 1)

REQUIREMENTS:
The client requested the creation of a class that will manage funds deposited in a bank account.
Initially, the class should provide two operations:
1. Depositing new funds
2. Withdrawing the deposited funds

During implementation, additional requirements emerged:
1. Depositing funds will always be possible. The withdrawal operation may occur
   after preliminary identity verification of the client (e.g., identity document verification).
2. Another owner can close the account. Once the account is closed, no operations
   can be performed on it.
3. The account may be deactivated if no operation has been performed on it for a certain period.
4. The account may be reactivated upon the occurrence of an operation (deposit or withdrawal).
5. Reactivating the account will trigger an additional action (undefined), e.g., sending a message
   about the reactivation.

TASKS:
1. Prepare an implementation in accordance with the above requirements. The implementation should be
   done in an object-oriented programming language.
2. Develop tests for the created class: initial and final conditions. The tests should
   cover all execution paths.
3. Based on point 2, create unit tests for the implemented class.

'''

# bank.py
import datetime

class BankAccount:
    def __init__(self, initial_balance=0.0):
        self.balance = initial_balance                  # Current balance
        self.active = True                              # Active (True) vs deactivated (False)
        self.closed = False                             # Closed accounts cannot be reopened
        self.last_operation = datetime.datetime.now()   # Timestamp of last operation
        self.notifications = []                         # Store notification messages

    def _notify_reactivation(self):
        # Placeholder for reactivation notification
        msg = f"Account reactivated at {datetime.datetime.now()}"
        self.notifications.append(msg)

    def deposit(self, amount):
        # Reactivation logic: if account is deactivated but not closed
        if not self.active and not self.closed:
            self.active = True
            self._notify_reactivation()
        if self.closed:
            raise RuntimeError("Cannot perform operations on a closed account.")
        # Perform deposit
        self.balance += amount
        self.last_operation = datetime.datetime.now()

    def withdraw(self, amount, identity_verified=True):
        # Reactivation logic
        if not self.active and not self.closed:
            self.active = True
            self._notify_reactivation()
        if self.closed:
            raise RuntimeError("Cannot perform operations on a closed account.")
        if not identity_verified:
            raise PermissionError("Identity not verified. Withdrawal rejected.")
        if amount > self.balance:
            raise ValueError("Insufficient funds.")
        self.balance -= amount
        self.last_operation = datetime.datetime.now()

    def close(self):
        # Close account permanently
        self.closed = True
        self.active = False

    def check_inactivity_and_deactivate(self, inactivity_days=30):
        # Deactivate if inactive for a threshold
        if self.active and not self.closed:
            if (datetime.datetime.now() - self.last_operation).days >= inactivity_days:
                self.active = False
