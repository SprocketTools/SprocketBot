import asyncio
import random
import aiohttp
from typing import Protocol, Optional, List
from google import genai
from google.genai import types
import discord


class AITools(Protocol):
    async def get_response(self, prompt: str, temperature: float = None, instructions: str = None,
                           mode: str = "normal", attachments: List[discord.Attachment] = None) -> Optional[str]:
        ...


class GeminiAITools:
    def __init__(self, APIkeys: tuple[str, ...]):
        self.keys = APIkeys
        print("AI Tools initialized.")

    # --- INTERNAL HELPER (Runs on a separate thread) ---
    def _blocking_generate(self, model_name: str, prompt: str, temperature: float,
                           system_instructions: str, image_parts: List[types.Part] = None):
        try:
            gemini = genai.Client(api_key=random.choice(self.keys))

            # Prepare contents: [text_prompt, image1, image2, ...]
            contents = [prompt]
            if image_parts:
                contents.extend(image_parts)

            if "gemma" not in model_name:
                config_obj = types.GenerateContentConfig(
                    temperature=temperature,
                    system_instruction=system_instructions
                )
            else:
                config_obj = types.GenerateContentConfig(
                    temperature=temperature,
                    top_k=100,
                    top_p=0.95
                )
                # Manual system prompt injection for Gemma (it supports images natively now)
                # We modify the prompt string in the list, keeping images separate
                contents[
                    0] = f'''===INSTRUCTIONS TO APPLY TO YOUR PROMPT===\n{system_instructions}\n\n===PROMPT===\n{prompt}'''
                print(f"Gemma is running ({model_name}) with {len(image_parts or [])} images...")

            message = gemini.models.generate_content(
                model=model_name,
                contents=contents,
                config=config_obj
            )

            try:
                response_text = message.text
                if not response_text:
                    raise ValueError("Empty response text")
                return response_text

            except Exception:
                print("---!! AI BLOCKED !!---")
                return None

        except Exception as e:
            print(f"---!! AI ERROR !!--- {e}")
            return None

    # --- MAIN ASYNC FUNCTION ---
    async def get_response(self, prompt: str, temperature: float = None, instructions: str = None,
                           mode: str = "normal", attachments: List[discord.Attachment] = None) -> Optional[str]:
        if not temperature:
            temperature = 1.0

        model_name = 'models/gemini-2.5-flash'

        match mode:
            case "fast":
                model_name = 'models/gemini-2.5-flash-lite'
            case "normal":
                model_name = 'models/gemini-2.5-flash'
            case "smart":
                model_name = 'models/gemini-3-flash-preview'
            case "gemma" | "gemma-3-27b-it":
                model_name = 'models/gemma-3-27b-it'

        if not instructions:
            instructions = "You are responding to a Discord conversation."

        # --- PROCESS ATTACHMENTS ---
        image_parts = []
        if attachments:
            async with aiohttp.ClientSession() as session:
                for att in attachments:
                    if att.content_type and att.content_type.startswith("image/"):
                        try:
                            async with session.get(att.url) as resp:
                                if resp.status == 200:
                                    image_data = await resp.read()
                                    # Create the Part object for the SDK
                                    image_parts.append(
                                        types.Part.from_bytes(
                                            data=image_data,
                                            mime_type=att.content_type
                                        )
                                    )
                        except Exception as e:
                            print(f"Failed to download image {att.filename}: {e}")

        try:
            response_text = await asyncio.to_thread(
                self._blocking_generate,
                model_name=model_name,
                prompt=prompt,
                temperature=temperature,
                system_instructions=instructions,
                image_parts=image_parts
            )
            return response_text

        except Exception as e:
            print(f"Thread Error: {e}")
            return None