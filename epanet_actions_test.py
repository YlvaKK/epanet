import unittest
from epanet_actions import NetworkUnits


class NetworkUnitsTest(unittest.TestCase):
    def test_units_invalid_input(self):
        with self.assertRaises(IndexError):
            NetworkUnits(-1)
        with self.assertRaises(IndexError):
            NetworkUnits(15)

    def test_units_imperial(self):
        nu = NetworkUnits(3)
        self.assertEqual(nu.pressure, 'psi')
        self.assertEqual(nu.flow, 'gpm')
        self.assertEqual(nu.length, 'foot')

    def test_units_metric(self):
        nu = NetworkUnits(6)
        self.assertEqual(nu.pressure, 'm of head')
        self.assertEqual(nu.flow, 'lps')
        self.assertEqual(nu.length, 'm')


class TrigonometryTest(unittest.TestCase):

    def test_get_elevation(self):
        self.assertEqual(True, False)


if __name__ == '__main__':
    unittest.main()
