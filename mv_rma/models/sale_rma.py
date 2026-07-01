from odoo import Command, api, fields, models
from odoo.exceptions import UserError


class SaleRma(models.Model):
    _name = 'sale.rma'
    _description = 'Return Merchandise Authorization'
    _order = 'id desc'

    name = fields.Char(
        string='RMA Number',
        required=True,
        readonly=True,
        copy=False,
        default='New',
    )
    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale Order',
        required=True,
        ondelete='cascade',
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
        related='sale_order_id.partner_id',
        store=True,
        readonly=True,
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
    )
    qty = fields.Float(
        string='Quantity',
        required=True,
        default=1.0,
    )
    reason = fields.Text(string='Reason')
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('processed', 'Processed'),
        ],
        string='Status',
        default='draft',
        required=True,
        copy=False,
    )
    move_id = fields.Many2one(
        comodel_name='account.move',
        string='Journal Entry',
        readonly=True,
        copy=False,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('sale.rma') or 'New'
        return super().create(vals_list)

    def action_confirm(self):
        for rma in self:
            if rma.state != 'draft':
                raise UserError("Only draft RMAs can be confirmed.")
            rma.state = 'confirmed'

    def action_credit_note(self):
        return self._create_move('out_refund')

    def action_reinvoice(self):
        return self._create_move('out_invoice')

    def _create_move(self, move_type):
        self.ensure_one()
        if self.state != 'confirmed':
            raise UserError("The RMA must be confirmed before it can be processed.")
        move = self.env['account.move'].create({
            'move_type': move_type,
            'partner_id': self.partner_id.id,
            'invoice_origin': self.name,
            'invoice_line_ids': [Command.create({
                'product_id': self.product_id.id,
                'quantity': self.qty,
                'name': self.reason or self.product_id.display_name,
            })],
        })
        self.move_id = move.id
        self.state = 'processed'
        return {
            'type': 'ir.actions.act_window',
            'name': 'Credit Note' if move_type == 'out_refund' else 'Invoice',
            'res_model': 'account.move',
            'res_id': move.id,
            'view_mode': 'form',
            'target': 'current',
        }
