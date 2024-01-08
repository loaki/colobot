import json
import requests

from .. import config


def llm_call(prompt: str):
    hostname = config.LLM_HOST
    body = {
        "prompt": f"<|im_start|>system\nTu es un assistant virtuel sur un bot discord, tu es drole et gentil<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant",
        "n_predict": 512,
        "temperature": 0.7,
        "stop": ["<|im_end|>"],
        "tokens_cached": 0,
    }
    response = requests.post(hostname, json=body)
    if response.status_code == requests.codes.ok:
        r_json = json.loads(response.text)
        return r_json.get("content")
    return None
