/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, useState, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

class MvCashRadarDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            buckets: [],
            currency: { symbol: "", position: "before" },
            company: "",
            loading: true,
        });

        onMounted(() => this.load());
    }

    async load() {
        this.state.loading = true;
        try {
            const data = await this.orm.call("mv.cash.radar", "get_dashboard_data", []);
            this.state.buckets = data.buckets;
            this.state.currency = data.currency;
            this.state.company = data.company;
        } catch (error) {
            console.error("Cash Radar load error:", error);
        } finally {
            this.state.loading = false;
        }
    }

    get incoming() {
        return this.state.buckets.filter((b) => b.direction === "in");
    }

    get outgoing() {
        return this.state.buckets.filter((b) => b.direction === "out");
    }

    // Card colour class is keyed off direction + overdue flag.
    cardClass(bucket) {
        if (bucket.overdue) {
            return "o_cash_card o_cash_overdue";
        }
        return bucket.direction === "in"
            ? "o_cash_card o_cash_incoming"
            : "o_cash_card o_cash_outgoing";
    }

    money(amount) {
        const body = (amount || 0).toLocaleString(undefined, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });
        const sym = this.state.currency.symbol;
        return this.state.currency.position === "after"
            ? `${body} ${sym}`
            : `${sym}${body}`;
    }

    // Open the full filtered list for a bucket.
    openBucket(bucket) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: bucket.label,
            res_model: bucket.model,
            domain: bucket.domain,
            views: [
                [false, "list"],
                [false, "form"],
            ],
            target: "current",
        });
    }

    // Open a single record from the preview list.
    openRecord(bucket, recId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: bucket.model,
            res_id: recId,
            views: [[false, "form"]],
            target: "current",
        });
    }
}

MvCashRadarDashboard.template = "mv_cash_radar.Dashboard";
registry.category("actions").add("mv_cash_radar_dashboard", MvCashRadarDashboard);
