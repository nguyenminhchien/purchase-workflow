# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class ProductPackaging(models.Model):
    _inherit = "product.packaging"

    def _compute_contained_qty(self, package_qty, qty_uom=False):
        """Returns the contained qty in the packages.
        Other words, this method converts package qty to product qty.

        :param package_qty: float of package quantity
        :param qty_uom: Optional uom of quantity
        :returns: float of contained qty (
            given in product UoM if no qty_uom provided)
        """
        self.ensure_one()
        product_qty = package_qty * self.qty
        if qty_uom:
            product_qty = self.product_uom_id._compute_quantity(product_qty, qty_uom)
        return product_qty
