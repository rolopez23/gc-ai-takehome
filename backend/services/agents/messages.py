"""Shared message-building helpers for agents."""

import base64


def build_user_message(
    pdf_blob: bytes | None = None, text: str | None = None
) -> list[dict]:
    """Build user message list for an agent, from either a PDF blob or plain text.

    Returns a list with a single user message dict, suitable for passing
    to AgentRunner.run() as the messages argument.
    """
    if pdf_blob is None and text is None:
        raise ValueError("Either pdf_blob or text must be provided")

    if pdf_blob is not None:
        return [
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": base64.standard_b64encode(pdf_blob).decode("ascii"),
                        },
                    }
                ],
            }
        ]

    return [{"role": "user", "content": text}]
