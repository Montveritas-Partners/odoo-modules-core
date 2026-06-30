# Odoo Modules Core

Production-grade Odoo Community modules, built by [Montveritas Partners](https://github.com/Montveritas-Partners) for real SMB manufacturing and distribution clients — not demos, not proof-of-concepts.

All modules here are built and tested on **Odoo 19.0 Community**, MIT-licensed, and designed to be dependency-light and safe to install alongside existing data.

## Modules

| Module | What it does |
|---|---|
| [`mv_cash_radar`](./mv_cash_radar) | Colour-coded Receivables & Payables dashboard inside Invoicing, with an optional daily digest email and in-app activity reminders |

More modules will land here as they're stripped of client-specific config and cleared for public release.

## Philosophy

These modules come out of hands-on Odoo Community work in manufacturing and distribution — RV industry, embedded/IoT-adjacent businesses, and general SMB operations. Each one is:

- **Read-only or additive by default** — nothing here mutates existing data unless that's explicitly the module's job
- **Config over code** — tunable via `ir.config_parameter` / System Parameters, not hardcoded values
- **Scoped** — no inherited views that silently change other parts of your Odoo instance

## Using these modules

Drop any module folder into your addons path and install it from the Apps list, or via command line:

```bash
docker exec <container> odoo -c /etc/odoo/odoo.conf -d <database> -u <module_name> --stop-after-init
```

## Contributing

Issues and PRs welcome. If you're running one of these in production and hit an edge case, open an issue — real-world bug reports are how these stay solid.

## About Montveritas Partners

Montveritas Partners provides Odoo Community consulting for SMB manufacturers and distributors — custom module development, implementation, and ongoing support, US-based and Community-native (no Enterprise upsell).

[montveritas.com](https://montveritas.com) · [LinkedIn](https://linkedin.com)

## License

MIT. See individual module folders for any module-specific licensing notes.
