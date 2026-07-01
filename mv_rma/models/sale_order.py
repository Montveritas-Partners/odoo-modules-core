from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    rma_ids = fields.One2many(
        comodel_name='sale.rma',
        inverse_name='sale_order_id',
        string='RMAs',
    )
    rma_count = fields.Integer(
        string='RMA Count',
        compute='_compute_rma_count',
    )

    @api.depends('rma_ids')
    def _compute_rma_count(self):
        for order in self:
            order.rma_count = len(order.rma_ids)

    def action_create_rma(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'New RMA',
            'res_model': 'sale.rma',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_sale_order_id': self.id,
            },
        }

    def action_view_rma(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'RMAs',
            'res_model': 'sale.rma',
            'view_mode': 'list,form',
            'domain': [('sale_order_id', '=', self.id)],
            'context': {
                'default_sale_order_id': self.id,
            },
        }
