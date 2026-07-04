import yaml
from pathlib import Path
import importlib.util


def _get_state():
    try:
        from operon.prompt.tool.reason.state import state
        return state
    except Exception:
        state_path = Path(__file__).parent / "state.py"
        spec = importlib.util.spec_from_file_location(
            "operon_prompt_tool_reason_state", str(state_path)
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.state


state = _get_state()


class Task:
    name = "Task"
    prompt = '''Task:
Add a task, tick a task or view tasks from local memory. To add a task:

type: "Task"
data:
  type: "Add"
  name: "name of task here"
  content: "content of task here"

The result of this call will be a None result

To view all tasks(in time order):

type: "Task"
data:
  type: "View"

the result of this will be in the following format:

type: "Result"
data:
  task1:
    name: name of task1
    content: content of task1
  ...

To tick a task(i.e. mark it as done and delete it):

type: "Task"
data:
  type: "Tick"
  name: "name of the task you wanna tick here"
The result of such will also be None result'''

    def run(self, value):
        try:
            res = value["data"]
        except Exception:
            return yaml.dump({"type": "Error", "data": "Invalid payload for Task tool"})

        t = res.get("type")
        if t == "Add":
            state.add_task(res["name"], res["content"])
            return yaml.dump({"type": "Result", "data": None})
        elif t == "View":
            data = state.get_task_view()
            print(data)
            return yaml.dump({"type": "Result", "data": {"fromTool": "Task", "value": data}})
        elif t == "Tick":
            try:
                state.tick_task(res["name"])
            except KeyError:
                return yaml.dump({"type": "Error", "data": "The task the plan want to hook to didn't exist; Check for typo or create it"})
            return yaml.dump({"type": "Result", "data": None})
        else:
            return yaml.dump({"type": "Error", "data": "Unknown `type` for task tool, it's either wrong or not exist"})
