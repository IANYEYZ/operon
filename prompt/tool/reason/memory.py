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

ROOT = Path(__file__).resolve().parents[3]
MEM_DIR = ROOT / "memory"


class Memory:
    name = "Memory"
    prompt = '''Memory
Add/View long term memory. Memory is only recommended for guidelines and philosiphys that should keep in mind whatever the goal is. For things that's only useful for one or two particular missions, use task and plan

To Add a Memory:

type: "Memory"
data:
    type: "Add"
    name: "Name of the memory file"
    content: "Content of such memory"

To view all memories's NAMEs:

type: "Memory"
data:
    type: "View"
    name: None

Note that this will only return the names of memories

To view one specific memory:

type: "Memory"
data:
    type: "View"
    name: "Name of the memory file you want to view"'''

    def run(self, value):
        res = value.get("data")
        t = res.get("type")
        if t == "Add":
            name, content = res.get("name"), res.get("content")
            (MEM_DIR / name).write_text(content)
            return yaml.dump({"type": "Result", "data": None})
        elif t == "View":
            name = res.get("name")
            if name is None:
                files = [p.name for p in MEM_DIR.iterdir()]
                return yaml.dump({"type": "Result", "data": {"fromTool": "Memory", "value": files}})
            else:
                target = MEM_DIR / name
                if not target.exists():
                    return yaml.dump({"type": "Error", "data": f"Memory {name} doesn't exist"})
                return yaml.dump({"type": "Result", "data": {"fromTool": "Memory", "value": target.read_text()}})
        else:
            return yaml.dump({"type": "Error", "data": "Unknown `type` for memory tool, it's either wrong or not exist"})
