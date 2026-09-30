# Фактически выполненные прогоны

Этот файл отделяет реально выполненные в текущей работе проверки от обязательного LLM-эксперимента, который без внешнего endpoint/API key не запускался.

## 1. Unit/negative tests

Команда:

```bash
python -m unittest discover -s tests -v
```

Фактический результат повторной проверки 30.09.2026:

- 25 tests
- 25 passed
- 0 failed
- время повторной локальной проверки: 0.011 s

Пять дополнительных негативных проверок находятся в `tests/test_negative_checks.py` и отклоняют: неверный навык, превышение бюджета, вымышленный ресурс, неверный `ticket_id`, validation от другого proposal.

## 2. Scripted test experiment

Команда полного детерминированного прогона:

```bash
python run.py --policy scripted --split test --mode all --repeats 2 --out results_scripted_test
```

Размер: 20 test-задач × 2 режима × 2 повтора = 80 эпизодов.

Зафиксированные результаты исходного запуска:

| Режим | Успехи | Success rate | Средние шаги | Средние tool calls | p50 | p95 |
|---|---:|---:|---:|---:|---:|---:|
| fixed | 24/40 | 60% | 4.2 | 3.6 | 0.149 ms | 0.698 ms |
| agent | 40/40 | 100% | 5.6 | 4.6 | 0.224 ms | 0.914 ms |

Разбивка по классам:

| Класс | fixed | agent |
|---|---:|---:|
| normal | 8/8 | 8/8 |
| missing_skill | 8/8 | 8/8 |
| no_resource | 8/8 | 8/8 |
| transient | 0/8 | 8/8 |
| stale | 0/8 | 8/8 |

`results_scripted_test_verified/` содержит дополнительный повторный прогон, выполненный при сборке этого архива. Успехи и средние шаги/tool calls совпали: fixed 24/40, agent 40/40, 4.2/5.6 шага и 3.6/4.6 tool calls. Субмиллисекундные p50/p95 отличаются между запусками из-за шума окружения, поэтому для отчёта сохранены значения исходно зафиксированного прогона выше.

## 3. Контролируемые сбои

1. `transient`: fixed завершает `tool_error` после `temporary_unavailable`; agent использует ошибку как observation, повторяет `list_resources` и успешно завершает задачу.
2. `stale`: fixed выбирает R0, получает `assignment_blocked` после изменения состояния и прекращает работу; agent перечитывает ресурсы, выбирает R1 и завершает `done` после validation.
3. `false_done`: ReplayPolicy пытается сразу вернуть `finish(done)` без proposal/validation; контроллер пишет `finish_without_validation`, затем `budget_exhausted`, evaluator возвращает False.

Трассы находятся в `failure_examples/`.

## 4. Что не запускалось

Обязательный итоговый прогон с реальной LLM:

```bash
python run.py --policy llm --split test --mode all --repeats 2 --out results_llm_test
```

не выполнялся, потому что в доступном runtime не было `MAS_LLM_BASE_URL`, `MAS_LLM_MODEL` и API key/локального LLM-сервера. Scripted-метрики нельзя выдавать за LLM-метрики; для scripted `model_calls/tokens = 0` означает отсутствие вызова модели, а не стоимость настоящего агента.
