"""Пять самостоятельных негативных проверок evaluator для отчёта ЛР2."""
import copy
import json
from pathlib import Path
import unittest

from core import Environment, ScriptedPolicy
from student import evaluate, run_agent

CASES = json.loads((Path(__file__).resolve().parents[1] / "data/dev.json").read_text(encoding="utf-8"))


class NegativeEvaluatorChecks(unittest.TestCase):
    def valid_result(self):
        result = run_agent(ScriptedPolicy(), Environment(CASES[0]))
        self.assertTrue(evaluate(result))
        return result

    @staticmethod
    def sync_validation(result):
        result["state"]["validation"] = {
            "valid": True,
            "version": result["state"]["version"],
            "proposal": copy.deepcopy(result["state"]["proposal"]),
        }

    def test_rejects_wrong_skill(self):
        result = self.valid_result()
        wrong = result["state"]["resources"][2]  # design вместо python
        result["state"]["proposal"].update(resource_id=wrong["id"], cost=wrong["cost"])
        self.sync_validation(result)
        self.assertFalse(evaluate(result))

    def test_rejects_over_budget(self):
        result = self.valid_result()
        result["state"]["ticket"]["budget"] = 1
        self.sync_validation(result)
        self.assertFalse(evaluate(result))

    def test_rejects_fabricated_resource(self):
        result = self.valid_result()
        result["state"]["proposal"].update(resource_id="R_DOES_NOT_EXIST", cost=0)
        self.sync_validation(result)
        self.assertFalse(evaluate(result))

    def test_rejects_wrong_ticket_id(self):
        result = self.valid_result()
        result["state"]["proposal"]["ticket_id"] = "T-FORGED"
        self.sync_validation(result)
        self.assertFalse(evaluate(result))

    def test_rejects_validation_from_another_proposal(self):
        result = self.valid_result()
        other = copy.deepcopy(result["state"]["proposal"])
        other["resource_id"] = "R1"
        other["cost"] = 50
        result["state"]["validation"] = {
            "valid": True,
            "version": result["state"]["version"],
            "proposal": other,
        }
        self.assertFalse(evaluate(result))


if __name__ == "__main__":
    unittest.main()
