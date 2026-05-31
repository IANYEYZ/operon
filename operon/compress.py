from operon.LLM import USER, ASSISTANT
import yaml

def compress(messages):
    result = []
    for item in messages:
        m = yaml.safe_load(item.content)
        if m.type == "Result":
            if m.data != None and m.data.get("fromTool") == "ReadFile":
                result.append(USER(yaml.dump({
                    "type": "Result",
                    "data": {
                        "fromTool": "ReadFile",
                        "content": "Result truncated, re-call this tool call to recover",
                        "start": m.data.start,
                        "end": m.data.end
                    }
                })))
        else:
            result.append(item)