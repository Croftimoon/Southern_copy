from odoo import fields, models, api, _


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    is_consignment_warehouse = fields.Boolean(string="Is Consignment Warehouse")

    @api.model
    def create_warehouses(self):
        for company in self.env['res.company'].search([]):
            wh_name = f"{company.name}-Consignment Warehouse"
            if self.search([('name', '=', wh_name)]):
                wh_name = wh_name + "2"
            wh_code = company.country_code if company.country_code else "" + 'CW'
            if self.search([('code', '=', wh_code)]):
                wh_code = wh_code + "2"
            warehouse = self.create({'is_consignment_warehouse': True, 'company_id': company.id,
                                     'name': wh_name,
                                     'code': wh_code, 'partner_id': company.partner_id.id})
            warehouse.view_location_id.is_consignment_location = True
            warehouse.wh_input_stock_loc_id.is_consignment_location = True
            warehouse.wh_output_stock_loc_id.is_consignment_location = True
            warehouse.wh_pack_stock_loc_id.is_consignment_location = True
            warehouse.wh_qc_stock_loc_id.is_consignment_location = True

    @api.model
    def default_get(self, default_fields):
        res = super().default_get(default_fields)
        if self.env.context.get('is_consignment_warehouse', False):
            res['is_consignment_warehouse'] = True
        return res
