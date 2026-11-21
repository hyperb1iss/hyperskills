# Multi-currency accounts and month-end revaluation

We now hold a euro bank account and some customers pay into it, so the ledger needs accounts in currencies other than USD. Invoicing stays in USD for now.

Accounts get a currency. Assets and liabilities may be held in EUR, GBP, CHF, or JPY; income, expense, and equity stay in USD. Every line now stores its amount in the account's currency plus the USD amount it was booked at, converted at the rate in effect on the posting date (`ledger/fx.py`). An entry must balance in USD, and also in its own currency when all of its lines share one. The rounding left over from converting each line goes to a new conversion rounding account. Reversals reuse the original USD amounts, so a reversed entry nets to zero in both currencies.

Closing a period now revalues every foreign-currency balance at the closing rate treasury records (`record_rate`) for the period end. The difference goes to the exchange gain or loss account before the period locks, and the close records which entry it posted.

Bank imports read amounts in the bank account's currency and require a clearing account in the same currency. Statement references are only unique within one bank feed, and the euro feed reuses the operating feed's numbering, so import keys are now scoped to the feed. A row with no rate for its date is reported like any other rejected row.

Migration 0003 backfills the currency and USD amounts for existing accounts and lines, rewrites existing import keys into the per-feed form, and creates the gain, loss, and rounding accounts, stopping if one of those codes is already used for a different kind of account. Run `ledger BOOKS migrate` before the first import after deploying.
