from datetime import datetime
import random
from turtledemo.paint import switchupdown

from google import genai
from google.genai import types
from typing import Protocol

class AITools(Protocol):
    async def get_response(self, prompt: str, temperature: float = None, instructions: str = None, think_budget: int = -1) -> str:  # Common definition that all will follow
        ...
class GeminiAITools:
    def __init__(self, APIkeys: tuple[str, ...]):
        self.keys = APIkeys
        print("Looks like your file copy thing is working like it should.")
    async def get_response(self, prompt: str, temperature: float = None, instructions: str = None, mode: str = "normal") -> str:
        if not temperature:
            temperature = 1
        print("hi")
        think_budget = 0
        model = 'gemini-2.5-flash'
        match mode:
            case "fast":
                think_budget = 0
                model = 'gemini-2.5-flash-lite'
            case "normal":
                think_budget = -1
                model = 'gemini-2.5-flash'
            case "smart":
                think_budget = -1
                model = 'gemini-2.5-pro'

        if not instructions:
            instructions = "You are responding to a Discord conversation; do not say anything remotely NSFW or racist."
        gemini = genai.Client(api_key=random.choice(self.keys))
        print("about to get it")
        message = gemini.models.generate_content(model=model, config=types.GenerateContentConfig(system_instruction=instructions, temperature=temperature, thinking_config=types.ThinkingConfig(thinking_budget=think_budget)), contents=prompt)
        print("got it")
        return message.text

