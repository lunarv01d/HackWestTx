import json
import ssl
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import certifi


TASKAGOTCHI_API_URL = (
    "https://taskagotchi-api-284899401668.us-central1.run.app"
)

# The actual Gemini model is selected by the Cloud Run backend.
DEFAULT_MODEL = "Taskagotchi Cloud"

# Use certifi's CA bundle explicitly. This avoids Python installations
# on macOS that do not automatically use the system Keychain trust store.
SSL_CONTEXT = ssl.create_default_context(
    cafile=certifi.where()
)


class GeminiAssistant:
    def __init__(self, base_url=TASKAGOTCHI_API_URL):
        self.base_url = base_url.rstrip("/")
        self.previous_interaction_id = None

        if not self.base_url.startswith("https://"):
            raise RuntimeError(
                "Taskagotchi's Gemini backend must use HTTPS."
            )

    def ask(self, prompt):
        prompt = prompt.strip()

        if not prompt:
            return ""

        payload = {
            "prompt": prompt,
            "previous_interaction_id": self.previous_interaction_id,
        }

        request = Request(
            f"{self.base_url}/api/gemini",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "Taskagotchi/1.0",
            },
            method="POST",
        )

        try:
            with urlopen(
                request,
                timeout=45,
                context=SSL_CONTEXT,
            ) as response:
                response_body = response.read().decode("utf-8")

        except HTTPError as exc:
            raw_error = exc.read().decode(
                "utf-8",
                errors="replace",
            )

            try:
                error_data = json.loads(raw_error)
                message = error_data.get(
                    "error",
                    raw_error,
                )
            except json.JSONDecodeError:
                message = raw_error

            raise RuntimeError(
                f"Taskagotchi API error ({exc.code}): {message}"
            ) from exc

        except URLError as exc:
            raise RuntimeError(
                "Could not reach the Taskagotchi API.\n\n"
                f"{exc.reason}"
            ) from exc

        except TimeoutError as exc:
            raise RuntimeError(
                "The Taskagotchi API request timed out."
            ) from exc

        try:
            data = json.loads(response_body)

        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Taskagotchi API returned an invalid response."
            ) from exc

        interaction_id = data.get("interaction_id")

        if interaction_id:
            self.previous_interaction_id = interaction_id

        text = data.get("text", "")

        if not isinstance(text, str):
            text = str(text)

        return (
            text
            or "Gemini returned an empty response."
        )

    def new_chat(self):
        self.previous_interaction_id = None
