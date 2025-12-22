
# Intelligent Wheat Disease Diagnosis (CLIP + RDF/SPARQL + LLM)

This is a **minimal reference implementation** of your project:

> *Intelligent Wheat Disease Diagnosis using CLIP, RDF Reasoning, and LLM-based Explanation*

It demonstrates:
- Image-based disease identification with **CLIP**
- A small **RDF knowledge graph** + **SPARQL reasoning**
- Optional **LLM explanation layer**
- A simple **Streamlit web UI**

---

## 1️⃣ Requirements

- Python 3.9+ recommended
- Internet connection (for downloading CLIP weights the first time)
- (Optional) OpenAI API key for the LLM explanation

Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate      # On Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 2️⃣ Running the Demo App

From the project root:

```bash
streamlit run app/main.py
```

Then open the local URL that Streamlit prints (usually http://localhost:8501).

---

## 3️⃣ Using the App

You can:

- Upload a wheat leaf **image**
- Optionally type a **text description of symptoms**
- Click **Run Diagnosis**

The pipeline:

1. `clip_model.py`  
   - Uses CLIP to classify the image into one of a few **demo diseases**:
     - Leaf Rust
     - Stem Rust
     - Yellow Rust
     - Powdery Mildew
     - Healthy

2. `rdf_knowledge.py` + `reasoner.py`  
   - RDF knowledge base with disease info (symptoms, pathogen, treatments, conditions)
   - SPARQL queries retrieve all facts for the predicted disease
   - Simple reasoning rule for **risk level** based on humidity

3. `nlp_symptom_extractor.py`  
   - Very small keyword-based symptom extractor (for demo purposes)
   - In a real system you can replace it with a proper NLP model

4. `llm_interface.py`  
   - If environment variable `OPENAI_API_KEY` is set, uses OpenAI Chat Completions
   - Otherwise falls back to a **template-based explanation** (no external API needed)

---

## 4️⃣ Environment Variables (optional)

For LLM explanations via OpenAI:

```bash
export OPENAI_API_KEY="sk-..."      # Linux / macOS
set OPENAI_API_KEY=sk-...           # Windows CMD
$env:OPENAI_API_KEY="sk-..."        # PowerShell
```

---

## 5️⃣ Extending the Project

Things you can extend / improve:

- Replace the tiny RDF demo with a full conversion of the **CIMMYT Wheat Diseases and Pests Guide**
- Improve symptom extraction with a real NLP model (spaCy, transformers, etc.)
- Add more diseases, symptoms, and rules
- Store provenance + confidences from CLIP/NLP in RDF
- Add user authentication, logging, or database storage

---

## 6️⃣ Project Structure

```text
wheat_diagnosis_hybrid/
├── app/
│   ├── main.py                  # Streamlit UI + pipeline orchestration
│   ├── clip_model.py            # CLIP wrapper for image-based classification
│   ├── rdf_knowledge.py         # RDF graph creation, loading, and SPARQL helpers
│   ├── reasoner.py              # Reasoning utilities + example rules
│   ├── nlp_symptom_extractor.py # Simple heuristic symptom extraction
│   ├── llm_interface.py         # LLM wrapper (OpenAI + fallback)
│   ├── config.py                # Configuration (diseases, labels, paths)
│   └── rdf/
│       └── wheat_diseases.ttl   # Tiny example RDF ontology for a few diseases
├── requirements.txt
└── README.md
```

This is a **starting point** implementation you can run, study, and extend into your full thesis / project.
