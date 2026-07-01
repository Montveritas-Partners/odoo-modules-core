{
    'name': 'Receivables & Payables',
    'summary': 'Adds a Receivables & Payables dashboard inside the Invoicing app plus a daily digest, flagging money to collect (invoices to send, overdue receivables) and money going out (vendor bills due), colour-coded by direction.',
    'version': '19.0.1.0.0',
    'license': 'Other OSI approved licence',
    'author': 'Montveritas',
    'website': 'https://github.com/Montveritas-Partners/odoo-modules-core',
    'category': 'Accounting/Accounting',
    'depends': ['base', 'web', 'mail', 'sale', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'data/cron.xml',
        'views/cash_radar_menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'mv_cash_radar/static/src/js/cash_radar.js',
            'mv_cash_radar/static/src/xml/cash_radar_templates.xml',
            'mv_cash_radar/static/src/scss/cash_radar.scss',
        ],
    },
    'installable': True,
}
