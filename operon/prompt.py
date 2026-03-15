"""
Load prompt
"""

def loadPrompt(name):
    return open(f"./prompt/{name}").read()