from .LLM import LLM, USER
from .server import ToolServer
from concurrent.futures import ThreadPoolExecutor
import os
import yaml

branchesPool = ThreadPoolExecutor()
branches = {}
branchID = 1

def branch(goal):
    currentID = branchID
    branches[currentID] = {
        "status": "Running"
    }
    llm = LLM(apikey = os.getenv("DEEPSEEK_API_KEY"), model = "deepseek-chat", systemPrompt = "")
    server = ToolServer()
    msg = USER(yaml.dump({
        "type": "Goal",
        "data": goal
    }))
    while True:
        res = llm(msg)
        # print(res)
        if res["type"] == "END":
            branches[currentID] = {
                "status": "Finished",
                "return": res["data"]
            }
            break
        elif res["type"] == "Error":
            msg = USER(res["data"])
        elif res["type"] == "MetaError":
            print(f"Error happens because of system error, from Branch {currentID}")
            print("Enter to retry", end = "\n")
            input()
            msg = None
        else:
            msg = USER(server(res))
    branchID += 1

def addBranch(goal):
    branchesPool.submit(lambda: branch(goal))