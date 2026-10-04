import unittest

from ml_engine import Finding
from ml_engine.scoring.health_score import HealthScoreConfig, calculate_health_score


class HealthScoreTests(unittest.TestCase):
    def test_size_normalized_completeness_and_balanced_target(self):
        score = calculate_health_score(
            {"rows": 10, "columns": 2, "missing_cells": 1, "duplicate_rows": 0},
            [],
        )
        self.assertEqual(score["components"]["completeness"], 90.0)
        self.assertEqual(score["components"]["balance"], 100.0)

    def test_custom_weights_and_grade(self):
        score = calculate_health_score({"rows": 1, "columns": 1, "missing_cells": 0}, [], HealthScoreConfig())
        self.assertEqual(score["grade"], "Excellent")

    def test_leakage_finding_affects_component(self):
        finding = Finding("leakage", "possible_data_leakage", "high", "check")
        score = calculate_health_score({}, [finding])
        self.assertLess(score["components"]["leakage"], 100)
