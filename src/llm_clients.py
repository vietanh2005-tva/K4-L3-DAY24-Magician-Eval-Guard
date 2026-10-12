"""Shared provider configuration for answering and RAGAS (lazy imports).

Keep credentials in OPENAI_API_KEY, including Gemini/OpenRouter credentials.
RAGAS embeddings are separate from the local bge-m3 retrieval embeddings.
"""

from functools import lru_cache

import config
from src.api_pacing import API_PACER


def _http_options(include_async=True):
    """Pace personal providers; preserve the teacher's OpenAI behavior.

    Each SDK owns its HTTP clients. Async clients must not be cached across
    baseline/production evaluations, which can run in different event loops.
    Only the pacer is shared, so all clients consume the same request budget.
    """
    if config.LLM_PROVIDER == "openai":
        return {}
    import httpx

    options = {"http_client": httpx.Client(event_hooks={"request": [API_PACER.wait]})}
    if include_async:
        options["http_async_client"] = httpx.AsyncClient(
            event_hooks={"request": [API_PACER.wait_async]})
    return options


@lru_cache(maxsize=1)
def create_llm_client():
    from openai import OpenAI

    if config.LLM_PROVIDER != "openai":
        print("  API pacing: at most 12 requests/minute, shared by chat and evaluation", flush=True)
    return OpenAI(api_key=config.OPENAI_API_KEY, base_url=config.OPENAI_BASE_URL,
                  **_http_options(include_async=False))


def create_ragas_llm():
    from langchain_openai import ChatOpenAI

    chat = ChatOpenAI(model=config.RAGAS_LLM_MODEL, temperature=0,
                      api_key=config.OPENAI_API_KEY, base_url=config.OPENAI_BASE_URL,
                      **_http_options())
    if config.LLM_PROVIDER == "openai":
        return chat

    # RAGAS answer_relevancy requests multiple completions. Some compatible
    # endpoints/models only return one choice, even when n > 1 is requested.
    # Send separate n=1 requests and regroup actual responses for RAGAS.
    from ragas.llms import LangchainLLMWrapper

    class SingleCompletionWrapper(LangchainLLMWrapper):
        @staticmethod
        def _combine(result, n):
            if len(result.generations) != n or any(not group for group in result.generations):
                raise ValueError("Evaluation provider returned incomplete completions")
            result.generations = [[group[0] for group in result.generations]]
            return result

        def generate_text(self, prompt, n=1, temperature=None, stop=None, callbacks=None):
            if n <= 0:
                raise ValueError("n must be positive")
            result = self.langchain_llm.generate_prompt(
                prompts=[prompt] * n, n=1,
                temperature=self.get_temperature(n) if temperature is None else temperature,
                stop=stop, callbacks=callbacks,
            )
            return self._combine(result, n)

        async def agenerate_text(self, prompt, n=1, temperature=None, stop=None, callbacks=None):
            if n <= 0:
                raise ValueError("n must be positive")
            result = await self.langchain_llm.agenerate_prompt(
                prompts=[prompt] * n, n=1,
                temperature=self.get_temperature(n) if temperature is None else temperature,
                stop=stop, callbacks=callbacks,
            )
            return self._combine(result, n)

    return SingleCompletionWrapper(chat)


def create_ragas_embeddings():
    from langchain_openai import OpenAIEmbeddings

    return OpenAIEmbeddings(
        model=config.RAGAS_EMBEDDING_MODEL,
        api_key=config.OPENAI_API_KEY,
        base_url=config.OPENAI_BASE_URL,
        # Send text strings, not OpenAI tiktoken IDs, to compatible endpoints.
        check_embedding_ctx_length=False,
        model_kwargs={"encoding_format": "float"},
        **_http_options(),
    )
