# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _prepare_sellers(self, params=False):
        """Override to filter by product_packaging_id if provided in params."""
        sellers = super()._prepare_sellers(params=params)
        if params and params.get("product_packaging_id"):
            sellers2 = sellers.filtered(
                lambda s, p=params["product_packaging_id"]: s.product_packaging_id == p
            )
            if sellers2:
                return sellers2
        return sellers
