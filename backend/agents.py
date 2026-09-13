"""
Core agent classes for the AI Agent Swarm.

This is the same 4-agent pipeline from agent_swarm.py (Generator, Evaluator,
Selector, Formatter), refactored so it can be imported by both the original
CLI/GitHub Actions script and the new API server, and so each stage can
report its progress via an optional callback instead of only printing to
stdout.
"""
import json
import time
import os
from google import genai

API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash-lite")

# Seconds to wait between calls to respect the Gemini free tier rate limit.
# Override with GEMINI_CALL_DELAY if your quota allows faster calls.
CALL_DELAY = float(os.environ.get("GEMINI_CALL_DELAY", "35"))

_client = None


def get_client():
    global _client
    if _client is None:
        if not API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Export it before starting the server."
            )
        _client = genai.Client(api_key=API_KEY)
    return _client


def call_gemini(prompt: str) -> str: time.sleep(CALL_DELAY) response = get_client().models.generate_content( model=MODEL, contents=prompt, ) return response.text Replace the whole thing with: def call_gemini(prompt: str) -> str: time.sleep(CALL_DELAY) max_attempts = 4 backoff = 20 # seconds, doubles each retry for attempt in range(1, max_attempts + 1): try: response = get_client().models.generate_content( model=MODEL, contents=prompt, ) return response.text except Exception as exc: message = str(exc) is_transient = any( marker in message for marker in ("503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED", "overloaded") ) if not is_transient or attempt == max_attempts: raise time.sleep(backoff) backoff *= 2 raise RuntimeError("Gemini call failed after retries.")
    return response.text


def _extract_json(response_text: str) -> dict:
    start_idx = response_text.find("{")
    end_idx = response_text.rfind("}") + 1
    json_str = response_text[start_idx:end_idx]
    return json.loads(json_str)


class GeneratorAgent:
    def generate(self, prompt: str) -> str:
        full_prompt = f"""You are an expert copywriter specializing in sales emails.
        Generate a professional, compelling sales email based on the user's prompt.
        The email should be concise, engaging, and include a clear call-to-action.

        Email Prompt: {prompt}"""
        return call_gemini(full_prompt)


class EvaluatorAgent:
    def evaluate(self, email: str) -> dict:
        evaluation_prompt = f"""Evaluate the following sales email on three dimensions:
1. Clarity (1-10): How clear and easy to understand is the message?
2. CTA (1-10): How effective is the call-to-action?
3. Tone (1-10): How appropriate and professional is the tone?

Email:
{email}

Respond in JSON format only, no extra text, no markdown, just raw JSON like this:
{{"clarity": 8, "cta": 7, "tone": 9, "overall_score": 8, "feedback": "your feedback here"}}"""

        response_text = call_gemini(evaluation_prompt)
        try:
            return _extract_json(response_text)
        except Exception:
            return {
                "clarity": 5,
                "cta": 5,
                "tone": 5,
                "overall_score": 5,
                "feedback": response_text,
            }


class SelectorAgent:
    def select_best(self, candidates: list, evaluations: list) -> tuple:
        selection_prompt = (
            "You are an expert email reviewer. Based on the scores below, "
            "select the best email.\n\nCandidates:\n"
        )

        for i, (email, eval_score) in enumerate(zip(candidates, evaluations)):
            selection_prompt += f"\n--- Candidate {i+1} ---\n"
            selection_prompt += f"Overall Score: {eval_score.get('overall_score', 0)}\n"
            selection_prompt += (
                f"Clarity: {eval_score.get('clarity', 0)}, "
                f"CTA: {eval_score.get('cta', 0)}, "
                f"Tone: {eval_score.get('tone', 0)}\n"
            )
            selection_prompt += f"Feedback: {eval_score.get('feedback', '')}\n"

        selection_prompt += (
            '\nRespond in JSON format only, no extra text, no markdown, just raw '
            'JSON like this: {"best_candidate": 1, "rationale": "reason here"}'
        )

        response_text = call_gemini(selection_prompt)
        try:
            result = _extract_json(response_text)
            return int(result.get("best_candidate", 1)) - 1, result.get("rationale", "")
        except Exception:
            return 0, response_text


class FormatterAgent:
    def format(self, email: str) -> str:
        formatting_prompt = f"""Polish and format the following sales email for final delivery.
Ensure it has:
- A suggested subject line at the top
- Correct grammar and punctuation
- Professional formatting with proper line breaks
- A compelling closing

Email:
{email}"""
        return call_gemini(formatting_prompt)


class EmailAgentSwarm:
    """Runs the 4-stage pipeline, reporting progress through on_update."""

    def __init__(self):
        self.generator = GeneratorAgent()
        self.evaluator = EvaluatorAgent()
        self.selector = SelectorAgent()
        self.formatter = FormatterAgent()

    def generate_email(self, prompt: str, on_update=None) -> dict:
        def emit(**patch):
            if on_update:
                on_update(patch)

        candidates = []
        evaluations = []

        emit(stage="generator", stage_status="running")
        for i in range(3):
            emit(stage="generator", stage_status="running", detail=f"Generating version {i+1}/3")
            candidates.append(self.generator.generate(prompt))
            emit(stage="generator", candidates=list(candidates))
        emit(stage="generator", stage_status="done")

        emit(stage="evaluator", stage_status="running")
        for i, email in enumerate(candidates):
            emit(stage="evaluator", stage_status="running", detail=f"Evaluating version {i+1}/3")
            scores = self.evaluator.evaluate(email)
            evaluations.append(scores)
            emit(stage="evaluator", evaluations=list(evaluations))
        emit(stage="evaluator", stage_status="done")

        emit(stage="selector", stage_status="running", detail="Selecting the best version")
        best_idx, rationale = self.selector.select_best(candidates, evaluations)
        emit(
            stage="selector",
            stage_status="done",
            best_index=best_idx,
            selection_rationale=rationale,
        )

        emit(stage="formatter", stage_status="running", detail="Formatting final email")
        final_email = self.formatter.format(candidates[best_idx])
        emit(stage="formatter", stage_status="done", final_email=final_email)

        return {
            "original_prompt": prompt,
            "candidates": candidates,
            "evaluations": evaluations,
            "best_index": best_idx,
            "selection_rationale": rationale,
            "final_email": final_email,
        }
