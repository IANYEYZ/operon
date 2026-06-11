from . import LLM, USER
from .server import ToolServer
from concurrent.futures import ThreadPoolExecutor
import os
import yaml
from . import loadBranchSystemPrompt

branchesPool = ThreadPoolExecutor(max_workers=10)
branches = {}
branchID = 1

def branch(goal):
    print("Running Branch with goal: ", goal)
    global branchID, branches
    currentID = branchID
    branchID += 1
    branches.update({
        currentID: {
            "status": "Running"
        }
    })
    print(branches)
    llm = LLM(apikey = os.getenv("DEEPSEEK_API_KEY"), model = "deepseek-chat",\
               gId = currentID, systemPrompt = loadBranchSystemPrompt())
    server = ToolServer()
    print(f"Branch {currentID} started with goal: {goal}")
    msg = USER(yaml.dump({
        "type": "Goal",
        "data": goal
    }))
    while True:
        print(f"Branch {currentID} is running with goal: {goal}")
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

def addBranch(goal):
    branchesPool.submit(lambda: branch(goal))