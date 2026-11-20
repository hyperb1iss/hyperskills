import unittest

from stockpile.catalog import Catalog, Product, normalize_sku


class NormalizeTest(unittest.TestCase):
    def test_lowercase_and_whitespace_are_tolerated(self):
        self.assertEqual(normalize_sku("  abc-1234 "), "ABC-1234")

    def test_malformed_codes_are_rejected(self):
        for text in ("AB-1234", "ABC-123", "ABC1234", "ABC-123456789", "", None, 1234):
            with self.subTest(text=text), self.assertRaises(ValueError):
                normalize_sku(text)


class CatalogTest(unittest.TestCase):
    def test_describe_falls_back_to_the_code(self):
        catalog = Catalog([Product("TEA-0001", "Loose leaf, 250 g")])
        self.assertEqual(catalog.describe("tea-0001"), "Loose leaf, 250 g")
        self.assertEqual(catalog.describe("TEA-0002"), "TEA-0002")

    def test_duplicates_are_rejected(self):
        catalog = Catalog([Product("TEA-0001", "Loose leaf")])
        with self.assertRaises(ValueError):
            catalog.add(Product("tea-0001", "Again"))

    def test_membership_ignores_malformed_codes(self):
        catalog = Catalog([Product("TEA-0001", "Loose leaf")])
        self.assertIn("TEA-0001", catalog)
        self.assertNotIn("not a sku", catalog)
        self.assertEqual(len(catalog), 1)


if __name__ == "__main__":
    unittest.main()
