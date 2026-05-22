from typing import Any, Dict, List, Optional
from app.core.logging import StructuredLogger
from app.middleware.error_handler import RulesEngineError


class RulesEngine:
    """
    Decoupled Rules Engine evaluating dynamic JSON predicates against transaction contexts
    to automate step routing, auto-approval, and step-skipping.
    """
    
    @staticmethod
    def evaluate_condition(field_val: Any, operator: str, rule_val: Any) -> bool:
        """
        Evaluates a single comparison predicate.
        """
        try:
            if operator == ">":
                return float(field_val) > float(rule_val)
            elif operator == "<":
                return float(field_val) < float(rule_val)
            elif operator == "==":
                return str(field_val).lower() == str(rule_val).lower()
            elif operator == "!=":
                return str(field_val).lower() != str(rule_val).lower()
            elif operator == "contains":
                return str(rule_val).lower() in str(field_val).lower()
            else:
                StructuredLogger.warning(f"Unsupported rules operator encountered: {operator}")
                return False
        except (ValueError, TypeError) as e:
            StructuredLogger.warning(
                f"Predicate evaluation type mismatch error. Field Value: {field_val}, Rule Value: {rule_val}. Error: {str(e)}"
            )
            return False

    @classmethod
    def evaluate_step_rule(
        cls,
        rule_def: Optional[Dict[str, Any]],
        context_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluates a step's rule definition. If conditions match, returns the action dictionary.
        
        Example rule_def:
        {
            "conditions": [
                {"field": "amount", "operator": ">", "value": 10000},
                {"field": "department_code", "operator": "==", "value": "FIN"}
            ],
            "action": "ROUTE_TO_ROLE",
            "action_value": "FinanceDirector"
        }
        """
        if not rule_def or "action" not in rule_def:
            return None

        conditions: List[Dict[str, Any]] = rule_def.get("conditions", [])
        
        # If no conditions are declared but action is present, execute action unconditionally
        if not conditions:
            return {
                "action": rule_def["action"],
                "action_value": rule_def.get("action_value")
            }

        # Verify all declared conditions are satisfied (AND logic)
        for cond in conditions:
            field = cond.get("field")
            operator = cond.get("operator")
            rule_value = cond.get("value")

            if not field or not operator or rule_value is None:
                StructuredLogger.warning(f"Mal-formed condition object ignored in rule evaluation: {cond}")
                return None

            # Retrieve attribute from transactional context data
            context_value = context_data.get(field)
            if context_value is None:
                StructuredLogger.info(
                    f"Rules evaluation: context field '{field}' is missing in request context. Condition fails."
                )
                return None

            # Perform single check
            if not cls.evaluate_condition(context_value, operator, rule_value):
                # Any single failure breaks the AND gate
                return None

        # All conditions passed successfully! Return overrides
        StructuredLogger.info(
            f"Rules matched! Executing action '{rule_def['action']}' with value '{rule_def.get('action_value')}'"
        )
        return {
            "action": rule_def["action"],
            "action_value": rule_def.get("action_value")
        }
