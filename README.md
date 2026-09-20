# 💳 POS Agent Cash-Out: A Terminal That Never Crashes

A Python simulation of a neighbourhood POS (agent-banking) machine in Nigeria. It works through a queue of cash-out requests, approves the valid ones, and rejects the broken ones with a clear reason, without ever crashing.

Built for the Python Advanced Cohort 38 exception-handling assignment. Pure standard library: no files, no regex, no network, no dependencies.

---

## The problem

A POS agent (Mama Ngozi, in the scenario) loads a cash **float** into her machine each morning. Customers then withdraw from their bank accounts. Real requests are messy:

- an amount typed as `"five thousand"`
- a ₦0 or negative amount
- a withdrawal larger than the customer's balance
- a withdrawal larger than the cash the machine physically holds
- an amount the machine cannot dispense (₦2,550 with ₦100 as the smallest note)
- a request that arrives with a field missing

If the software crashes on any of these, the whole queue stops. The requirement is that every bad request is rejected with a human-readable reason and the machine moves on.

---

## How it works

| Function | Responsibility |
| --- | --- |
| `validate_amount()` | Converts input to a clean `int`. Rejects non-numbers, fractions, zero/negative values, non-multiples of ₦100, and amounts above the ₦100,000 limit. |
| `check_balance()` | Raises `InsufficientFundsError` if the customer is asking for more than they have. |
| `check_agent_float()` | Raises `TransactionError` if the machine doesn't hold enough cash. |
| `charge_fee()` | ₦100 per full ₦5,000, using integer division (`//`), so there are no kobo or decimals. |
| `process_cashout()` | Orchestrates everything in `try` / `except` / `else` / `finally`. Returns the new float, or the unchanged float on failure. |
| `main()` | Runs the day: starts at ₦50,000, tallies successes and failures, prints a summary. |

### Exception hierarchy

```
Exception
└── TransactionError
    ├── InsufficientFundsError
    └── DailyLimitError        (stretch goal)
```

`InsufficientFundsError` and `DailyLimitError` are subclasses of `TransactionError`, so one `except TransactionError` block handles all business-rule failures. A more specific handler can still be added later without touching the existing one.

### Structure of `process_cashout`

```python
try:
    customer = request["customer"]
    amount = validate_amount(request["amount"])
    balance = request["account_balance"]        # missing key -> KeyError
    check_balance(amount, balance)
    check_agent_float(amount, agent_float)
except TransactionError as error:               # business-rule failures
    ...
except KeyError as missing:                     # incomplete request
    ...
except Exception as unexpected:                 # last-resort safety net
    ...
else:                                           # only runs if nothing failed
    ...approve, charge fee, reduce float...
finally:                                        # always runs
    print("--- transaction ended ---")
```

Success logic lives in `else`, not at the end of `try`. That way an error inside the approval code can't be mistaken for a validation failure. The generic `except Exception` comes last, because Python matches handlers top to bottom.

---

## Design decisions

**`float()` then a whole-number check, instead of `int()`.**
`int("2550.75")` raises an error, but `int(2550.75)` silently truncates to `2550`. In a cash system, quietly changing the amount is worse than rejecting it. Converting with `float()` and then requiring `.is_integer()` accepts `"5000"`, `5000` and `"5000.0"`, and rejects `"5000.5"`. `nan` and `inf` fail the same check.

**A safety net that gets used.**
A customer balance that arrives as a string (`"lots"`) isn't a `KeyError` or a `TransactionError`. It raises a `TypeError` at the comparison. The generic `except Exception` handles it, so the queue continues.

**`finally` for the "transaction ended" line.**
It runs on success, on rejection and on unexpected errors, so every request gets a clean closing line.

---

## Sample run

The queue includes deliberately broken entries.

```
====== MAMA NGOZI POS TERMINAL ======
Opening float: ₦50,000

Processing cash-out for Chinedu Okafor (08031234567)...
✅ Approved: ₦5,000 paid out to Chinedu Okafor | Fee: ₦100 | Float left: ₦45,000
--- transaction ended ---

Processing cash-out for Aisha Bello (07061234567)...
❌ Rejected: amount 'five thousand' is not a valid number.
--- transaction ended ---

Processing cash-out for Emeka Nwosu (08101234567)...
❌ Rejected: ₦40,000 is more than the account balance of ₦2,000.
--- transaction ended ---

Processing cash-out for Fatima Sani (09021234567)...
❌ Rejected: amount must be a multiple of ₦100 (got ₦2,550).
--- transaction ended ---

Processing cash-out for Tunde Adeyemi (08051234567)...
❌ Rejected: agent float too low — need ₦75,000 but only ₦45,000 available.
--- transaction ended ---

Processing cash-out for Blessing Eze (07031234567)...
✅ Approved: ₦10,000 paid out to Blessing Eze | Fee: ₦200 | Float left: ₦35,000
--- transaction ended ---

Processing cash-out for Unknown Customer (08099887766)...
❌ Rejected: request is missing required information (KeyError: 'account_balance').
--- transaction ended ---

Processing cash-out for Ibrahim Musa (08122334455)...
❌ Rejected: amount must be positive (got ₦-3,000).
--- transaction ended ---

Processing cash-out for Ngozi Uche (09033445566)...
❌ Rejected: amount must be positive (got ₦0).
--- transaction ended ---

============ END OF DAY ============
Successful cash-outs: 2
Failed cash-outs:     7
Final float: ₦35,000
```

---

## Testing beyond the sample data

Extra inputs I ran against the code to check it survives:

| Input | Result |
| --- | --- |
| `"5000"` (digit string) | Accepted as `5000` |
| `"5000.5"` | Rejected: must be a whole number |
| `nan`, `"inf"` | Rejected: must be a whole number |
| `None`, `[1]` | Rejected: not a valid number |
| `150000` | Rejected: above the ₦100,000 limit |
| Balance is the string `"lots"` | Caught by the generic `Exception` handler |
| Request is `None` | Caught by the generic `Exception` handler |

Note that `True` passes float conversion as `1.0`, so it is rejected only because 1 isn't a multiple of ₦100. That is correct behaviour, but for the wrong reason. A stricter version would reject booleans explicitly.

---

## Stretch goals implemented

- **Daily limit:** `DailyLimitError` fires above ₦100,000 per cash-out.
- **Low-float warning:** a ⚠️ warning prints when the float drops below ₦10,000.
- **String amounts:** `"5000"` is accepted; `"five thousand"` is still rejected.

---

## Known limitations

- **Success is detected by "the float changed".** This works because an approved amount is always positive, but it is indirect. Returning `(new_float, success)` would be more robust; I kept the signature the assignment specifies.
- **The POS fee is calculated and displayed, but not deducted** from the customer or added to the agent's earnings. This follows the spec, but a real system would need to handle it.
- **`account_balance` isn't validated** the way `amount` is. A non-numeric balance is only caught by the generic handler.
- **Amounts are plain `int`s.** A real system would use `Decimal` or integer kobo.

---

## Running it

```bash
python pos-cashout.py
```

Requires Python 3.7 or later (the code uses `sys.stdout.reconfigure`, guarded for older versions). The `₦` symbol needs a UTF-8 terminal; the script switches stdout to UTF-8 where it can.

---

## What this project demonstrates

- `try` / `except` / `else` / `finally` used correctly, with specific handlers before the generic one
- Custom exception hierarchies that model business rules
- Defensive input validation that treats all input as untrusted
- Fail-safe design: a failed transaction leaves state (the float) exactly as it was
- Testing edge cases beyond the provided data

---

**Author:** Emediong Kevin Etim