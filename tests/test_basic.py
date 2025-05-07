#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Basic unit tests for mouse_juggler.py
"""

import unittest
import sys
import os
import numpy as np

# Add root directory to path to import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import mouse_juggler

class TestBasicFunctions(unittest.TestCase):
    """Tests for the basic trajectory calculation functions."""

    def test_pairwise(self):
        """Test for the pairwise function."""
        data = [1, 2, 3, 4]
        result = list(mouse_juggler.pairwise(data))
        expected = [(1, 2), (2, 3), (3, 4)]
        self.assertEqual(result, expected)

    def test_bezier_curve(self):
        """Test for the bezier curve function."""
        start = np.array([0, 0])
        control = np.array([10, 10])
        end = np.array([20, 0])
        n = 3
        
        result = mouse_juggler.bezier_curve(start, control, end, n)
        
        # Verify that the shape is correct
        self.assertEqual(result.shape, (n, 2))
        
        # Verify that the first point is the start
        np.testing.assert_array_almost_equal(result[0], start)
        
        # Verify that the last point is the end
        np.testing.assert_array_almost_equal(result[-1], end)

    def test_smooth_trajectory(self):
        """Test for the smooth trajectory generation function."""
        origin = (0, 0)
        destination = (100, 100)
        steps = 10
        
        result = mouse_juggler.smooth_trajectory(origin, destination, steps)
        
        # Verify that the length is correct
        self.assertEqual(len(result), steps)
        
        # Verify that the first point is the origin
        np.testing.assert_array_equal(result[0], np.array(origin))
        
        # Verify that the last point is the destination
        np.testing.assert_array_equal(result[-1], np.array(destination))

if __name__ == '__main__':
    unittest.main()