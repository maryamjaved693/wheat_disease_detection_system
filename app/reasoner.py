
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, Any, List

from config import LOW_CONFIDENCE_THRESHOLD
from rdf_knowledge import WheatKnowledgeBase, DiseaseFacts


@dataclass
class ReasoningResult:
    disease_label: str
    clip_confidence: float
    risk_level: str
    is_low_confidence: bool
    facts: Dict[str, Any]
    symptom_evidence: List[str]
    explanation_trace: List[str]


class WheatReasoner:
    """Simple rule-based layer on top of RDF facts + CLIP/NLP outputs."""

    def __init__(self, kb: WheatKnowledgeBase | None = None):
        self.kb = kb or WheatKnowledgeBase()

    def reason(
        self,
        disease_label: str,
        clip_confidence: float,
        text_symptoms: List[str] | None = None,
    ) -> ReasoningResult:
        facts_obj: DiseaseFacts | None = self.kb.get_disease_facts(disease_label)
        facts_dict: Dict[str, Any] = self.kb.to_dict(facts_obj)

        explanation_trace: List[str] = []
        symptom_evidence: List[str] = []

        # Symptom cross-check (very simple)
        if text_symptoms and facts_obj is not None:
            matched = []
            for sym in facts_obj.symptoms:
                for ts in text_symptoms:
                    if ts.lower() in sym.lower() or sym.lower() in ts.lower():
                        matched.append(sym)
                        break
            if matched:
                symptom_evidence = matched
                explanation_trace.append(
                    f"Text symptoms {text_symptoms} match RDF symptoms {matched} for {disease_label}."
                )
            else:
                explanation_trace.append(
                    f"Text symptoms {text_symptoms} did NOT clearly match RDF symptoms for {disease_label}."
                )

        # Risk level based on confidence only
        if clip_confidence >= 0.7:
            risk_level = "High"
        elif clip_confidence >= 0.4:
            risk_level = "Medium"
        else:
            risk_level = "Low"

        is_low_confidence = clip_confidence < LOW_CONFIDENCE_THRESHOLD
        if is_low_confidence:
            explanation_trace.append(
                f"CLIP confidence {clip_confidence:.2f} is below threshold {LOW_CONFIDENCE_THRESHOLD:.2f} -> Suggest human verification."
            )

        return ReasoningResult(
            disease_label=disease_label,
            clip_confidence=clip_confidence,
            risk_level=risk_level,
            is_low_confidence=is_low_confidence,
            facts=facts_dict,
            symptom_evidence=symptom_evidence,
            explanation_trace=explanation_trace,
        )

    def to_dict(self, result: ReasoningResult) -> Dict[str, Any]:
        return asdict(result)
