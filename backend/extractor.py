class SemanticExtractor:

    async def extract(
        self,
        messages: list[dict],
    ) -> list[str]:
        ...