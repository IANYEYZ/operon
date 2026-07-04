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


class ScratchPad:
    name = "ScratchPad"
    prompt = '''ScratchPad
Temperarily write down thoughts, useful for reasoning. The content in ScratchPad is not saved between different sessions. The ScratchPad is not shown to the user

type: "ScratchPad"
data: "The text you want to append. If you just want to view current content, leave this as an empty string"

The return value will be the whole content of the ScratchPad'''

    def run(self, value):
        append = value.get("data")
        if not isinstance(append, str):
            return yaml.dump({"type": "Error", "data": "The data entry of ScratchPad must be a string"})
        result = state.append_scratch(append)
        return yaml.dump({"type": "Result", "data": {"fromTool": "ScratchPad", "value": result}})
