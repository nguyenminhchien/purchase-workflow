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
from odoo.exceptions import ValidationError


class ProductSupplierinfo(models.Model):
    _inherit = "product.supplierinfo"

    # Columns section
    product_variant_ids = fields.Many2many(
        comodel_name="product.product",
        compute="_compute_product_variant_ids",
        string="Product Variants",
    )
    product_packaging_id = fields.Many2one(
        "product.packaging",
        string="Packaging",
        check_company=True,
        domain="[('purchase', '=', True), ('product_id', 'in', product_variant_ids)]",
    )

    package_qty = fields.Float(
        related="product_packaging_id.qty",
    )
    indicative_package = fields.Boolean(
        help="""If checked, the system will not force you to purchase"""
        """ a strict multiple of package quantity""",
        default=False,
    )
    price_policy = fields.Selection(
        [("uom", "per UOM"), ("package", "per Package")],
        default="uom",
    )
    base_price = fields.Float(
        compute="_compute_base_price",
        store=True,
        readonly=False,
        digits="Product Price",
        help="The price to purchase a product",
    )
    price = fields.Float(
        compute="_compute_price",
        store=True,
        readonly=False,
    )

    @api.depends("product_id", "product_tmpl_id")
    def _compute_product_variant_ids(self):
        for psi in self:
            psi.product_variant_ids = (
                psi.product_id or psi.product_tmpl_id.product_variant_ids
            )

    @api.depends("price", "price_policy", "product_packaging_id")
    def _compute_base_price(self):
        for psi in self:
            if psi.price_policy == "package" and psi.product_packaging_id:
                psi.base_price = psi.price * psi.package_qty
            else:
                psi.base_price = psi.price

    @api.depends("base_price", "price_policy", "product_packaging_id")
    def _compute_price(self):
        for psi in self:
            if (
                psi.price_policy == "package"
                and psi.product_packaging_id
                and psi.package_qty
            ):
                psi.price = psi.base_price / psi.package_qty
            else:
                psi.price = psi.base_price

    # Constraints section
    @api.constrains("product_packaging_id")
    def _check_packaging(self):
        psis = self.filtered("product_packaging_id")
        for psi in psis:
            product = psi.product_packaging_id.product_id
            if (
                psi.product_id and product != psi.product_id
            ) or product.product_tmpl_id != psi.product_tmpl_id:
                raise ValidationError(
                    self.env._(
                        "The packaging %s is not valid for the product or variant.",
                        psi.product_packaging_id.display_name,
                    )
                )

    # Init section
    @api.model
    def _init_package_qty(self):
        psi_ids = self.sudo().search([])
        for psi in psi_ids:
            vals = {}
            if not psi.package_qty:
                vals["package_qty"] = max(psi.min_qty, 1)
            if not psi.base_price:
                vals["base_price"] = psi.price
            if vals:
                psi.write(vals)
        return psi_ids.ids
