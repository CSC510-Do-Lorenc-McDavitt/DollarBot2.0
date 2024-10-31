"""
File: test_currency.py
Author: Yumo Shen, Jiewen Liu, Haojie Zhou
Date: October 28, 2024
Description: File includes tests for basic functionality, error handling, data integrity, and edge cases for the currency module. 

Copyright (c) 2024

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS," WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import sys
import os
import unittest
from unittest import mock
from code.currency import get_supported_currencies, get_conversion_rate


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestCurrency(unittest.TestCase):

    def test_fetch_supported_currencies(self):
        currencies = get_supported_currencies()
        self.assertIsNotNone(currencies, "Failed to fetch supported currencies")
        self.assertIn("USD", currencies, "USD should be in supported currencies")

    def test_fetch_supported_currencies_failure(self):
        with unittest.mock.patch("requests.get", side_effect=Exception("Network error")):
            currencies = get_supported_currencies()
            self.assertIsNone(currencies, "Should return None on failure")

    def test_supported_currencies_list_not_empty(self):
        currencies = get_supported_currencies()
        self.assertGreater(len(currencies), 0, "Currency list should not be empty")

    def test_valid_currency_in_supported_list(self):
        currencies = get_supported_currencies()
        self.assertIn("EUR", currencies, "EUR should be in supported currencies")

    def test_invalid_currency_not_in_supported_list(self):
        currencies = get_supported_currencies()
        self.assertNotIn("XYZ", currencies, "XYZ should not be in supported currencies")

    def test_conversion_rate_success(self):
        rate = get_conversion_rate("USD", "EUR")
        self.assertIsInstance(rate, float, "Conversion rate should be a float")

    def test_conversion_rate_invalid_currency(self):
        rate = get_conversion_rate("USD", "XYZ")
        self.assertIsNone(rate, "Invalid target currency should return None")

    def test_conversion_rate_base_currency_failure(self):
        rate = get_conversion_rate("AAA", "USD")
        self.assertIsNone(rate, "Invalid base currency should return None")

    def test_conversion_rate_network_failure(self):
        with unittest.mock.patch("requests.get", side_effect=Exception("Network error")):
            rate = get_conversion_rate("USD", "EUR")
            self.assertIsNone(rate, "Should return None on network failure")

    def test_conversion_rate_precision(self):
        rate = get_conversion_rate("USD", "EUR")
        self.assertAlmostEqual(rate, round(rate, 2), delta=0.01, msg="Rate should be accurate to 2 decimal places")
    
    def test_empty_base_currency(self):
        rate = get_conversion_rate("", "USD")
        self.assertIsNone(rate, "Empty base currency should return None")

    def test_empty_target_currency(self):
        rate = get_conversion_rate("USD", "")
        self.assertIsNone(rate, "Empty target currency should return None")

    def test_same_base_and_target_currency(self):
        rate = get_conversion_rate("USD", "USD")
        self.assertEqual(rate, 1.0, "Same base and target currency should return 1.0")

    def test_supported_currencies_type(self):
        currencies = get_supported_currencies()
        self.assertIsInstance(currencies, list, "Supported currencies should be a list")

    def test_supported_currencies_elements_type(self):
        currencies = get_supported_currencies()
        if currencies:
            self.assertIsInstance(currencies[0], str, "Currency codes should be strings")

    def test_conversion_rate_invalid_base_currency_format(self):
        rate = get_conversion_rate("US1", "EUR")
        self.assertIsNone(rate, "Invalid base currency format should return None")

    def test_conversion_rate_invalid_target_currency_format(self):
        rate = get_conversion_rate("USD", "EU1")
        self.assertIsNone(rate, "Invalid target currency format should return None")

    def test_conversion_rate_none_base_currency(self):
        rate = get_conversion_rate(None, "EUR")
        self.assertIsNone(rate, "None as base currency should return None")

    def test_conversion_rate_none_target_currency(self):
        rate = get_conversion_rate("USD", None)
        self.assertIsNone(rate, "None as target currency should return None")

    def test_conversion_rate_large_amount_precision(self):
        rate = get_conversion_rate("USD", "JPY")
        if rate:
            converted_amount = rate * 1_000_000
            self.assertAlmostEqual(converted_amount, round(converted_amount, 2), delta=0.01, msg="Large amount conversion should be accurate to 2 decimal places")

if __name__ == '__main__':
    unittest.main()
