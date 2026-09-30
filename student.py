"""Реализация управляемого цикла агента и независимого evaluator."""
from core import parse_action, episode


def _finish_is_currently_valid(env):
    """Контроллерная проверка для finish(done).

    Здесь проверяется именно наличие актуальной успешной validation того же
    предложения. Полную проверку истинности результата выполняет evaluate().
    """
    state = env.snapshot()
    proposal = state.get("proposal")
    validation = state.get("validation")
    return bool(
        proposal
        and validation
        and validation.get("valid") is True
        and validation.get("version") == state.get("version")
        and validation.get("proposal") == proposal
    )


def run_agent(policy, env, max_steps=12):
    """Запустить agent loop с наблюдаемой историей и жёстким лимитом шагов."""
    history = []

    while len(history) < max_steps:
        step = len(history) + 1

        try:
            raw = policy.next_action(history)
        except Exception as exc:
            history.append({
                "step": step,
                "observation": {
                    "ok": False,
                    "error": "model_error",
                    "exception_type": type(exc).__name__,
                },
            })
            return episode("model_error", history, env)

        event = {"step": step, "raw": raw}
        try:
            action = parse_action(raw)
        except ValueError as exc:
            event["observation"] = {"ok": False, "error": str(exc)}
            history.append(event)
            continue

        event["action"] = action

        if action["type"] == "tool":
            try:
                observation = env.call(action["name"], action["args"])
            except Exception as exc:
                # В данной учебной Environment ошибки обычно возвращаются как
                # observation. Этот guard сохраняет контракт и для иной среды.
                observation = {
                    "ok": False,
                    "error": "tool_error",
                    "exception_type": type(exc).__name__,
                }
            event["observation"] = observation
            history.append(event)
            continue

        status = action["status"]
        question = action["question"]

        if status == "done" and not _finish_is_currently_valid(env):
            event["observation"] = {
                "ok": False,
                "error": "finish_without_validation",
            }
            history.append(event)
            continue

        event["observation"] = {"ok": True, "final_status": status}
        history.append(event)
        return episode(status, history, env, question)

    return episode("budget_exhausted", history, env)


def evaluate(result):
    """Проверить успех эпизода только по финальному состоянию среды."""
    if not isinstance(result, dict):
        return False

    status = result.get("status")
    state = result.get("state")
    if not isinstance(state, dict):
        return False

    ticket = state.get("ticket")
    resources = state.get("resources")
    proposal = state.get("proposal")
    validation = state.get("validation")
    version = state.get("version")

    if not isinstance(ticket, dict) or not isinstance(resources, list):
        return False

    skill = ticket.get("skill")
    budget = ticket.get("budget")

    def eligible(resource):
        return bool(
            isinstance(resource, dict)
            and skill is not None
            and skill in resource.get("skills", [])
            and resource.get("available") is True
            and isinstance(resource.get("cost"), (int, float))
            and isinstance(budget, (int, float))
            and resource["cost"] <= budget
        )

    if status == "done":
        if not isinstance(proposal, dict) or not isinstance(validation, dict):
            return False

        resource = next(
            (r for r in resources if isinstance(r, dict) and r.get("id") == proposal.get("resource_id")),
            None,
        )
        if resource is None or not eligible(resource):
            return False

        if proposal.get("ticket_id") != ticket.get("id"):
            return False
        if proposal.get("policy_id") != "P1":
            return False
        if proposal.get("cost") != resource.get("cost"):
            return False

        return bool(
            validation.get("valid") is True
            and validation.get("version") == version
            and validation.get("proposal") == proposal
        )

    if status == "needs_input":
        question = result.get("question", "")
        q = question.casefold() if isinstance(question, str) else ""
        return bool(
            skill is None
            and proposal is None
            and question.strip()
            and ("навык" in q or "skill" in q)
        )

    if status == "no_solution":
        return bool(
            skill is not None
            and proposal is None
            and not any(eligible(resource) for resource in resources)
        )

    return False
