import yaml
from pathlib import Path
import importlib.util


def _get_state():
    try:
        from operon.prompt.tool.reason.state import state
        return state
    except Exception:
        state_path = Path(__file__).parent / "state.py"
        spec = importlib.util.spec_from_file_location("operon_prompt_tool_reason_state", str(state_path))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.state


state = _get_state()


class Plan:
    name = "Plan"
    prompt = '''Plan

Add/View a plan to a task. To add a Plan:

type: "Plan"
data:
    type: "Add"
    hook: "task name you want the plan to hook to, note that the task must exist, if it didn't then create it first"
    content: "content of the plan"

To view plans on a task:

type: "Plan"
data:
    type: "View"
    hook: "task name you want to view plans for"'''

    def run(self, value):
        try:
            res = value["data"]
        except Exception:
            return yaml.dump({"type": "Error", "data": "Invalid payload for Plan tool"})

        t = res.get("type")
        if t == "Add":
            try:
                state.add_plan(res["hook"], res["content"])
            except KeyError:
                return yaml.dump({"type": "Error", "data": "The task the plan want to hook to didn't exist; Check for typo or create it"})
            return yaml.dump({"type": "Result", "data": None})
        elif t == "View":
            try:
                data = state.get_plans(res["hook"])
            except KeyError:
                return yaml.dump({"type": "Error", "data": "The task that the plan want to hook to didn't exist; Check for typo or create it"})
            return yaml.dump({"type": "Result", "data": {"fromTool": "Plan", "value": data}})
        else:
            return yaml.dump({"type": "Error", "data": "Unknown `type` for plan tool, it's either wrong or not exist"})
