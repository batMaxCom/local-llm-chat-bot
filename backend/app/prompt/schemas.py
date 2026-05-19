from dataclasses import dataclass


@dataclass
class PromptBuildResult:
    messages: list[dict]
    total_tokens: int
    summary_tokens: int
    recent_tokens: int