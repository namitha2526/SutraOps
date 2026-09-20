import sys
import unittest
sys.path.append("backend")
from app.services.rules_engine import RulesEngine


class TestRulesEngine(unittest.TestCase):
    def test_evaluate_condition_greater_than(self):
        # Numeric checks
        self.assertTrue(RulesEngine.evaluate_condition(15000, ">", 10000))
        self.assertFalse(RulesEngine.evaluate_condition(5000, ">", 10000))
        self.assertFalse(RulesEngine.evaluate_condition(10000, ">", 10000))
        # String representations of float
        self.assertTrue(RulesEngine.evaluate_condition("15000", ">", "10000"))
        # Invalid values handling
        self.assertFalse(RulesEngine.evaluate_condition("abc", ">", 10000))

    def test_evaluate_condition_less_than(self):
        self.assertTrue(RulesEngine.evaluate_condition(5000, "<", 10000))
        self.assertFalse(RulesEngine.evaluate_condition(15000, "<", 10000))
        self.assertFalse(RulesEngine.evaluate_condition(10000, "<", 10000))
        self.assertTrue(RulesEngine.evaluate_condition("5000.5", "<", "10000"))
        self.assertFalse(RulesEngine.evaluate_condition("abc", "<", 10000))

    def test_evaluate_condition_equal(self):
        # Case insensitive string checks
        self.assertTrue(RulesEngine.evaluate_condition("FIN", "==", "fin"))
        self.assertTrue(RulesEngine.evaluate_condition("IT", "==", "IT"))
        self.assertFalse(RulesEngine.evaluate_condition("HR", "==", "FIN"))
        # Numeric equality represented as string
        self.assertTrue(RulesEngine.evaluate_condition(100, "==", "100"))

    def test_evaluate_condition_not_equal(self):
        self.assertTrue(RulesEngine.evaluate_condition("HR", "!=", "FIN"))
        self.assertFalse(RulesEngine.evaluate_condition("FIN", "!=", "fin"))

    def test_evaluate_condition_contains(self):
        self.assertTrue(RulesEngine.evaluate_condition("Finance Department", "contains", "finance"))
        self.assertTrue(RulesEngine.evaluate_condition("Information Technology", "contains", "tech"))
        self.assertFalse(RulesEngine.evaluate_condition("HR", "contains", "finance"))

    def test_evaluate_condition_unsupported_operator(self):
        self.assertFalse(RulesEngine.evaluate_condition("test", "INVALID_OP", "test"))

    def test_evaluate_step_rule_no_rule(self):
        self.assertIsNone(RulesEngine.evaluate_step_rule(None, {}))
        self.assertIsNone(RulesEngine.evaluate_step_rule({"conditions": []}, {}))  # Missing action

    def test_evaluate_step_rule_unconditional_action(self):
        rule = {"action": "AUTO_APPROVE"}
        result = RulesEngine.evaluate_step_rule(rule, {})
        self.assertEqual(result, {"action": "AUTO_APPROVE", "action_value": None})

    def test_evaluate_step_rule_match_conditions(self):
        rule = {
            "conditions": [
                {"field": "amount", "operator": ">", "value": 10000},
                {"field": "department_code", "operator": "==", "value": "FIN"}
            ],
            "action": "ROUTE_TO_ROLE",
            "action_value": "FinanceDirector"
        }
        # Matching context
        context_match = {"amount": 15000, "department_code": "FIN"}
        result = RulesEngine.evaluate_step_rule(rule, context_match)
        self.assertEqual(result, {"action": "ROUTE_TO_ROLE", "action_value": "FinanceDirector"})

        # Non-matching context (one condition fails)
        context_mismatch = {"amount": 5000, "department_code": "FIN"}
        self.assertIsNone(RulesEngine.evaluate_step_rule(rule, context_mismatch))

        # Missing field in context
        context_missing = {"amount": 15000}
        self.assertIsNone(RulesEngine.evaluate_step_rule(rule, context_missing))


if __name__ == "__main__":
    unittest.main()
