"""
Construct a LLM class
Also parse the response
"""
from openai import OpenAI
import yaml
import os

from . import prompt

class LLM:
    def __init__(self, apikey: str, model: str, url: str = ""):
        self.client = OpenAI(api_key=apikey, base_url=url)
        self.model = model
        self.messages = [
            {"role": "system", "content": prompt.loadPrompt("SYSTEM")}
        ]
    def __call__(self, saveMessage: bool = True):
        res = self.client.chat.completions.create(
            model = self.model,
            messages = self.messages,
            stream = False
        )
        value = yaml.safe_load(res)
        print(value)

default = LLM(apikey = os.getenv("DEEPSEEK_API_KEY"))