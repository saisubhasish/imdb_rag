import re

def remove_think_tags(text):
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

def remove_query(text):
    return text['result']