from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestPurchaseComputeOrderMinPackage(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.supplierinfo_model = cls.env["product.supplierinfo"]
        cls.cpo_model = cls.env["computed.purchase.order"]
        cls.cpol_model = cls.env["computed.purchase.order.line"]

        cls.supplier = cls.env["res.partner"].create({"name": "Test CPO Supplier"})

        # Product 1: min=3, no max, package_qty=10, price 3.31 per uom
        cls.product1 = cls.env["product.product"].create(
            {"name": "Test CPO Product 1", "purchase_ok": True}
        )
        cls.psi1 = cls.supplierinfo_model.create(
            {
                "partner_id": cls.supplier.id,
                "product_tmpl_id": cls.product1.product_tmpl_id.id,
                "min_nb_of_package": 3,
                "max_nb_of_package": 0,
                "package_qty": 10,
                "base_price": 3.31,
                "price_policy": "uom",
            }
        )
        cls.psi1.price = 3.31

        # Product 2: min=2, max=5, package_qty=10, price 5.0 per uom
        cls.product2 = cls.env["product.product"].create(
            {"name": "Test CPO Product 2", "purchase_ok": True}
        )
        cls.psi2 = cls.supplierinfo_model.create(
            {
                "partner_id": cls.supplier.id,
                "product_tmpl_id": cls.product2.product_tmpl_id.id,
                "min_nb_of_package": 2,
                "max_nb_of_package": 5,
                "package_qty": 10,
                "base_price": 5.0,
                "price_policy": "uom",
            }
        )
        cls.psi2.price = 5.0

    def test_compute_two_lines_clamped_to_min(self):
        cpo = self.cpo_model.create(
            {
                "partner_id": self.supplier.id,
                "target_type": "product_price_inv_eq",
                "valid_psi": "first",
            }
        )
        cpo.compute_active_product_stock()
        self.assertEqual(len(cpo.line_ids), 2)
        line1 = cpo.line_ids.filtered(lambda line: line.product_id == self.product1)
        line2 = cpo.line_ids.filtered(lambda line: line.product_id == self.product2)
        self.assertTrue(line1 and line2)
        for line in line1 | line2:
            line.consumption_range = 1
            line.displayed_average_consumption = 5

        # Small target => the loop stops right away and each line is clamped
        # up to its own min_nb_of_package.
        cpo.purchase_target = 50
        cpo.compute_purchase_quantities()

        self.assertEqual(line1.purchase_qty_package, 3)
        self.assertEqual(line1.purchase_qty, 30)
        self.assertEqual(line2.purchase_qty_package, 2)
        self.assertEqual(line2.purchase_qty, 20)

    def test_purchase_qty_package_exceeds_max(self):
        cpo = self.cpo_model.create({"partner_id": self.supplier.id})
        cpol = self.cpol_model.create(
            {
                "computed_purchase_order_id": cpo.id,
                "product_id": self.product2.id,
                "psi_id": self.psi2.id,
                "purchase_qty_package": 3,
                "uom_po_id": self.product2.uom_id.id,
            }
        )
        with self.assertRaises(ValidationError):
            cpol.write({"purchase_qty_package": 6})
