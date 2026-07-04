import operon
import operon.server
import yaml
import json
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

srcPath = Path(__file__).parent

if __name__ == "__main__":
    llm = operon.defaultLLM
    server = operon.server.toolServer
    operon.server.loadFromConfig(server, srcPath / "operon" / "prompt" / "tool")
    command = input(">>> ")
    if command == ":exit": exit(0)
    msg = operon.USER(yaml.dump({
        "type": "Message",
        "data": command
    }))
    while True:
        res = llm(msg)
        # print(res)
        if res.get("type") == "Print":
            text = res["data"]
            console = Console()
            md = Markdown(text)
            console.print(
                Panel(
                    md,
                    title="LLM",
                    border_style="blue"
                )
            )
            msg = operon.USER(yaml.dump({
                "type": "None",
                "data": None
            }))
        elif res.get("type") == "END":
            command = input(">>> ")
            if command == ":exit": break
            msg = operon.USER(yaml.dump({
                "type": "Message",
                "data": command
            }))
        elif res.get("type") == "AskUser":
            print("LLM: ", res["data"])
            command = input(">>> ")
            if command == ":exit": break
            msg = operon.USER(yaml.dump({
                "type": "Message",
                "data": command
            }))
        elif res.get("type") == "Error":
            msg = operon.USER(res["data"])
        elif res.get("type") == "MetaError":
            print("Error happens because of system error")
            print("Enter to retry", end = "\n")
            input()
            msg = None
        else:
            msg = operon.USER(server(res))
    open(srcPath / "operon" / "task.json", "w").write(json.dumps(server.tasks))
    