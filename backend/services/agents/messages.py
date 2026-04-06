"""Shared message-building and prompt helpers for agents."""

import base64


def build_user_message(
    pdf_blob: bytes | None = None, text: str | None = None
) -> list[dict]:
    """Build user message list for an agent, from a PDF blob, plain text, or both.

    Returns a list with a single user message dict, suitable for passing
    to AgentRunner.run() as the messages argument.

    When both pdf_blob and text are provided, the message content includes
    both a document block and a text block (useful for the splitter agent).
    """
    if pdf_blob is None and text is None:
        raise ValueError("Either pdf_blob or text must be provided")

    content: list[dict] = []

    if pdf_blob is not None:
        content.append(
            {
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": base64.standard_b64encode(pdf_blob).decode("ascii"),
                },
            }
        )

    if text is not None:
        content.append({"type": "text", "text": text})

    # Single content block (text-only) can use the simple string format
    if len(content) == 1 and content[0].get("type") == "text":
        return [{"role": "user", "content": text}]

    return [{"role": "user", "content": content}]


def append_instructions(
    prompt: str,
    instructions: str | None,
    *,
    relevance_note: str | None = None,
) -> str:
    """Append user-provided instructions to a system prompt in a standard format.

    If instructions is None or empty, returns the prompt unchanged.
    An optional relevance_note is appended after the instructions block
    (e.g., "These instructions may not be relevant for this clause; if irrelevant, ignore.").
    """
    if not instructions:
        return prompt

    block = (
        f'\n\n## Additional instructions from reviewer\n"{instructions}"\n'
        "(Source: user-provided review instructions)"
    )
    if relevance_note:
        block += f"\n{relevance_note}"
    return prompt + block
