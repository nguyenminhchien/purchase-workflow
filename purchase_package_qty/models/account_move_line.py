##############################################################################
#
#    Purchase - Package Quantity Module for Odoo
#    Copyright (C) 2019-Today: La Louve (<https://cooplalouve.fr>)
#    Copyright (C) 2019-Today: Druidoo (<https://www.druidoo.io>)
#    Copyright (C) 2016-Today Akretion (https://www.akretion.com)
#    License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
#    @author Julien WESTE
#    @author Sylvain LE GAL (https://twitter.com/legalsylvain)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    product_packaging_id = fields.Many2one(
        "product.packaging",
        string="Packaging",
        domain="[('product_id', '=', product_id)]",
        check_company=True,
    )

    package_qty = fields.Float(
        related="product_packaging_id.qty",
        help="The quantity of products in a package.",
    )
    product_packaging_quantity = fields.Float(
        "Packaging Quantity",
        compute="_compute_product_packaging_quantity",
        inverse="_inverse_product_packaging_quantity",
        help="The number of packages.",
    )
    price_policy = fields.Selection(
        [("uom", "per UOM"), ("package", "per Package")],
        default="uom",
    )

    @api.depends("product_packaging_id", "product_uom_id", "quantity", "price_policy")
    def _compute_product_packaging_quantity(self):
        self.product_packaging_quantity = False
        for line in self:
            if not line.product_packaging_id:
                continue
            if line.price_policy == "package":
                line.product_packaging_quantity = line.quantity
            else:
                line.product_packaging_quantity = (
                    line.product_packaging_id._compute_qty(
                        line.quantity, line.product_uom_id
                    )
                )

    def _inverse_product_packaging_quantity(self):
        """Inverse method to set quantity from product_packaging_quantity."""
        self._set_product_packaging_quantity()

    @api.onchange("product_packaging_quantity", "price_policy")
    def onchange_product_packaging_quantity(self):
        """Onchange method to set quantity from product_packaging_quantity from UI."""
        self._set_product_packaging_quantity()

    def _set_product_packaging_quantity(self):
        for line in self:
            if not line.product_packaging_id or line.parent_state != "draft":
                continue
            if line.price_policy == "package":
                line.quantity = line.product_packaging_quantity
            else:
                line.quantity = line.product_packaging_id._compute_contained_qty(
                    line.product_packaging_quantity,
                    qty_uom=line.product_uom_id,
                )
