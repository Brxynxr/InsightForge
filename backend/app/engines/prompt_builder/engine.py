from app.engines.base import BaseEngine, EngineContext


class PromptBuilderEngine(BaseEngine):
    """Builds prompts for the LLM. Contains no business logic."""

    def __init__(self, system_prompt: str = "", template: str | None = None) -> None:
        self.system_prompt = system_prompt
        self.template = template or "Process the following text:\n\n{{text}}"

    def execute(self, context: EngineContext) -> EngineContext:
        prompts = []
        for record in context.records:
            text = record.get("optimized_text", record.get("text", ""))
            prompt = self.template.replace("{{text}}", text)
            prompts.append({"system": self.system_prompt, "user": prompt})
        context.metadata["prompts"] = prompts
        return context
