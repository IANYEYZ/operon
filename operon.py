import operon
import yaml
import json
from pathlib import Path

srcPath = Path(__file__).parent

if __name__ == "__main__":
    sessions = json.load(open(srcPath / "operon" / "session.js"))
    print("Choose sessions to start - leave empty for new session")
    print(list(sessions.keys()))
    session = ""
    while True:
        session = input(">>> ")
        if session == "" or session in sessions.keys(): break
        print("invalid session name, please re-enter")
    print("OK, session loaded")
    history = sessions[session] if session != "" else {}
    # print(session, "\n", history)
    llm = operon.defaultLLM
    if session != "": llm.setMessages(history)
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
            msg = operon.USER(res["data"])
        else:
            msg = operon.USER(server(res))
    open(srcPath / "operon" / "task.json", "w").write(json.dumps(server.tasks))
    if session == "":
        sessionName = input("enter session name: ")
        sessions[sessionName] = llm.messages
    else:
        sessions[session] = llm.messages
    json.dump(sessions, open(srcPath / "operon" / "session.js"))
    