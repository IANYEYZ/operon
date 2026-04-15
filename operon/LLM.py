"""
Construct a LLM class
Also parse the response
"""
from openai import OpenAI
import yaml
import os
from dotenv import load_dotenv

from . import loadPrompt

load_dotenv()

def SYSTEM(message: str = ""): return {"role": "system", "content": message}
def USER(message: str = ""): return {"role": "user", "content": message}
def ASSISTANT(message: str = ""): return {"role": "assistant", "content": message}

class LLM:
    def __init__(self, apikey: str, model: str, url: str = "https://api.deepseek.com"):
        self.client = OpenAI(api_key=apikey, base_url=url)
        self.model = model
        self.messages = [
            SYSTEM(loadPrompt("SYSTEM"))
        ]
    def __call__(self, userMessage, saveMessage: bool = True):
        self.messages.append(userMessage)
        res = self.client.chat.completions.create(
            model = self.model,
            messages = self.messages,
            stream = False,
            temperature=0.5
        ).choices[0].message.content
        # print("Raw LLM Response: ", res)
        # print("---")
        # print("Parsed LLM Response: ", yaml.safe_load(res))
        if saveMessage:
            self.messages.append(ASSISTANT(res))
        try:
            return yaml.safe_load(res)
        except:
            return {
                "type": "Error",
                "data": "Yaml Error because of incorrect format, please try again"
            }

defaultLLM = LLM(apikey = os.getenv("DEEPSEEK_API_KEY"), model = "deepseek-chat")