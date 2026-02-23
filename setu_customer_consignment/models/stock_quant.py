from odoo import _, api, fields, models

from odoo.osv import expression

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    def _gather(self, product_id, location_id, lot_id=None, package_id=None, owner_id=None, strict=False, qty=0):
        if self._context.get('property_is_consignment_order') and self._context.get('consignment_lots'):
            removal_strategy = self._get_removal_strategy(product_id, location_id)
            domain = [('product_id', '=', product_id.id)]
            # removal_strategy_order = self._get_removal_strategy_domain_order(removal_strategy=removal_strategy, domain=domain)
            domain, order = self._get_removal_strategy_domain_order(domain, removal_strategy, qty)


            if not strict:
                # if lot_id:
                #     domain = expression.AND([['|', ('lot_id', '=', lot_id.id), ('lot_id', '=', False)], domain])
                if self._context.get('property_is_consignment_order') and self._context.get('consignment_lots'):
                    domain = expression.AND(
                        [['|', ('lot_id', 'in', self._context.get('consignment_lots')), ('lot_id', '=', False)],
                         domain])
                elif lot_id:
                    domain = expression.AND([['|', ('lot_id', '=', lot_id.id), ('lot_id', '=', False)], domain])
                if package_id:
                    domain = expression.AND([[('package_id', '=', package_id.id)], domain])
                if owner_id:
                    domain = expression.AND([[('owner_id', '=', owner_id.id)], domain])
                domain = expression.AND([[('location_id', 'child_of', location_id.id)], domain])
            else:
                domain = expression.AND(
                    [['|', ('lot_id', '=', lot_id.id), ('lot_id', '=', False)] if lot_id else [('lot_id', '=', False)],
                     domain])
                domain = expression.AND([[('package_id', '=', package_id and package_id.id or False)], domain])
                domain = expression.AND([[('owner_id', '=', owner_id and owner_id.id or False)], domain])
                domain = expression.AND([[('location_id', '=', location_id.id)], domain])

            return self.search(domain=domain, order=order).sorted(lambda q: not q.lot_id)
        else:
            return super(StockQuant, self)._gather(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=strict,
                                                   qty=0)
