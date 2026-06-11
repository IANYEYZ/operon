"""
Construct a LLM class
Also parse the response
"""
from openai import OpenAI
import yaml
import os
from dotenv import load_dotenv
import time

from . import loadSystemPrompt

load_dotenv()

def SYSTEM(message: str = ""): return {"role": "system", "content": message}
def USER(message: str = ""): return {"role": "user", "content": message}
def ASSISTANT(message: str = ""): return {"role": "assistant", "content": message}

class LLM:
    def __init__(self, apikey: str, model: str, systemPrompt = loadSystemPrompt(), gId = 0, url: str = "https://api.deepseek.com"):
        self.client = OpenAI(api_key=apikey, base_url=url)
        self.model = model
        self.messages = [
            SYSTEM(systemPrompt)
        ]
        self.gId = gId
    def setMessages(self, messages):
        self.messages = messages
    def __call__(self, userMessage = None, saveMessage: bool = True):
        if userMessage != None: self.messages.append(userMessage)
        for attempt in range(3):
            try:
                res = self.client.chat.completions.create(
                    model = self.model,
                    messages = self.messages,
                    stream = False,
                    temperature=0.3
                ).choices[0].message.content
                # print("Raw LLM Response: ", res)
                # print("---")
                if saveMessage:
                    self.messages.append(ASSISTANT(res))
                try:
                    print(f"Parsed LLM Response from {self.gId}: ", yaml.safe_load(res))
                    if isinstance(yaml.safe_load(res), dict):
                        return yaml.safe_load(res)
                    else:
                        raise Exception("")
                except:
                    print("Format Error:")
                    print(res)
                    return {
                        "type": "Error",
                        "data": """Format Error because of incorrect format, please try again
Possible format errors:
1. there's extra text around the yaml. Stop putting text(even apologize) before yaml, and the issue will be solved. For example, the following is NOT valid, because of the "Mnnn, let me think" before the yaml

Mnnn, let me think
type: "Print"
data: "OK, I found the solution"

Delete the Mnnn, let me think, and only output

type: "Print"
data: "OK, I found the solution"

Will fix the issue
2. double quote or single quote not covering the whole string
for example, the following is NOT valid
type: "Print"
data: "Hello there" This is a test
because the double quote incorrectly stopped early
It's also recommended that, for multi-line string, use the | grammar in yaml
3. more than one tool calls being put together. Seperate them into multiple calls, first call the first one, then call the second one, etc.
4. a format different of yaml is used. For example, the following is NOT valid
<print>
OK, let's make this
</print>
In short, your output need to be correct yaml, with nothing else before or after, for one and only one tool call
Note that this errored message won't be displayed to user, find the format issue, and manually redo what you want to do"""
                    }
            except Exception as e:
                last_err = e
                print(f"SYSTEM: LLM {self.gId} call failed, attempt {attempt + 1}/3: {e}")
                if attempt < 2:
                    time.sleep(1)

        return {
            "type": "MetaError",
            "data": f"LLM API Error after 3 retries: {last_err}"
        }

defaultLLM = LLM(apikey = os.getenv("DEEPSEEK_API_KEY"), model = "deepseek-chat")