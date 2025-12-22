
from pathlib import Path

# Base paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RDF_DIR = PROJECT_ROOT / "app" / "rdf"
# Use the CIMMYT-derived RDF graph
RDF_FILE = RDF_DIR / "cimmyt_wheat_diseases.ttl"

# Disease labels will be loaded dynamically from RDF
# This list is a fallback if RDF loading fails
DISEASE_LABELS_FALLBACK = [
    "Healthy",
    "Leaf Rust",
    "Stem Rust",
    "Stripe Rust (Yellow Rust)",
    "Powdery Mildew",
]

# Disease labels will be loaded lazily to avoid circular imports
DISEASE_LABELS = None

def get_disease_labels():
    """Dynamically load all disease labels from RDF."""
    global DISEASE_LABELS
    if DISEASE_LABELS is not None:
        return DISEASE_LABELS
    
    try:
        from rdf_knowledge import WheatKnowledgeBase
        kb = WheatKnowledgeBase()
        labels = kb.get_all_disease_labels()
        # Add "Healthy" as the first option
        if "Healthy" not in labels:
            DISEASE_LABELS = ["Healthy"] + labels
        else:
            DISEASE_LABELS = labels
        return DISEASE_LABELS
    except Exception:
        DISEASE_LABELS = DISEASE_LABELS_FALLBACK
        return DISEASE_LABELS

# Default humidity value if user doesn't specify (used in reasoning demo)
DEFAULT_HUMIDITY = 60  # percent

# Thresholds
LOW_CONFIDENCE_THRESHOLD = 0.7
HIGH_HUMIDITY_THRESHOLD = 70
