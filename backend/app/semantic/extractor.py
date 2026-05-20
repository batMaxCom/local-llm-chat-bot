import json
import re

from app.const import SEMANTIC_EXTRACTION_PROMPT
from app.llm import generate_text

from app.semantic.schemas import (
    SemanticFact,
)


class SemanticExtractor:

    async def extract(
        self,
        messages: list[dict],
    ) -> list[SemanticFact]:
        conversation_text = (
            self._messages_to_text(
                messages,
            )
        )

        prompt = [
            {
                "role": "system",
                "content": (
                    SEMANTIC_EXTRACTION_PROMPT
                ),
            },
            {
                "role": "user",
                "content": conversation_text,
            },
        ]

        response = await generate_text(
            messages=prompt,
            temperature=0.1,
        )

        try:
            parsed = self._parse_json_response(response)

        except Exception as e:
            return []

        facts = []

        for item in parsed:
            category = item.get(
                "category",
            )

            content = item.get(
                "content",
            )

            if not category or not content:
                continue

            facts.append(
                SemanticFact(
                    category=category,
                    content=content,
                )
            )

        return facts

    @staticmethod
    def _parse_json_response(
            response: str,
    ) -> list[dict]:
        match = re.search(
            r"\[.*\]",
            response,
            re.DOTALL,
        )

        if not match:
            return []

        json_content = match.group(0)

        return json.loads(
            json_content,
        )

    @staticmethod
    def _messages_to_text(
        messages: list[dict],
    ) -> str:
        lines = []

        for message in messages:
            role = message["role"]

            content = message["content"]

            lines.append(
                f"{role.upper()}: {content}"
            )

        return "\n".join(lines)