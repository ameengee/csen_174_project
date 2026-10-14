import base64
from typing import Any

from backend.configs.exceptions import InvalidRequestError

def build_profile_content(data: bytes) -> list[dict[str, Any]]:
    """Return OpenAI input content parts for an uploaded PDF or LinkedIn export zip."""
    if data.startswith(b"%PDF"):
        return [
            {
                "type": "input_file",
                "filename": "linkedin_profile.pdf",
                "file_data": "data:application/pdf;base64,"
                + base64.b64encode(data).decode("ascii"),
            }
        ]
    raise InvalidRequestError("Upload a LinkedIn profile PDF or the LinkedIn data export .zip")
