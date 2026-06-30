from datetime import timedelta

from odoo import api, fields, models

# Default lookahead for the "Bills Due Soon" bucket. Overridable per-DB via the
# ir.config_parameter "mv_cash_radar.due_soon_days".
DEFAULT_DUE_SOON_DAYS = 7
# Where the daily digest email goes. Empty by default: set the recipient(s) via
# the ir.config_parameter "mv_cash_radar.digest_recipients" (comma-separated).
# With no recipients configured, the dashboard and in-app activity still work;
# only the digest email is skipped.
DEFAULT_RECIPIENTS = ""

# Direction is encoded as a colour family in the UI: incoming = green/teal,
# outgoing = amber. A red flag is layered on top when a bucket is overdue.
INCOMING = "in"
OUTGOING = "out"


class MvCashRadar(models.AbstractModel):
    """Read-only aggregator powering the Cash Radar dashboard and daily digest.

    Abstract on purpose: it owns no records, it only reads sale.order and
    account.move and rolls them into five buckets. The same buckets feed both
    the OWL dashboard (get_dashboard_data) and the cron digest
    (_cron_send_digest), so the screen and the email can never disagree.
    """

    _name = "mv.cash.radar"
    _description = "Cash Radar - Money In / Out Aggregator"

    # ------------------------------------------------------------------
    # Config helpers
    # ------------------------------------------------------------------
    @api.model
    def _due_soon_days(self):
        param = self.env["ir.config_parameter"].sudo().get_param(
            "mv_cash_radar.due_soon_days"
        )
        try:
            return int(param) if param else DEFAULT_DUE_SOON_DAYS
        except (TypeError, ValueError):
            return DEFAULT_DUE_SOON_DAYS

    @api.model
    def _digest_recipients(self):
        param = self.env["ir.config_parameter"].sudo().get_param(
            "mv_cash_radar.digest_recipients"
        )
        return (param or DEFAULT_RECIPIENTS).strip()

    # ------------------------------------------------------------------
    # Bucket domains — single source of truth for both the cards and the
    # list views opened when a card is clicked.
    # ------------------------------------------------------------------
    @api.model
    def _bucket_domains(self):
        today = fields.Date.context_today(self)
        due_soon = today + timedelta(days=self._due_soon_days())
        open_states = ["not_paid", "partial"]

        return {
            # --- INCOMING: money owed to us ---------------------------------
            "to_invoice": {
                "model": "sale.order",
                "domain": [
                    ("invoice_status", "=", "to invoice"),
                    ("state", "=", "sale"),
                ],
                "direction": INCOMING,
                "overdue": False,
                "label": "Ready to Invoice",
                "subtitle": "Delivered / confirmed orders not yet billed",
                "icon": "fa-file-text-o",
                "date_field": "date_order",
            },
            "awaiting_payment": {
                "model": "account.move",
                "domain": [
                    ("move_type", "=", "out_invoice"),
                    ("state", "=", "posted"),
                    ("payment_state", "in", open_states),
                    ("invoice_date_due", ">=", today),
                ],
                "direction": INCOMING,
                "overdue": False,
                "label": "Awaiting Payment",
                "subtitle": "Invoices sent, not yet due",
                "icon": "fa-hourglass-half",
                "date_field": "invoice_date_due",
            },
            "overdue_receivables": {
                "model": "account.move",
                "domain": [
                    ("move_type", "=", "out_invoice"),
                    ("state", "=", "posted"),
                    ("payment_state", "in", open_states),
                    ("invoice_date_due", "<", today),
                ],
                "direction": INCOMING,
                "overdue": True,
                "label": "OVERDUE Receivables",
                "subtitle": "Past due — go collect",
                "icon": "fa-exclamation-triangle",
                "date_field": "invoice_date_due",
            },
            # --- OUTGOING: money we owe -------------------------------------
            "bills_due_soon": {
                "model": "account.move",
                "domain": [
                    ("move_type", "=", "in_invoice"),
                    ("state", "=", "posted"),
                    ("payment_state", "in", open_states),
                    ("invoice_date_due", ">=", today),
                    ("invoice_date_due", "<=", due_soon),
                ],
                "direction": OUTGOING,
                "overdue": False,
                "label": "Bills Due Soon",
                "subtitle": "Vendor bills due within %s days" % self._due_soon_days(),
                "icon": "fa-calendar",
                "date_field": "invoice_date_due",
            },
            "overdue_bills": {
                "model": "account.move",
                "domain": [
                    ("move_type", "=", "in_invoice"),
                    ("state", "=", "posted"),
                    ("payment_state", "in", open_states),
                    ("invoice_date_due", "<", today),
                ],
                "direction": OUTGOING,
                "overdue": True,
                "label": "OVERDUE Bills",
                "subtitle": "Past due — pay these",
                "icon": "fa-exclamation-triangle",
                "date_field": "invoice_date_due",
            },
        }

    # Order the cards appear in, grouped by direction.
    _CARD_ORDER = [
        "to_invoice",
        "awaiting_payment",
        "overdue_receivables",
        "bills_due_soon",
        "overdue_bills",
    ]

    @api.model
    def _amount_field(self, model):
        """Pick the best monetary field per model, defensively.

        sale.order exposes ``amount_to_invoice`` on recent versions; if it is
        absent we fall back to ``amount_total``. account.move always has
        ``amount_residual`` (the still-open amount).
        """
        if model == "sale.order":
            fld = self.env["sale.order"]._fields
            return "amount_to_invoice" if "amount_to_invoice" in fld else "amount_total"
        return "amount_residual"

    # ------------------------------------------------------------------
    # Aggregation
    # ------------------------------------------------------------------
    @api.model
    def _compute_bucket(self, key, spec, preview_limit=6):
        Model = self.env[spec["model"]]
        amount_field = self._amount_field(spec["model"])
        date_field = spec["date_field"]

        records = Model.search(spec["domain"], order="%s asc" % date_field)
        total = sum(records.mapped(amount_field)) if records else 0.0

        preview = []
        for rec in records[:preview_limit]:
            partner = rec.partner_id
            preview.append({
                "id": rec.id,
                "name": rec.display_name,
                "partner": partner.display_name if partner else "",
                "amount": rec[amount_field],
                "date": rec[date_field] and fields.Date.to_string(rec[date_field]) or "",
            })

        return {
            "key": key,
            "label": spec["label"],
            "subtitle": spec["subtitle"],
            "icon": spec["icon"],
            "direction": spec["direction"],
            "overdue": spec["overdue"],
            "model": spec["model"],
            "domain": spec["domain"],
            "count": len(records),
            "total": total,
            "records": preview,
        }

    @api.model
    def get_dashboard_data(self):
        """Public entry point for the OWL dashboard (called over RPC)."""
        specs = self._bucket_domains()
        currency = self.env.company.currency_id
        buckets = [
            self._compute_bucket(key, specs[key]) for key in self._CARD_ORDER
        ]
        return {
            "buckets": buckets,
            "currency": {
                "symbol": currency.symbol or "",
                "position": currency.position or "before",
            },
            "company": self.env.company.display_name,
        }

    # ------------------------------------------------------------------
    # The "nag": daily digest email + one in-app activity
    # ------------------------------------------------------------------
    def _format_money(self, amount):
        currency = self.env.company.currency_id
        # Group thousands with commas, matching the branded PDF money format.
        body = "{:,.2f}".format(amount or 0.0)
        if currency.position == "after":
            return "%s %s" % (body, currency.symbol or "")
        return "%s%s" % (currency.symbol or "", body)

    @api.model
    def _build_digest_html(self, data):
        rows = []
        for b in data["buckets"]:
            if not b["count"]:
                continue
            if b["overdue"]:
                colour, weight = "#c0392b", "bold"  # red flag
            elif b["direction"] == INCOMING:
                colour, weight = "#1e8449", "normal"  # green = incoming
            else:
                colour, weight = "#b9770e", "normal"  # amber = outgoing
            rows.append(
                "<tr>"
                "<td style='padding:8px 12px;font-weight:%s;color:%s;'>%s</td>"
                "<td style='padding:8px 12px;text-align:center;'>%s</td>"
                "<td style='padding:8px 12px;text-align:right;font-weight:%s;color:%s;'>%s</td>"
                "</tr>" % (
                    weight, colour, b["label"],
                    b["count"],
                    weight, colour, self._format_money(b["total"]),
                )
            )

        if not rows:
            body = "<p>All clear — nothing to invoice, collect, or pay right now. ✅</p>"
        else:
            body = (
                "<table style='border-collapse:collapse;width:100%;max-width:520px;'>"
                "<thead><tr style='background:#1A6FBF;color:#fff;'>"
                "<th style='padding:8px 12px;text-align:left;'>Bucket</th>"
                "<th style='padding:8px 12px;'>Count</th>"
                "<th style='padding:8px 12px;text-align:right;'>Amount</th>"
                "</tr></thead><tbody>" + "".join(rows) + "</tbody></table>"
            )

        return (
            "<div style='font-family:Arial,Helvetica,sans-serif;color:#222;'>"
            "<h2 style='margin:0 0 4px;'>Receivables &amp; Payables — %s</h2>"
            "<p style='color:#666;margin:0 0 16px;'>Money to collect (green) and money going out (amber).</p>"
            "%s"
            "<p style='margin-top:16px;color:#888;font-size:12px;'>"
            "Open <b>Invoicing &gt; Receivables &amp; Payables</b> in Odoo for the full clickable view.</p>"
            "</div>" % (data["company"], body)
        )

    @api.model
    def _digest_subject(self, data):
        overdue_recv = next(b for b in data["buckets"] if b["key"] == "overdue_receivables")
        to_invoice = next(b for b in data["buckets"] if b["key"] == "to_invoice")
        bits = []
        if overdue_recv["count"]:
            bits.append("%s OVERDUE in" % overdue_recv["count"])
        if to_invoice["count"]:
            bits.append("%s to invoice" % to_invoice["count"])
        tail = (" — " + ", ".join(bits)) if bits else " — all clear"
        return "Receivables & Payables%s" % tail

    @api.model
    def _post_digest_activity(self, data):
        """Drop one self-deduplicating To-Do activity in the recipient's bell.

        We remove any prior auto-created Cash Radar activity first so the user
        sees today's snapshot, not a growing pile.
        """
        users = self.env["res.users"].search([
            ("login", "in", [r.strip() for r in self._digest_recipients().split(",")]),
        ])
        if not users:
            return
        todo = self.env.ref("mail.mail_activity_data_todo", raise_if_not_found=False)
        partner_model = self.env["ir.model"]._get("res.partner").id
        summary = "Receivables & Payables — daily check"

        for user in users:
            partner = user.partner_id
            # Clear yesterday's auto activity (matched by our summary marker).
            old = self.env["mail.activity"].search([
                ("res_model", "=", "res.partner"),
                ("res_id", "=", partner.id),
                ("summary", "=", summary),
            ])
            old.unlink()

            note = self._build_digest_html(data)
            vals = {
                "res_model_id": partner_model,
                "res_id": partner.id,
                "summary": summary,
                "note": note,
                "user_id": user.id,
                "date_deadline": fields.Date.context_today(self),
            }
            if todo:
                vals["activity_type_id"] = todo.id
            self.env["mail.activity"].create(vals)

    @api.model
    def _cron_send_digest(self):
        """Entry point for the daily cron: email + in-app activity."""
        data = self.get_dashboard_data()
        html = self._build_digest_html(data)
        subject = self._digest_subject(data)
        recipients = self._digest_recipients()

        if recipients:
            mail = self.env["mail.mail"].sudo().create({
                "subject": subject,
                "body_html": html,
                "email_to": recipients,
                "auto_delete": True,
            })
            mail.send()

        self._post_digest_activity(data)
        return True
