# Receivables & Payables (`mv_cash_radar`)

A colour-coded dashboard inside the Odoo **Invoicing** app that makes "money to
collect" and "money going out" impossible to miss, plus an optional daily email
digest and in-app activity reminder.

- **Odoo:** 19.0 Community
- **License:** MIT
- **Author:** MontVeritas Partners LLC

## What it does

Adds a **Receivables & Payables** header inside the Invoicing app (alongside
Customers / Vendors / Reporting) showing five live, clickable cards:

**Receivables — money coming in (green)**
- Ready to Invoice — confirmed sales orders not yet billed
- Awaiting Payment — posted customer invoices, not yet due
- Overdue Receivables — past due (red, pulsing)

**Payables — money going out (amber)**
- Bills Due Soon — vendor bills due within N days
- Overdue Bills — past due (red, pulsing)

Each card shows the total amount and count, links through to the filtered list,
and previews the top records. Direction is encoded by colour (green = in,
amber = out); anything overdue turns red and pulses.

## Daily digest (optional)

A scheduled action runs once a day (07:00 server time by default) and:

- emails a colour-coded summary to the configured recipients, and
- drops one self-deduplicating to-do activity in each recipient's Odoo inbox.

The digest email only sends if recipients are configured (see below). The
dashboard and in-app activity work regardless. For email delivery, configure an
outgoing mail server in **Settings → Technical → Outgoing Mail Servers**.

## Configuration

No code changes needed — tune via **Settings → Technical → System Parameters**:

| Parameter | Default | Meaning |
|---|---|---|
| `mv_cash_radar.due_soon_days` | `7` | Lookahead window for "Bills Due Soon" |
| `mv_cash_radar.digest_recipients` | _(empty)_ | Comma-separated emails for the daily digest |

## Notes

- **Alert-only** — it never creates, sends, or pays anything automatically.
- Adds **no inheritance** to native views and all styling is scoped to its own
  screen, so nothing else in Odoo changes appearance.
- Amounts are summed in the company currency (residual amount for invoices/bills,
  amount-to-invoice for sales orders). Mixed-currency totals are summed as-is.

## Install

Drop the module into your addons path and install **Receivables & Payables**
from the Apps list (or `-i mv_cash_radar` on the command line).
