from datetime import datetime
import random
from google import genai
from google.genai import types
from typing import Protocol

class AITools(Protocol):
    async def get_response(self, prompt: str, temperature: float = None, instructions: str = None) -> str:  # Common definition that all will follow
        ...
class GeminiAITools:
    def __init__(self, APIkeys: tuple[str, ...]):
        self.keys = APIkeys
    async def get_response(self, prompt: str, temperature: float = None, instructions: str = None) -> str:
        if not temperature:
            temperature = 1
        if not instructions:
            instructions = "You are responding to a Discord conversation; do not say anything remotely NSFW or racist."
        gemini = genai.Client(api_key=random.choice(self.keys))
        message = gemini.models.generate_content(model='gemini-2.5-flash', config=types.GenerateContentConfig(system_instruction=instructions, temperature=temperature), contents=prompt)
        return message.text

