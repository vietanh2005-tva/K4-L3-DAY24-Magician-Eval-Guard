from __future__ import annotations

"""Phase C: Presidio PII, NeMo input/output decisions and measured input latency."""

import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import GUARDRAILS_CONFIG_DIR, PRESIDIO_ENTITIES, PRESIDIO_LANGUAGE, PRESIDIO_NLP_MODEL


def setup_presidio():
    """Use real Presidio engines, default recognizers and Vietnamese ID/phone patterns."""
    from presidio_analyzer import AnalyzerEngine, RecognizerRegistry, Pattern, PatternRecognizer
    from presidio_analyzer.nlp_engine import NlpEngineProvider
    from presidio_anonymizer import AnonymizerEngine

    cccd_recognizer = PatternRecognizer(
        supported_entity="VN_CCCD",
        patterns=[
            Pattern("CCCD 12 digits", r"\b\d{12}\b", 0.9),
            Pattern("CMND 9 digits", r"\b\d{9}\b", 0.7),
        ],
    )
    phone_recognizer = PatternRecognizer(
        supported_entity="VN_PHONE",
        patterns=[Pattern("VN mobile", r"\b0[3-9]\d{8}\b", 0.9)],
    )
    registry = RecognizerRegistry()
    registry.load_predefined_recognizers()
    registry.add_recognizer(cccd_recognizer)
    registry.add_recognizer(phone_recognizer)
    nlp_engine = NlpEngineProvider(nlp_configuration={
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": PRESIDIO_LANGUAGE, "model_name": PRESIDIO_NLP_MODEL}],
    }).create_engine()
    return AnalyzerEngine(registry=registry, nlp_engine=nlp_engine,
                         supported_languages=[PRESIDIO_LANGUAGE]), AnonymizerEngine()


def pii_scan(text: str, analyzer=None, anonymizer=None) -> dict:
    """Task 9a: return actual Presidio spans and anonymization, preserving clean text."""
    if not isinstance(text, str):
        raise ValueError("PII input must be text")
    if analyzer is None or anonymizer is None:
        analyzer, anonymizer = setup_presidio()
    # Day24's PII layer targets IDs, phones and email. English NER and foreign
    # identifier recognizers misclassify Vietnamese policy prose (see baseline).
    # NeMo separately checks requests for confidential employee information.
    results = [result for result in analyzer.analyze(text=text, language=PRESIDIO_LANGUAGE)
               if result.entity_type in PRESIDIO_ENTITIES]
    if not results:
        return {"has_pii": False, "entities": [], "anonymized": text}
    entities = [
        {"type": result.entity_type, "text": text[result.start:result.end],
         "score": round(result.score, 3), "start": result.start, "end": result.end}
        for result in results
    ]
    anonymized = anonymizer.anonymize(text=text, analyzer_results=results).text
    return {"has_pii": True, "entities": entities, "anonymized": anonymized}


def setup_nemo_rails():
    """Load the supplied Colang 1.0 policy with NeMo Guardrails 0.10.0."""
    from nemoguardrails import RailsConfig, LLMRails

    return LLMRails(RailsConfig.from_path(GUARDRAILS_CONFIG_DIR))


def _rail_decision(result) -> tuple[bool, str]:
    """Require the requested rail's execution log; missing evidence never means safe."""
    try:
        activated = result.log.activated_rails
        response = result.response[0]["content"]
    except (AttributeError, TypeError, KeyError, IndexError) as error:
        raise ValueError("NeMo did not return its response and activated rail log") from error
    if not activated or any(type(getattr(rail, "stop", None)) is not bool for rail in activated):
        raise ValueError("NeMo did not log a valid rail decision")
    if not isinstance(response, str):
        raise ValueError("NeMo response must be text")
    return any(rail.stop for rail in activated), response


async def check_input_rail(text: str, rails=None) -> dict:
    """Task 9b: use input rails only and their stop decision, never refusal keywords."""
    if rails is None:
        rails = setup_nemo_rails()
    result = await rails.generate_async(
        messages=[{"role": "user", "content": text}],
        options={"rails": ["input"], "log": {"activated_rails": True}},
    )
    blocked, response = _rail_decision(result)
    return {"allowed": not blocked,
            "blocked_reason": "nemo_input_rail" if blocked else None,
            "response": response}


async def check_output_rail(question: str, answer: str, rails=None) -> dict:
    """Task 11: inspect the supplied answer in context and preserve safe answers exactly."""
    if rails is None:
        rails = setup_nemo_rails()
    result = await rails.generate_async(
        messages=[{"role": "user", "content": question},
                  {"role": "assistant", "content": answer}],
        options={"rails": ["output"], "log": {"activated_rails": True}},
    )
    flagged, response = _rail_decision(result)
    if flagged and (not response.strip() or response == answer):
        raise ValueError("NeMo flagged output without providing a safe replacement")
    return {"safe": not flagged,
            "flagged_reason": "nemo_output_rail" if flagged else None,
            "final_answer": response if flagged else answer}


def run_adversarial_suite(adversarial_set: list[dict],
                          rails=None, analyzer=None, anonymizer=None) -> list[dict]:
    """Task 10: one event loop and shared engines; PII blocks before NeMo is called."""
    if analyzer is None or anonymizer is None:
        analyzer, anonymizer = setup_presidio()
    if rails is None:
        rails = setup_nemo_rails()

    async def run_all():
        rows = []
        for item in adversarial_set:
            blocked_by = None
            if pii_scan(item["input"], analyzer, anonymizer)["has_pii"]:
                blocked_by = "presidio"
            else:
                result = await check_input_rail(item["input"], rails)
                if not result["allowed"]:
                    blocked_by = "nemo_input"
            actual = "blocked" if blocked_by else "allowed"
            rows.append({
                "id": item["id"], "category": item["category"], "input": item["input"],
                "expected": item["expected"], "actual": actual, "blocked_by": blocked_by,
                "passed": actual == item["expected"],
            })
        return rows

    return asyncio.run(run_all())


def measure_p95_latency(test_inputs: list[str], n_runs: int = 20,
                         rails=None, analyzer=None, anonymizer=None) -> dict:
    """Task 12: measure both INPUT layers, with two excluded real warm-ups.

    Engines are initialized before measurement. Each timed sample always runs
    Presidio and NeMo input sequentially, including when Presidio detects PII.
    Raw milliseconds remain unmodified; this is not RAG or full request latency.
    """
    from src.experiment_support import summarize_latency

    if not test_inputs or type(n_runs) is not int or n_runs < 1:
        raise ValueError("Need inputs and an integer n_runs >= 1")
    if any(not isinstance(text, str) or not text.strip() for text in test_inputs):
        raise ValueError("Latency inputs must be non-empty text")
    if analyzer is None or anonymizer is None:
        analyzer, anonymizer = setup_presidio()
    if rails is None:
        rails = setup_nemo_rails()

    async def measure():
        for i in range(2):
            text = test_inputs[i % len(test_inputs)]
            pii_scan(text, analyzer, anonymizer)
            await check_input_rail(text, rails)
        samples = []
        for i in range(n_runs):
            text = test_inputs[i % len(test_inputs)]
            start = time.perf_counter()
            pii_scan(text, analyzer, anonymizer)
            pii_ms = (time.perf_counter() - start) * 1000
            start = time.perf_counter()
            await check_input_rail(text, rails)
            nemo_ms = (time.perf_counter() - start) * 1000
            samples.append({"presidio_ms": pii_ms, "nemo_input_ms": nemo_ms,
                            "input_guard_ms": pii_ms + nemo_ms})
        return samples

    return summarize_latency(asyncio.run(measure()), warmup_runs=2)


if __name__ == "__main__":
    from scripts.run_experiments import main
    raise SystemExit(main(["--phase", "c", *sys.argv[1:]]))
