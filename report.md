# Отчёт по ЛР2

## 1. Взаимодействие модели и инструментов

Контроллер реализован как цикл `policy.next_action(history) → parse_action → env.call → observation → history`. Policy получает только цель, описание инструментов и историю наблюдений; `case`, `env.snapshot()`, `category` и `fault` ей не передаются. Каждая попытка получить действие расходует один из 12 шагов. Невалидный JSON становится наблюдением `invalid_json`, неизвестный инструмент не выполняется, исключение policy завершает эпизод как `model_error`, а инструментальная ошибка остаётся наблюдением и позволяет агенту перепланировать. `finish(done)` проходит отдельный gate: должны существовать proposal и актуальная положительная validation той же версии и именно для этого proposal. После завершения `evaluate()` независимо проверяет существование/доступность ресурса, навык, бюджет, стоимость, `ticket_id`, `policy_id=P1` и согласованность validation.

```text
policy → JSON action → parse_action → tool/env → observation → history → policy
                           ↘ finish → controller guard → evaluate(final state)
```

## 2. Результаты

Выполнен детерминированный scripted-прогон на test: 20 задач × 2 режима × 2 повтора = 80 эпизодов. Это проверка механики стенда, **не обязательный LLM-эксперимент**.

| Режим | Успехи | Success rate | Шаги/эп. | Tool calls/эп. | Model calls | Tokens | p50 / p95 |
|---|---:|---:|---:|---:|---:|---:|---:|
| fixed | 24/40 | 60% | 4.2 | 3.6 | 0 | 0 | 0.149 / 0.698 ms |
| agent | 40/40 | 100% | 5.6 | 4.6 | 0 | 0 | 0.224 / 0.914 ms |

По классам normal, missing_skill и no_resource оба режима дали 8/8. На transient и stale fixed дал 0/8, agent — 8/8. Разница возникает именно там, где требуется использовать новое observation и изменить следующий шаг. Нулевые model calls/tokens относятся только к ScriptedPolicy и не являются оценкой стоимости LLM.

## 3. Сбои и независимая проверка

`test_04 / transient`: fixed получает `temporary_unavailable` на первом `list_resources` и заканчивает `tool_error`; agent повторяет чтение, затем создаёт и валидирует proposal. Трасса: `failure_examples/01_transient_fixed_vs_agent.json`.

`test_05 / stale`: R0 становится недоступен перед записью. fixed получает `assignment_blocked`; agent перечитывает ресурсы, выбирает R1 и успешно завершает. Трасса: `failure_examples/02_stale_fixed_vs_agent.json`.

`false_done`: ReplayPolicy возвращает `finish(done)` без proposal и validation. Контроллер записывает `finish_without_validation`, эпизод заканчивается `budget_exhausted`, `evaluate=False`. Трасса: `failure_examples/03_false_done_guard.json`. Дополнительные пять негативных тестов проверяют wrong skill, over budget, fabricated resource, wrong `ticket_id` и validation от другого proposal; все 25 тестов проходят.

## 4. Выводы

В учебной среде обратная связь дала преимущество только на transient/stale, где состояние меняется или чтение временно падает; цена — рост средней траектории с 4.2 до 5.6 шага и tool calls с 3.6 до 4.6. Независимый evaluator необходим: строка `done` и даже `validation.valid=True` сами по себе не доказывают корректность конечного состояния. Результат ограничен маленьким синтетическим набором. Обязательный LLM test-прогон 80 эпизодов в этом runtime не выполнялся из-за отсутствия LLM endpoint/API key, поэтому scripted-цифры не выдаются за LLM-результаты.
