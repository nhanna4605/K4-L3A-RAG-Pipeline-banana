"""Xoay vong (api_key, model) de vuot gioi han 20 request/ngay/model cua free tier.

Free tier Gemini: quotaId=GenerateRequestsPerDayPerProjectPerModel, limit=20.
Quota tinh rieng cho tung cap (key, model), nen N key x M model = N*M*20 request/ngay.
"""

import itertools
import time
from pathlib import Path

from dotenv import dotenv_values

REPO = Path("D:/Moitruongaocuaclaude/Lab8/K4-L3A-2A202602770-LV3")

MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-flash-lite-latest",
]


def load_keys() -> list[str]:
    env = dotenv_values(REPO / ".env")
    keys = []
    for name in ("GEMINI_API_KEY", "GEMINI_API_KEY_2", "GEMINI_API_KEY_3"):
        value = (env.get(name) or "").strip()
        if value and value not in keys:
            keys.append(value)
    if not keys:
        raise SystemExit("Khong co GEMINI_API_KEY nao trong .env")
    return keys


class Rotator:
    """Goi generate_content, tu chuyen sang cap (key, model) khac khi gap 429."""

    def __init__(self, models: list[str] | None = None):
        from google import genai

        self.keys = load_keys()
        self.models = models or MODELS
        self.pairs = list(itertools.product(range(len(self.keys)), self.models))
        self.clients = {i: genai.Client(api_key=k) for i, k in enumerate(self.keys)}
        self.cursor = 0
        self.exhausted: set[tuple[int, str]] = set()
        self.calls = 0
        self.used: dict[tuple[int, str], int] = {}

    def capacity(self) -> str:
        total = len(self.pairs) * 20
        return f"{len(self.keys)} key x {len(self.models)} model = {total} request/ngay"

    def generate(self, system_prompt: str, user_message: str,
                 temperature: float = 0.3, top_p: float = 0.9) -> str:
        from google.genai import types

        attempts = 0
        while attempts < len(self.pairs) * 2:
            key_index, model = self.pairs[self.cursor % len(self.pairs)]
            self.cursor += 1
            attempts += 1
            if (key_index, model) in self.exhausted:
                continue
            try:
                response = self.clients[key_index].models.generate_content(
                    model=model,
                    contents=user_message,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=temperature,
                        top_p=top_p,
                    ),
                )
                self.calls += 1
                self.used[(key_index, model)] = self.used.get((key_index, model), 0) + 1
                return (response.text or "").strip()
            except Exception as error:
                text = str(error)
                if "RESOURCE_EXHAUSTED" in text or "429" in text:
                    self.exhausted.add((key_index, model))
                    continue
                if "503" in text or "UNAVAILABLE" in text or "500" in text:
                    time.sleep(3)
                    continue
                raise
        raise RuntimeError(
            f"Het quota tren toan bo {len(self.pairs)} cap (key, model). "
            f"Da goi thanh cong {self.calls} request."
        )

    def report(self) -> str:
        lines = [f"  Tong request thanh cong: {self.calls}",
                 f"  Cap (key, model) da het quota: {len(self.exhausted)}/{len(self.pairs)}"]
        for (ki, model), n in sorted(self.used.items(), key=lambda x: -x[1]):
            lines.append(f"    key#{ki + 1}  {model:26} {n} request")
        return "\n".join(lines)
