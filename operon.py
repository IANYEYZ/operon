import operon
import yaml
import json
from pathlib import Path

srcPath = Path(__file__).parent

if __name__ == "__main__":
    llm = operon.defaultLLM
    server = operon.toolServer
    command = input(">>> ")
    if command == ":exit": exit(0)
    msg = operon.USER(yaml.dump({
        "type": "Message",
        "data": command
    }))
    while True:
        res = llm(msg)
        # print(res)
        if res["type"] == "Print":
            print("LLM: ", res["data"])
            msg = operon.USER(yaml.dump({
                "type": "None",
                "data": None
            }))
        elif res["type"] == "END":
            command = input(">>> ")
            if command == ":exit": break
            msg = operon.USER(yaml.dump({
                "type": "Message",
                "data": command
            }))
        elif res["type"] == "Error":
            msg = operon.USER(res)
        else:
            msg = operon.USER(server(res))
    open(srcPath / "task.json", "w").write(json.dumps(server.tasks))
    