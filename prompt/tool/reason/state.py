import json
import threading
from pathlib import Path


class ReasonState:
    def __init__(self):
        self.lock = threading.Lock()
        # operon package root: ../../..
        self.op_root = Path(__file__).resolve().parents[3]
        self.task_file = self.op_root / "task.json"
        self._load_tasks()
        self.scratch = ""

    def _load_tasks(self):
        if self.task_file.exists():
            try:
                self.tasks = json.loads(self.task_file.read_text())
            except Exception:
                self.tasks = {}
        else:
            self.tasks = {}

    def _save(self):
        try:
            tmp = self.task_file.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(self.tasks, indent=2))
            tmp.replace(self.task_file)
        except Exception:
            # best-effort save; ignore failures to avoid crashing tools
            pass

    def get_tasks(self):
        with self.lock:
            return dict(self.tasks)

    def add_task(self, name: str, content: str):
        with self.lock:
            self.tasks[name] = {"content": content, "plan": []}
            self._save()

    def tick_task(self, name: str):
        with self.lock:
            if name not in self.tasks:
                raise KeyError("task does not exist")
            self.tasks.pop(name)
            self._save()

    def get_task_view(self):
        with self.lock:
            data = {}
            for p, i in enumerate(self.tasks.keys()):
                data["task" + str(p)] = {
                    "name": i,
                    "content": self.tasks[i].get("content")
                }
            return data

    def add_plan(self, hook: str, content: str):
        with self.lock:
            if hook not in self.tasks:
                raise KeyError("task does not exist")
            self.tasks[hook].setdefault("plan", []).append(content)
            self._save()

    def get_plans(self, hook: str):
        with self.lock:
            if hook not in self.tasks:
                raise KeyError("task does not exist")
            return list(self.tasks[hook].get("plan", []))

    def append_scratch(self, text: str):
        with self.lock:
            self.scratch += text
            return self.scratch

    def get_scratch(self):
        with self.lock:
            return self.scratch


state = ReasonState()
