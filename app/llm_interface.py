
from __future__ import annotations

import os
from typing import Dict, Any

import json

try:
    import openai
except ImportError:  # type: ignore
    openai = None  # type: ignore

try:
    from groq import Groq
except ImportError:  # type: ignore
    Groq = None  # type: ignore


def build_prompt(structured_result: Dict[str, Any]) -> str:
    """Create a prompt for the LLM from reasoning + RDF results."""
    facts = structured_result.get("facts", {})
    disease_name = structured_result.get("disease_label") or facts.get("disease_name", "Unknown disease")
    pathogen = facts.get("pathogen", "Unknown pathogen")
    symptoms = facts.get("symptoms", [])
    treatments = facts.get("treatments", [])
    conditions = facts.get("conditions", [])
    plant_parts = facts.get("plant_parts", [])
    hosts = facts.get("hosts", [])
    risk_level = structured_result.get("risk_level", "Unknown")
    clip_conf = structured_result.get("clip_confidence", 0.0)
    is_low_conf = structured_result.get("is_low_confidence", False)
    symptom_evidence = structured_result.get("symptom_evidence", [])

    # Build symptom description
    symptom_text = ""
    if symptoms:
        symptom_text = "\n".join([f"- {s}" for s in symptoms[:3]])  # Limit to first 3
    
    # Build condition description
    condition_text = ""
    if conditions:
        condition_text = conditions[0] if conditions else ""

    # Build treatment description
    treatment_text = ""
    if treatments:
        treatment_text = "\n".join([f"- {t}" for t in treatments])

    base = f"""You are an expert agronomist and plant pathologist helping a farmer diagnose wheat diseases.

**Disease Information:**
- Disease Name: {disease_name}
- Pathogen: {pathogen}
- CLIP Model Confidence: {clip_conf:.1%}
- Risk Level: {risk_level}

**Symptoms:**
{symptom_text if symptom_text else "No specific symptoms provided"}

**Environmental Conditions:**
{condition_text if condition_text else "No specific conditions provided"}

**Affected Plant Parts:**
{', '.join(plant_parts) if plant_parts else "Not specified"}

**Available Treatment/Management Options:**
{treatment_text if treatment_text else "No specific treatments available in knowledge base - provide general management advice based on best practices"}

Write a clear, helpful diagnosis report in markdown format that includes:

1. **Diagnosis**: Clearly state the predicted disease and confidence level
2. **Symptoms**: Describe the key symptoms in simple, farmer-friendly language
3. **Pathogen**: Explain what causes this disease
4. **Risk Assessment**: Explain the risk level based on current conditions
5. **Treatment Recommendations**: Provide 3-5 practical treatment and management steps. IMPORTANT: Use the treatment options provided above if available, and expand on them with specific, actionable advice. If no treatments are provided, give general best-practice management recommendations.
6. **Prevention**: Suggest preventive measures
7. **When to Consult Expert**: If confidence is below 70%, recommend consulting a local expert

Format your response in clean markdown with clear sections. Be practical and farmer-friendly.
"""
    return base


def call_groq_chat(prompt: str) -> str:
    """Call Groq API for LLM responses."""
    if Groq is None:
        raise RuntimeError("groq package is not installed. Install it with: pip install groq")
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set. Set it as an environment variable.")
    
    client = Groq(api_key=api_key)
    
    response = client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[
            {"role": "system", "content": "You are an expert agronomist and plant pathologist specializing in wheat diseases. Provide practical, actionable advice for farmers."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.4,
        max_tokens=1500,
    )
    return response.choices[0].message.content  # type: ignore[index]

def call_openai_chat(prompt: str) -> str:
    """Call OpenAI ChatCompletion API if available, otherwise raise RuntimeError."""
    if openai is None:
        raise RuntimeError("openai package is not installed. Install it or use the template fallback.")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set. Set it or use the template fallback.")
    openai.api_key = api_key

    # Using Chat Completions API (gpt-4o-mini or similar)
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert agronomist and plant pathologist."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.4,
    )
    return resp.choices[0].message["content"]  # type: ignore[index]


def template_fallback(structured_result: Dict[str, Any]) -> str:
    """Simple string-based explanation if no LLM is available."""
    facts = structured_result.get("facts", {})
    disease_name = structured_result.get("disease_label") or facts.get("disease_name", "Unknown disease")
    pathogen = facts.get("pathogen", "Unknown pathogen")
    treatments = facts.get("treatments", [])
    conditions = facts.get("conditions", [])
    plant_parts = facts.get("plant_parts", [])
    hosts = facts.get("hosts", [])
    risk_level = structured_result.get("risk_level", "Unknown")
    clip_conf = structured_result.get("clip_confidence", 0.0)
    is_low_conf = structured_result.get("is_low_confidence", False)

    parts = []
    parts.append(
        f"Based on your input, the system thinks your wheat most likely has **{disease_name}** "
        f"(model confidence: {clip_conf:.2f})."
    )

    if pathogen:
        parts.append(f"This disease is caused by **{pathogen}**.")

    if plant_parts:
        parts_str = ", ".join(plant_parts)
        parts.append(f"This disease typically affects **{parts_str}**.")

    if hosts:
        hosts_str = ", ".join(hosts)
        parts.append(f"Affected hosts include: **{hosts_str}**.")

    if conditions:
        cond_str = ", ".join(conditions)
        parts.append(
            f"It tends to develop under conditions such as **{cond_str}**. "
            f"The current **risk level is {risk_level}**."
        )

    if treatments:
        tr_str = "; ".join(treatments)
        parts.append(
            f"Recommended management includes: **{tr_str}**. Follow local guidelines and product labels carefully."
        )

    return "\n\n".join(parts)


def generate_explanation(structured_result: Dict[str, Any]) -> str:
    """High-level wrapper: try Groq LLM first, then OpenAI, then template."""
    prompt = build_prompt(structured_result)
    
    # Try Groq first (preferred for treatments)
    try:
        return call_groq_chat(prompt)
    except Exception as e:
        # Try OpenAI as fallback
        try:
            return call_openai_chat(prompt)
        except Exception:
            # Final fallback to template
            return template_fallback(structured_result)
