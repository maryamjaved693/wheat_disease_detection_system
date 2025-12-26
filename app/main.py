
import io
from typing import Optional

import streamlit as st
from PIL import Image

from clip_model import WheatDiseaseCLIP
from rdf_knowledge import WheatKnowledgeBase
from reasoner import WheatReasoner
from nlp_symptom_extractor import extract_symptoms
from llm_interface import generate_explanation


@st.cache_resource
def load_clip_model():
    return WheatDiseaseCLIP()


@st.cache_resource
def load_kb_and_reasoner(cache_version: int = 2):
    """Load knowledge base and reasoner. Cache version forces reload when changed."""
    kb = WheatKnowledgeBase()
    reasoner = WheatReasoner(kb)
    return kb, reasoner


def run_pipeline(
    image: Optional[Image.Image],
    symptom_text: str,
):
    kb, reasoner = load_kb_and_reasoner()
    clip_model = load_clip_model()

    clip_label = "Healthy"
    clip_conf = 0.0
    all_scores = []
    is_wheat = True
    wheat_confidence = 0.0

    if image is not None:
        # First, check if the image is wheat-related
        is_wheat, wheat_confidence = clip_model.is_wheat_image(image)
        
        if not is_wheat:
            # Return early with error flag if not wheat
            return {
                "error": "not_wheat",
                "wheat_confidence": wheat_confidence,
                "message": "The uploaded image does not appear to be wheat-related. Please upload an image of wheat leaves or plants."
            }
        
        # Only proceed with disease prediction if image is wheat-related
        clip_label, clip_conf, all_scores = clip_model.predict(image)

    text_symptoms = extract_symptoms(symptom_text)

    reasoning_result = reasoner.reason(
        disease_label=clip_label,
        clip_confidence=clip_conf,
        text_symptoms=text_symptoms,
    )

    reasoning_dict = reasoner.to_dict(reasoning_result)
    explanation = generate_explanation(reasoning_dict)

    return {
        "clip_label": clip_label,
        "clip_confidence": clip_conf,
        "clip_scores": all_scores,
        "text_symptoms": text_symptoms,
        "reasoning": reasoning_dict,
        "llm_explanation": explanation,
        "is_wheat": is_wheat,
        "wheat_confidence": wheat_confidence,
    }


def main():
    st.set_page_config(
        page_title="Wheat Disease Diagnosis",
        page_icon="🌾",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        color: #2E7D32;
        padding: 1rem 0;
    }
    .diagnosis-box {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<h1 class="main-header">🌾 Wheat Disease Diagnosis System</h1>', unsafe_allow_html=True)
    st.markdown("---")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### 📤 Upload Image")
        uploaded = st.file_uploader(
            "Choose a wheat leaf image",
            type=["jpg", "jpeg", "png"],
            help="Upload a clear image of the wheat leaf showing disease symptoms"
        )
        
        st.markdown("### 📝 Additional Information")
        symptom_text = st.text_area(
            "Describe symptoms (optional)",
            placeholder="e.g., orange spots on upper leaves, weather conditions",
            height=100,
        )
        
        run_button = st.button("🔍 Diagnose Disease", type="primary", use_container_width=True)

    with col2:
        st.markdown("### 📷 Image Preview")
        pil_image = None
        if uploaded is not None:
            pil_image = Image.open(uploaded).convert("RGB")
            st.image(pil_image, use_container_width=True, caption="Uploaded image")
        else:
            st.info("👆 Please upload a wheat leaf image to begin diagnosis")

    if run_button:
        if pil_image is None:
            st.warning("⚠️ Please upload an image first")
        else:
            with st.spinner("🔄 Analyzing image and retrieving disease information..."):
                result = run_pipeline(pil_image, symptom_text)

            # Check if there's an error (non-wheat image)
            if result.get("error") == "not_wheat":
                st.markdown("---")
                st.markdown('<div class="diagnosis-box">', unsafe_allow_html=True)
                st.markdown("### 📋 Diagnosis Result")
                st.markdown("**I can only answer queries about wheat images. Please upload an image of wheat leaves or plants for disease diagnosis.**")
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.markdown("---")
                st.markdown('<div class="diagnosis-box">', unsafe_allow_html=True)
                
                # Disease prediction
                clip_label = result['clip_label']
                clip_conf = result['clip_confidence']
                
                st.markdown(f"### 🔬 Predicted Disease: **{clip_label}**")
                
                # Get facts
                reasoning = result["reasoning"]
                facts = reasoning.get("facts", {})
                disease_name = facts.get("disease_name", clip_label)
                pathogen = facts.get("pathogen", "Unknown")
                risk_level = reasoning.get("risk_level", "Unknown")
                
                # Key information in columns
                col_info1, col_info2 = st.columns(2)
                with col_info1:
                    st.markdown(f"**Pathogen:** {pathogen}")
                    st.markdown(f"**Risk Level:** {risk_level}")
                with col_info2:
                    if facts.get("plant_parts"):
                        st.markdown(f"**Affected Parts:** {', '.join(facts['plant_parts'][:2])}")
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                # LLM Explanation in markdown
                st.markdown("---")
                st.markdown("### 📋 Diagnosis Report")
                st.markdown(result["llm_explanation"])
                
                # Additional details in expander
                with st.expander("🔍 View Technical Details"):
                    if result["clip_scores"]:
                        st.markdown("**Top Predictions:**")
                        top_scores = result["clip_scores"][:5]
                        for disease, score in top_scores:
                            st.progress(float(score), text=f"{disease}: {score:.1%}")
                    
                    if facts.get("symptoms"):
                        st.markdown("**Symptoms from Knowledge Base:**")
                        for symptom in facts.get("symptoms", [])[:3]:
                            st.markdown(f"- {symptom[:200]}...")
                    
                    if reasoning.get("explanation_trace"):
                        st.markdown("**Reasoning Steps:**")
                        for line in reasoning.get("explanation_trace", []):
                            st.markdown(f"- {line}")


if __name__ == "__main__":
    main()
