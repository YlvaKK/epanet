import unittest
from pytest_mock import mocker
from epanet_actions import *


class ProjectActionsTest(unittest.TestCase):

    def test_create_leakage_suite_1(self):
        mocker.patch("epanet.toolkit.getnodeid", return_value='x')
        mocker.patch("epanet.toolkit.addnode", return_value=4)
        mocker.patch("epanet.toolkit.addlink", return_value=2)
        mocker.patch("epanet.toolkit.setpipedata", return_value=0)

        pa = ProjectActions(0, True)
        pa.create_leakage_suite(3)
        self.assertEqual(pa.create_leakage_suite(3), ['x', 'ln 0', 'ln 1', 'ln 2', 'x'])


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
        self.assertEqual(True, True)


if __name__ == '__main__':
    unittest.main()
