from collections.abc import AsyncGenerator

from openai import AsyncOpenAI
from transformers import AutoTokenizer

MODEL_NAME = "qwen2.5-coder-7b-instruct"

client = AsyncOpenAI(
    base_url="http://localhost:1234/v1",
    api_key="lm-studio",
)

tokenizer = AutoTokenizer.from_pretrained(
    "Qwen/Qwen2.5-Coder-7B-Instruct",
)


def count_tokens(text: str) -> int:
    return len(tokenizer.encode(text))


def count_message_tokens(message: dict) -> int:
    content = message.get("content", "")

    return count_tokens(content)


async def generate_stream(
    messages: list[dict],
) -> AsyncGenerator[str, None]:
    stream = await client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=0.7,
        stream=True,
    )

    async for chunk in stream:
        delta = chunk.choices[0].delta.content

        if delta:
            yield delta


async def generate_text(
    messages: list[dict],
    temperature: float = 0.2,
) -> str:
    response = await client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=temperature,
    )

    return response.choices[0].message.content or ""