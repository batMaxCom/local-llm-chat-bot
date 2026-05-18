from collections.abc import Generator

from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:1234/v1",
    api_key="lm-studio",
)

MODEL_NAME = "qwen2.5-coder-7b-instruct"


def generate_stream(
    messages: list[dict],
) -> Generator[str, None, None]:
    stream = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=0.7,
        stream=True,
    )

    for chunk in stream:
        delta = chunk.choices[0].delta.content

        if delta:
            yield delta


def generate_text(
    messages: list[dict],
    temperature: float = 0.2,
) -> str:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=temperature,
    )

    return response.choices[0].message.content or ""
