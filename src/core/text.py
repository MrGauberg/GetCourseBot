import json


def get_text(path):
    with open(path, 'r') as f:
        content = f.read()
        text = json.loads(content)
    return text
