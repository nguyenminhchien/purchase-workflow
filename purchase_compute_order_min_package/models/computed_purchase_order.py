##############################################################################
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

from odoo import models


class ComputedPurchaseOrder(models.Model):
    _inherit = "computed.purchase.order"

    def parse_cpol_vals(self, psi, product):
        res = super().parse_cpol_vals(psi, product)
        if psi.package_qty:
            # Packaging case
            purchase_qty_package = psi.min_nb_of_package
            # Only prefill the minimum number of packages when the purchase
            # target is large enough to absorb it. If applying the minimum
            # would already make this line's subtotal exceed the target, start
            # from 0 instead of forcing the minimum.
            if self.purchase_target and purchase_qty_package:
                if psi.price_policy == "package":
                    unit_price = psi.base_price
                    qty = purchase_qty_package
                else:
                    unit_price = psi.price
                    qty = purchase_qty_package * psi.package_qty
                subtotal = qty * unit_price * (1 - psi.discount / 100.0)
                if subtotal > self.purchase_target:
                    purchase_qty_package = 0
            res.update({"purchase_qty_package": purchase_qty_package})
        return res
