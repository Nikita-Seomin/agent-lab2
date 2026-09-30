"""Сформировать три воспроизводимых примера сбоев/защит контроллера."""
import json
from pathlib import Path
from baseline import run_fixed
from core import Environment, ReplayPolicy, ScriptedPolicy, finish
from student import evaluate, run_agent

cases = json.loads((Path(__file__).parent / "data/test.json").read_text(encoding="utf-8"))
by_id = {c["id"]: c for c in cases}
out = Path("failure_examples")
out.mkdir(exist_ok=True)

examples = []

# 1. transient: fixed прекращает работу после первого неудачного чтения ресурсов.
case = by_id["test_04"]
fixed = run_fixed(ScriptedPolicy(), Environment(case))
agent = run_agent(ScriptedPolicy(), Environment(case))
examples.append(("01_transient_fixed_vs_agent", {"case_id": case["id"], "fixed": fixed, "fixed_success": evaluate(fixed), "agent": agent, "agent_success": evaluate(agent)}))

# 2. stale: R0 устаревает между list_resources и propose_assignment.
case = by_id["test_05"]
fixed = run_fixed(ScriptedPolicy(), Environment(case))
agent = run_agent(ScriptedPolicy(), Environment(case))
examples.append(("02_stale_fixed_vs_agent", {"case_id": case["id"], "fixed": fixed, "fixed_success": evaluate(fixed), "agent": agent, "agent_success": evaluate(agent)}))

# 3. ложный done: контроллер не принимает завершение без validation.
case = by_id["test_01"]
false_done = run_agent(ReplayPolicy([finish("done")]), Environment(case), max_steps=1)
examples.append(("03_false_done_guard", {"case_id": case["id"], "result": false_done, "success": evaluate(false_done)}))

for name, payload in examples:
    (out / f"{name}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
