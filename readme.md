# Operon

<p align="center">
  <img src="logo.svg" width="160">
</p>

<h3 align="center">
Teach software to think.
</h3>

<p align="center">
An embeddable AI runtime for existing applications.
</p>

---

## What is Operon?

Most AI frameworks start with the model and build an application around it.

Operon starts from the opposite direction:

> The application already exists.

Operon adds a reasoning layer to software you already built.

Your application provides capabilities.

Operon decides when and how to use them.

---

## Why Operon?

AI should become part of software.

A database does not replace your application. It becomes part of it.

Operon follows the same idea:

- The host owns data and execution.
- Tools expose existing capabilities.
- Operon handles reasoning and coordination.

---

## Quick Start

Install:

```bash
pip install openai pyyaml python-dotenv
```

Then copy `operon.py` to your project

Example:

```python
from operon import *
from dotenv import load_dotenv
import os
load_dotenv()
brain = Operon(os.getenv("DEEPSEEK_API_KEY"), "deepseek-chat",
"""You are running inside a math helper. Your goal is to solve the math problem provided to you
Use the Calculator tool as much as you want.
Use `Report` tool once and only once (before END) to report the result back""")
@tool(shape = Str())
def Calculator(expression):
    """
    Calculator:
    Takes an expression and returns its value
    format:
    type: "Calculator"
    data: "put expression here"
    """
    return eval(expression)
@tool(shape = OneOf(Str(), Int(), Float()))
def Report(value):
    """
    Report:
    Report the result back to the system, only put the numeric result here, do not add any formatting
    format:
    type: "Report"
    data: "value here"
    """
    print(f"The answer of your question is {value}")
brain.use(Calculator).use(Report)
brain.run("What's 230 * 131?")
```

Tools are normal application functions.

Operon does not replace your software.
It connects reasoning to what your software can already do.

---

## Features

* Lightweight embeddable runtime
* Tool-based application integration
* Shape validation for inputs and auto-retry
* Runtime Cards for host context
* Controller hooks for application policies

---

## Philosophy

AI should not replace software.

AI should become part of software.

**Operon — Teach software to think.**
