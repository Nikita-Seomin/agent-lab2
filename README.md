# ЛР2 — пакет работы

Python 3.10+, внешние зависимости для scripted-прогона не нужны.

## 1. Проверка реализации

```bash
python -m unittest discover -s tests -v
```

Ожидается: 25 тестов, включая 5 самостоятельных негативных проверок в `tests/test_negative_checks.py`.

## 2. Детерминированная проверка механики

```bash
python run.py --policy scripted --split dev --mode all --out results_scripted_dev
python run.py --policy scripted --split test --mode all --repeats 2 --out results_scripted_test
python analyze_results.py results_scripted_test/results.csv --out results_scripted_test/category_summary.csv
python make_failure_examples.py
```

`scripted` — только отладочный двойник, не LLM-эксперимент.


## Что уже реально запускалось

См. `RUN_EVIDENCE.md`. Подтверждено: 25/25 тестов, полный scripted test на 80 эпизодов, пять негативных проверок и три контролируемых сбоя. Дополнительная повторная проверка находится в `results_scripted_test_verified/`. Исходный исследовательский документ сохранён в `evidence/research_source.docx`.

Важно: обязательный test-прогон на реальной LLM в доступном runtime не выполнялся; scripted-данные не следует выдавать за LLM.

## 3. Обязательный LLM-эксперимент

Сначала задать переменные окружения. Пример PowerShell:

```powershell
$env:MAS_LLM_BASE_URL = "https://YOUR-ENDPOINT/v1"
$env:MAS_LLM_MODEL = "YOUR-MODEL"
$env:MAS_LLM_API_KEY = "YOUR-KEY"
```

Отладка только на dev:

```bash
python run.py --policy llm --split dev --mode all --out results_llm_dev
```

После фиксации `agent_prompt.txt`, модели и настроек — test без дальнейшей настройки:

```bash
python run.py --policy llm --split test --mode all --repeats 2 --out results_llm_test
python analyze_results.py results_llm_test/results.csv --out results_llm_test/category_summary.csv
```

Итоговый test содержит 20 задач × 2 режима × 2 повтора = 80 эпизодов. В `results_llm_test` автоматически сохраняются `results.csv`, `summary.csv`, `run_config.json`, JSON каждого эпизода и JSONL истории. Запросы/ответы LLM находятся внутри JSON эпизодов; API-ключ туда не попадает.

## 4. Перед сдачей

Заменить таблицу раздела 2 в `report.md` реальными метриками LLM и разобрать три LLM-сбоя, если они есть. Если собственных сбоев недостаточно, допускаются приложенные ReplayPolicy-примеры. Не выдавать scripted-метрики за LLM.
