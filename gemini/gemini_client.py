import os

from google import genai


DEFAULT_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.8-flash",
)

SYSTEM_INSTRUCTION = """
You are the AI assistant inside Taskagotchi, a desktop app designed to help
people notice and break out of doom-scrolling habits.

Be concise, practical, friendly, and non-judgmental.

When the user seems stuck in a scrolling loop:
- suggest one small, concrete action they can take immediately;
- prefer short breaks, intentional transitions, and realistic goals;
- do not shame or lecture the user;
- keep advice useful for someone sitting at a computer;
- answer normal questions too when the user asks them.

You are called Gemini inside the Taskagotchi interface.
""".strip()


class GeminiAssistant:
    def __init__(self, model=DEFAULT_MODEL):
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set.\n\n"
                "Set it before starting Taskagotchi.\n\n"
                'macOS/Linux:\n'
                'export GEMINI_API_KEY="your-key-here"\n\n'
                'Windows PowerShell:\n'
                '$env:GEMINI_API_KEY="your-key-here"'
            )

        self.model = model
        self.client = genai.Client(api_key=api_key)
        self.previous_interaction_id = None

    def ask(self, prompt):
        prompt = prompt.strip()

        if not prompt:
            return ""

        request = {
            "model": self.model,
            "input": prompt,
            "system_instruction": SYSTEM_INSTRUCTION,
        }

        if self.previous_interaction_id:
            request["previous_interaction_id"] = (
                self.previous_interaction_id
            )

        interaction = self.client.interactions.create(
            **request
        )

        self.previous_interaction_id = interaction.id

        return (
            interaction.output_text
            or "Gemini returned an empty response."
        )

    def new_chat(self):
        self.previous_interaction_id = None
