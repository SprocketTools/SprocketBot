import asyncio
import random
from typing import Protocol, Optional
from google import genai
from google.genai import types


class AITools(Protocol):
    async def get_response(self, prompt: str, temperature: float = None, instructions: str = None,
                           think_budget: int = -1) -> str:
        ...


class GeminiAITools:
    def __init__(self, APIkeys: tuple[str, ...]):
        self.keys = APIkeys
        print("AI Tools initialized.")

    # --- INTERNAL HELPER (Runs on a separate thread) ---
    def _blocking_generate(self, model_name: str, prompt: str, temperature: float, system_instructions: str):
        try:
            gemini = genai.Client(api_key=random.choice(self.keys))
            if "gemma" not in model_name:
                config_obj = types.GenerateContentConfig(
                    temperature=temperature,
                    system_instruction=system_instructions
                )
            else:
                config_obj = types.GenerateContentConfig(
                    temperature=temperature
                )
                prompt = f'''===INSTRUCTIONS TO APPLY TO YOUR PROMPT===\n{system_instructions}\n\n\n\n\n\n\n\n===PROMPT===\n{prompt}'''
                print("Gemma is running...")


            message = gemini.models.generate_content(
                model=model_name,
                contents=[prompt],
                config=config_obj
            )

            try:
                response_text = message.text
                if not response_text:
                    raise ValueError("Empty response text")
                return response_text

            except Exception:
                print("---!! AI BLOCKED !!---")
                # Return None to signal the bot to use a generic error message
                return None

        except Exception as e:
            print(f"---!! AI ERROR !!--- {e}")
            # Return None to signal the bot to use a generic error message
            return None

    # --- MAIN ASYNC FUNCTION ---
    async def get_response(self, prompt: str, temperature: float = None, instructions: str = None,
                           mode: str = "normal") -> Optional[str]:
        if not temperature:
            temperature = 1.0

        model_name = 'models/gemini-2.5-flash'
        match mode:
            case "fast":
                model_name = 'models/gemini-2.5-flash-lite'
            case "normal":
                model_name = 'models/gemini-2.5-flash'
            case "smart":
                model_name = 'models/gemini-2.5-pro'
            case "gemma":
                model_name = 'models/gemma-3-27b-it'

        if not instructions:
            instructions = "You are responding to a Discord conversation."

        try:
            response_text = await asyncio.to_thread(
                self._blocking_generate,
                model_name=model_name,
                prompt=prompt,
                temperature=temperature,
                system_instructions=instructions
            )
            return response_text

        except Exception as e:
            print(f"Thread Error: {e}")
            return None