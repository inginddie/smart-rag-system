# -*- coding: utf-8 -*-
import json
from collections import Counter
from pathlib import Path

class FAQManager:
    """Gestiona el registro y obtención de preguntas frecuentes."""

    def __init__(self, log_path: str = "data/faqs.json"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._data = {}
        self._load()

    def _load(self):
        if self.log_path.exists():
            try:
                with open(self.log_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except Exception:
                self._data = {}
        else:
            self._data = {}

    def _save(self):
        try:
            with open(self.log_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def log_question(self, question: str) -> None:
        question = question.strip()
        if not question:
            return
        self._data[question] = self._data.get(question, 0) + 1
        self._save()

    def get_top_questions(self, n: int = 5):
        counter = Counter(self._data)
        return [q for q, _ in counter.most_common(n)]
