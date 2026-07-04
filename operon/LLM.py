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

import re

START_RE = re.compile(r'(?m)^type:\s*["\'][^"\']+["\']\s*$')

def has_extra_text_before_yaml(text: str) -> bool:
    match = START_RE.search(text)
    if match is None: return False
    before = text[:match.start()]
    return before.strip() != ""

def extra_text_before_yaml(text: str) -> str:
    match = START_RE.search(text)
    if match is None:
        raise ValueError('No YAML start found: expected line like `type: "something"`')
    return text[:match.start()]

load_dotenv()

def SYSTEM(message: str = ""): return {"role": "system", "content": message}
def USER(message: str = ""): return {"role": "user", "content": message}
def ASSISTANT(message: str = ""): return {"role": "assistant", "content": message}

class LLM:
    def __init__(self, apikey: str, model: str, systemPrompt = loadSystemPrompt()
                 , gId = 0, url: str = "https://api.deepseek.com"):
        self.client = OpenAI(api_key=apikey, base_url=url)
        self.model = model
        self.messages = [SYSTEM(systemPrompt)]
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
                # print(res)
                if saveMessage:
                    self.messages.append(ASSISTANT(res))
                try:
                    # Prefer the first YAML document that parses to a mapping.
                    # print(res)
                    parsed = None
                    multiple = False
                    try:
                        docs = list(yaml.safe_load_all(res))
                        if len(docs) > 1: multiple = True
                        for doc in docs:
                            if isinstance(doc, dict):
                                parsed = doc
                                break
                    except Exception:
                        parsed = None

                    # Fallback: single-document parse
                    if parsed is None:
                        parsed = yaml.safe_load(res)
                    
                    if multiple:
                        return {
                            "type": "Error",
                            "data": """Format Error: multiple tool calls detected
All these tool calls are canceled, manually redo them one by one"""
                        }

                    print(f"Parsed LLM Response from {self.gId}: ", parsed)
                    if isinstance(parsed, dict):
                        return parsed
                    else:
                        raise Exception("")
                except:
                    print("Format Error:")
                    print(res)
                    if has_extra_text_before_yaml(res):
                        return {
                            "type": "Error",
                            "data": f"Format Error: extra text before YAML.\n\nExtra text before yaml: {extra_text_before_yaml(res)}\n\nYour output must start with `type:` on the very first line. No explanations, no thinking out loud, no markdown. Just pure YAML, starting at line 1.\n\nRedo waht you want to do"
                        }
                    return {
                        "type": "Error",
                        "data": "Format Error: invalid YAML output.\n\nYour output must be a single valid YAML tool call with nothing before or after.\nCommon issues:\n- Extra text around the YAML\n- Missing or broken quotes\n- Multiple tool calls in one response\n- Wrong format (not YAML)\n\nFix the format and retry."
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

defaultLLM = LLM(apikey = os.getenv("LONGCAT_API_KEY"), model = "LongCat-2.0", url = "https://api.longcat.chat/openai")