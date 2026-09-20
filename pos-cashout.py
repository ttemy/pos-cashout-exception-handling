"""
POS Agent Cash-Out — Exception Handling Assignment
Python Advanced Cohort 38

The machine must NEVER crash, no matter how broken a request is.
Every bad request is rejected with a clear reason and the queue moves on.
"""

import sys
from typing import Any

try:
    sys.stdout.reconfigure(encoding="utf-8")  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
except Exception:
    pass  


CASHOUT_REQUESTS: list[dict[str, Any]] = [  # pyright: ignore[reportExplicitAny]
    {"customer": "Chinedu Okafor", "phone": "08031234567", "amount": 5000,  "account_balance": 20000},
    {"customer": "Aisha Bello",    "phone": "07061234567", "amount": "five thousand", "account_balance": 15000},
    {"customer": "Emeka Nwosu",    "phone": "08101234567", "amount": 40000, "account_balance": 2000},
    {"customer": "Fatima Sani",    "phone": "09021234567", "amount": 2550,  "account_balance": 30000},
    {"customer": "Tunde Adeyemi",  "phone": "08051234567", "amount": 75000, "account_balance": 90000},
    {"customer": "Blessing Eze",   "phone": "07031234567", "amount": 10000, "account_balance": 50000},
    {"customer": "Unknown Customer","phone": "08099887766", "amount": 3000},  # <-- missing "account_balance"!
    {"customer": "Ibrahim Musa",   "phone": "08122334455", "amount": -3000, "account_balance": 10000},
    {"customer": "Ngozi Uche",     "phone": "09033445566", "amount": 0,     "account_balance": 8000},
]

NOTE_UNIT = 100
OPENING_FLOAT = 50000
DAILY_LIMIT = 100000       # stretch goal 1
LOW_FLOAT_WARNING = 10000  # stretch goal 2


# ---------------------------------------------------------------------------
# TODO 1: CUSTOM EXCEPTIONS
# ---------------------------------------------------------------------------
class TransactionError(Exception):
    """Base error for anything that goes wrong during a cash-out."""
    pass


class InsufficientFundsError(TransactionError):
    """Raised when a customer tries to withdraw more than their balance."""
    pass


class DailyLimitError(TransactionError):
    """Stretch goal: raised when a single cash-out exceeds DAILY_LIMIT."""
    pass


# ---------------------------------------------------------------------------
# TODO 2: VALIDATE THE AMOUNT
# ---------------------------------------------------------------------------
def validate_amount(amount: Any) -> int:  # pyright: ignore[reportAny, reportExplicitAny]
    """Convert `amount` to a clean int and make sure it is a valid cash-out."""
    # Step 1: conversion. float() (not int()) so that "5000", 5000 and "5000.0"
    # all work, and so that "2550.75" is caught below instead of being
    # silently truncated.
    try:
        number = float(amount)  # pyright: ignore[reportAny]
    except (ValueError, TypeError):
        raise TransactionError(f"amount {amount!r} is not a valid number.")

    # Step 2: must be a whole number. is_integer() is False for nan and inf
    # too, so those are rejected here as well.
    if not number.is_integer():
        raise TransactionError(f"amount {amount!r} must be a whole number of naira.")
    number = int(number)

    # Step 3: must be positive.
    if number <= 0:
        raise TransactionError(f"amount must be positive (got ₦{number:,}).")

    # Step 4: must be a multiple of the smallest note.
    if number % NOTE_UNIT != 0:
        raise TransactionError(
            f"amount must be a multiple of ₦{NOTE_UNIT} (got ₦{number:,})."
        )

    # Stretch goal 1: daily limit.
    if number > DAILY_LIMIT:
        raise DailyLimitError(
            f"₦{number:,} is above the ₦{DAILY_LIMIT:,} single cash-out limit."
        )

    return number


# ---------------------------------------------------------------------------
# TODO 3: CHECK THE CUSTOMER'S ACCOUNT BALANCE
# ---------------------------------------------------------------------------
def check_balance(amount: int, account_balance: float) -> None:
    if amount > account_balance:
        raise InsufficientFundsError(
            f"₦{amount:,} is more than the account balance of ₦{account_balance:,}."
        )


# ---------------------------------------------------------------------------
# TODO 4: CHECK THE AGENT'S FLOAT
# ---------------------------------------------------------------------------
def check_agent_float(amount: int, agent_float: int) -> None:
    if amount > agent_float:
        raise TransactionError(
            f"agent float too low — need ₦{amount:,} but only ₦{agent_float:,} available."
        )


# ---------------------------------------------------------------------------
# TODO 5: CHARGE THE POS FEE
# ---------------------------------------------------------------------------
def charge_fee(amount: int) -> int:
    return (amount // 5000) * 100


# ---------------------------------------------------------------------------
# TODO 6: PROCESS ONE CASH-OUT
# ---------------------------------------------------------------------------
def process_cashout(request: dict[str, Any], agent_float: int) -> int:  # pyright: ignore[reportExplicitAny]
    """Process one request safely. Returns the updated float (unchanged on failure)."""
    new_float = agent_float

    try:
        customer = request["customer"]  # pyright: ignore[reportAny]
        amount = validate_amount(request["amount"])
        balance = request["account_balance"]  # pyright: ignore[reportAny]
        check_balance(amount, balance)  # pyright: ignore[reportAny]
        check_agent_float(amount, agent_float)
    except TransactionError as error:
        print(f"❌ Rejected: {error}")
    except KeyError as missing:
        print(f"❌ Rejected: request is missing required information (KeyError: {missing}).")
    except Exception as unexpected:
        print(f"❌ Rejected: unexpected problem — {type(unexpected).__name__}: {unexpected}")
    else:
        fee = charge_fee(amount)
        new_float = agent_float - amount
        print(
            f"✅ Approved: ₦{amount:,} paid out to {customer} | "
            + f"Fee: ₦{fee:,} | Float left: ₦{new_float:,}"
        )
        # Stretch goal 2: low-float warning.
        if new_float < LOW_FLOAT_WARNING:
            print(f"⚠️  Warning: float is low (₦{new_float:,}). Time to top up!")
    finally:
        print("--- transaction ended ---")

    return new_float


# ---------------------------------------------------------------------------
# TODO 7: MAIN
# ---------------------------------------------------------------------------
def main() -> None:
    agent_float = OPENING_FLOAT

    print("====== MAMA NGOZI POS TERMINAL ======")
    print(f"Opening float: ₦{agent_float:,}")
    print()

    successes = 0
    failures = 0

    for request in CASHOUT_REQUESTS:
        name = request.get("customer", "Unknown")  # pyright: ignore[reportAny]
        phone = request.get("phone", "")  # pyright: ignore[reportAny]
        print(f"Processing cash-out for {name} ({phone})...")

        old_float = agent_float
        agent_float = process_cashout(request, agent_float)

        # A success always pays out a positive amount, so the float only
        # changes when the transaction was approved.
        if agent_float != old_float:
            successes += 1
        else:
            failures += 1
        print()

    print("============ END OF DAY ============")
    print(f"Successful cash-outs: {successes}")
    print(f"Failed cash-outs:     {failures}")
    print(f"Final float: ₦{agent_float:,}")


if __name__ == "__main__":
    main()