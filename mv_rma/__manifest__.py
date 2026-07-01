{
    'name': 'RMA (Return Merchandise Authorization)',
    'summary': 'Minimal RMA management: raise returns from a sale order and issue a credit note or re-invoice.',
    'version': '19.0.1.0.0',
    'license': 'Other OSI approved licence',
    'author': 'Montveritas',
    'website': 'https://github.com/Montveritas-Partners/odoo-modules-core',
    'category': 'Sales/Sales',
    'depends': ['sale', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/sale_rma_views.xml',
        'views/sale_order_button.xml',
    ],
    'installable': True,
    'application': False,
}
