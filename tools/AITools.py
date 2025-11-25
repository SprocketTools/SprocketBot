import asyncio
import random
from typing import Protocol
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
        """
        This function handles the synchronous (blocking) Google API call.
        """
        try:
            # Re-initialize client per call to be thread-safe/key-safe
            gemini = genai.Client(api_key=random.choice(self.keys))

            # Create the specific config object your library expects
            config_obj = types.GenerateContentConfig(
                temperature=temperature,
                system_instruction=system_instructions
            )

            # The BLOCKING call
            message = gemini.models.generate_content(
                model=model_name,
                contents=[prompt],
                config=config_obj
            )

            # --- CHANGED: Safer text extraction ---
            # Instead of checking .parts (which caused the error), we try to access .text directly.
            # If the response was blocked by safety filters, accessing .text usually raises an error,
            # which we catch below.
            try:
                response_text = message.text
                if not response_text:
                    raise ValueError("Empty response text")
                return response_text

            except Exception:
                # This block handles cases where the AI refused to answer (safety filter)
                print("---!! AI BLOCKED !!---")
                if hasattr(message, 'prompt_feedback'):
                    print(f"Safety Feedback: {message.prompt_feedback}")
                return "Apologies Tony, I cannot comply."

        except Exception as e:
            print(f"---!! AI ERROR !!--- {e}")
            return "Sir, I am experiencing a connection failure."

    # --- MAIN ASYNC FUNCTION (Called by the bot) ---
    async def get_response(self, prompt: str, temperature: float = None, instructions: str = None,
                           mode: str = "normal") -> str:
        if not temperature:
            temperature = 1.0

        # Model selection
        model_name = 'models/gemini-2.5-flash'
        match mode:
            case "fast":
                model_name = 'models/gemini-2.5-flash-lite'
            case "normal":
                model_name = 'models/gemini-2.5-flash'
            case "smart":
                model_name = 'models/gemini-2.5-pro'

        if not instructions:
            instructions = "You are responding to a Discord conversation."

        # Run the blocking function in a separate thread
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
            return "Sir, internal system failure."