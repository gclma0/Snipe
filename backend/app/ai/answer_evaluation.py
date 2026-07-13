import re
from typing import Literal

from pydantic import BaseModel, Field

ANSWER_EVALUATION_VERSION = "deterministic-answer-evaluation-v1"


class AnswerEvaluationResult(BaseModel):
    output_type: str = "interview_answer_evaluation"
    output_version: str = ANSWER_EVALUATION_VERSION
    relevance_score: int = Field(ge=0, le=100)
    clarity_score: int = Field(ge=0, le=100)
    evidence_score: int = Field(ge=0, le=100)
    depth_score: int = Field(ge=0, le=100)
    confidence_score: int = Field(ge=0, le=100)
    overall_score: int = Field(ge=0, le=100)
    star_feedback: list[str] = Field(default_factory=list, max_length=6)
    strengths: list[str] = Field(default_factory=list, max_length=5)
    improvements: list[str] = Field(default_factory=list, max_length=5)
    improved_answer: str
    follow_up_question: str
    cautions: list[str] = Field(default_factory=list, max_length=5)


def evaluate_answer(
    *,
    question: str,
    answer: str,
    evidence_to_use: list[str],
    category: str | None = None,
) -> AnswerEvaluationResult:
    cleaned_answer = _clean(answer)
    question_terms = _terms(question)
    answer_terms = _terms(cleaned_answer)
    evidence_terms = {term for item in evidence_to_use for term in _terms(item)}

    relevance = _score_overlap(question_terms, answer_terms)
    evidence = (
        _score_overlap(evidence_terms, answer_terms)
        if evidence_terms
        else _evidence_score(answer)
    )
    clarity = _clarity_score(cleaned_answer)
    depth = _depth_score(cleaned_answer)
    confidence = _confidence_score(cleaned_answer)
    overall = round(
        (relevance * 0.25)
        + (clarity * 0.2)
        + (evidence * 0.25)
        + (depth * 0.2)
        + (confidence * 0.1)
    )

    strengths = _strengths(relevance, clarity, evidence, depth)
    improvements = _improvements(relevance, clarity, evidence, depth, confidence, evidence_to_use)
    return AnswerEvaluationResult(
        relevance_score=relevance,
        clarity_score=clarity,
        evidence_score=evidence,
        depth_score=depth,
        confidence_score=confidence,
        overall_score=overall,
        star_feedback=_star_feedback(cleaned_answer),
        strengths=strengths,
        improvements=improvements,
        improved_answer=_improved_answer(
            answer=cleaned_answer,
            evidence_to_use=evidence_to_use,
            improvements=improvements,
        ),
        follow_up_question=_follow_up_question(
            category=category,
            evidence_score=evidence,
            depth_score=depth,
        ),
        cautions=[
            (
                "Do not add achievements, metrics, tools, employers, or responsibilities "
                "unless they are true."
            ),
            "Use bracketed placeholders only for details you still need to verify.",
        ],
    )


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _terms(value: str) -> set[str]:
    return {
        term
        for term in re.findall(r"[a-z0-9+#.]+", value.lower())
        if len(term) > 2 and term not in {"the", "and", "for", "with", "that", "this"}
    }


def _score_overlap(expected: set[str], actual: set[str]) -> int:
    if not expected:
        return 60 if actual else 0
    return min(100, round((len(expected & actual) / len(expected)) * 100))


def _clarity_score(answer: str) -> int:
    word_count = len(answer.split())
    if word_count < 12:
        return 35
    if word_count > 220:
        return 70
    sentences = max(1, len(re.findall(r"[.!?]", answer)))
    avg_words = word_count / sentences
    return 85 if avg_words <= 35 else 65


def _evidence_score(answer: str) -> int:
    has_specifics = bool(
        re.search(r"\b(project|built|created|led|used|improved|reported)\b", answer, re.I)
    )
    has_result = bool(
        re.search(r"\b(result|outcome|impact|reduced|increased|delivered)\b", answer, re.I)
    )
    return 80 if has_specifics and has_result else 55 if has_specifics else 30


def _depth_score(answer: str) -> int:
    word_count = len(answer.split())
    if word_count >= 80:
        return 85
    if word_count >= 40:
        return 70
    if word_count >= 18:
        return 50
    return 25


def _confidence_score(answer: str) -> int:
    hedges = len(re.findall(r"\b(maybe|probably|kind of|sort of|i guess|not sure)\b", answer, re.I))
    if not answer:
        return 0
    return max(35, 85 - hedges * 15)


def _star_feedback(answer: str) -> list[str]:
    checks: list[tuple[str, Literal["present", "missing"]]] = [
        (
            "Situation",
            "present" if re.search(r"\bwhen|while|in my|during\b", answer, re.I) else "missing",
        ),
        (
            "Task",
            "present"
            if re.search(r"\bneeded|responsible|goal|task\b", answer, re.I)
            else "missing",
        ),
        (
            "Action",
            "present"
            if re.search(r"\bi built|i created|i led|i used|i analyzed|i worked\b", answer, re.I)
            else "missing",
        ),
        (
            "Result",
            "present"
            if re.search(r"\bresult|outcome|impact|delivered|improved\b", answer, re.I)
            else "missing",
        ),
    ]
    return [f"{name}: {state}." for name, state in checks]


def _strengths(relevance: int, clarity: int, evidence: int, depth: int) -> list[str]:
    strengths = []
    if relevance >= 70:
        strengths.append("The answer addresses the question directly.")
    if clarity >= 70:
        strengths.append("The answer is understandable and concise.")
    if evidence >= 70:
        strengths.append("The answer uses evidence connected to the profile.")
    if depth >= 70:
        strengths.append("The answer gives enough detail for follow-up discussion.")
    return strengths or ["The answer gives a starting point for interview practice."]


def _improvements(
    relevance: int,
    clarity: int,
    evidence: int,
    depth: int,
    confidence: int,
    evidence_to_use: list[str],
) -> list[str]:
    improvements = []
    if relevance < 70:
        improvements.append("Answer the exact question before adding background context.")
    if evidence < 70:
        improvements.append("Add a truthful example from verified profile evidence.")
    if depth < 70:
        improvements.append("Add scope, action, and result details using the STAR method.")
    if clarity < 70:
        improvements.append("Shorten the answer and use clearer sequence.")
    if confidence < 70:
        improvements.append("Replace uncertain phrasing with accurate, specific wording.")
    if evidence_to_use:
        improvements.append("Prepare the cited evidence before using this answer in an interview.")
    return improvements[:5]


def _improved_answer(*, answer: str, evidence_to_use: list[str], improvements: list[str]) -> str:
    base = answer or "I would answer with a real example from my profile."
    evidence = evidence_to_use[0] if evidence_to_use else "[verified example from my profile]"
    return (
        f"{base} I would strengthen this by clearly stating the situation, my task, the "
        f"specific action I took, and the true result. Evidence to use: {evidence}. "
        "I would only include metrics or achievements after verifying they are accurate."
    )


def _follow_up_question(*, category: str | None, evidence_score: int, depth_score: int) -> str:
    if evidence_score < 70:
        return "What concrete evidence can you provide to support that answer?"
    if depth_score < 70:
        return "What was your exact role, and what changed because of your actions?"
    if category == "technical":
        return "What tradeoff or limitation did you encounter while doing that work?"
    return "What would you do differently if you faced the same situation again?"
