"""HTTP /v1/chat/completions. Ключ только из окружения, запросы логируются без него."""
import json
import os
import time
from pathlib import Path
import urllib.request
from urllib.parse import urlparse

class LLMPolicy:
    def __init__(self, mode="agent", temperature=0.2):
        self.base = os.environ["MAS_LLM_BASE_URL"].rstrip("/")
        parsed = urlparse(self.base)
        if parsed.scheme != "https" and not (parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1", "::1"}):
            raise ValueError("Use HTTPS or local HTTP endpoint")
        self.model = os.environ["MAS_LLM_MODEL"]
        self.key = os.environ.get("MAS_LLM_API_KEY", "")
        self.temperature = temperature
        self.system = Path(__file__).with_name("agent_prompt.txt").read_text(encoding="utf-8")
        if mode == "fixed":
            self.system += "\nФиксированный workflow: сначала верни propose_assignment или finish needs_input/no_solution. После validate_assignment верни только finish. Новые чтения и повтор записи в этом режиме недоступны."
        self.requests = []
        self.usage = {"prompt_tokens": 0, "completion_tokens": 0, "model_calls": 0}

    def next_action(self, history):
        messages = [{"role": "system", "content": self.system},
                    {"role": "user", "content": json.dumps({"goal": "Создать допустимое предложение по текущей заявке и проверить его. Либо запросить навык, либо сообщить отсутствие решения.", "history": history}, ensure_ascii=False)}]
        payload = {"model": self.model, "messages": messages, "temperature": self.temperature,
                   "max_tokens": 256, "stream": False}
        self.requests.append({"request": payload})
        self.usage["model_calls"] += 1
        headers = {"Content-Type": "application/json"}
        if self.key:
            headers["Authorization"] = "Bearer " + self.key
        req = urllib.request.Request(self.base + "/chat/completions",
                                     data=json.dumps(payload).encode(), headers=headers, method="POST")
        try:
            time.sleep(2)
            
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.load(response)
        except Exception:
            self.usage["prompt_tokens"] = None
            self.usage["completion_tokens"] = None
            raise
        content = result["choices"][0]["message"]["content"]
        self.requests[-1]["response_content"] = content
        self.requests[-1]["usage"] = result.get("usage")
        usage = result.get("usage", {})
        for key in ("prompt_tokens", "completion_tokens"):
            if key not in usage or self.usage[key] is None:
                self.usage[key] = None
            else:
                self.usage[key] += usage[key]
        if not isinstance(content, str):
            raise ValueError("model content is not text")
        return content
