import unittest

from e5_price_list import normalize_pairs


class PriceListNormalizationTests(unittest.TestCase):
    def test_identical_pairs_are_equal(self):
        left = normalize_pairs([[" चाय ", "20"]])
        right = normalize_pairs([["चाय", 20]])
        self.assertEqual(left, right)

    def test_missing_pair_is_not_equal(self):
        left = normalize_pairs([["चाय", 20], ["कॉफी", 40]])
        right = normalize_pairs([["चाय", 20]])
        self.assertNotEqual(left, right)


if __name__ == "__main__":
    unittest.main()
