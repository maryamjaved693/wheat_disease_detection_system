
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List

from rdflib import Graph, Namespace, RDF, RDFS, Literal, URIRef

from config import RDF_FILE

WHEAT = Namespace("http://example.org/wheat#")


@dataclass
class DiseaseFacts:
    uri: URIRef
    label: str
    pathogen: str | None
    symptoms: List[str]
    treatments: List[str]
    conditions: List[str]
    plant_parts: List[str]
    hosts: List[str]
    notes: List[str]


class WheatKnowledgeBase:
    def __init__(self, ttl_path: Path | None = None):
        self.ttl_path = ttl_path or RDF_FILE
        self.graph = Graph()
        self._load()

    def _load(self):
        if not self.ttl_path.exists():
            raise FileNotFoundError(f"RDF file not found at {self.ttl_path}")
        self.graph.parse(self.ttl_path, format="turtle")

    def get_all_disease_labels(self) -> List[str]:
        """Get all disease labels from the RDF graph, preferring shorter names."""
        labels = []
        seen_uris = set()
        
        for s, p, o in self.graph.triples((None, RDF.type, WHEAT.Disease)):
            if s in seen_uris:
                continue
            seen_uris.add(s)
            
            # Get all labels for this disease
            disease_labels = [str(o) for _, _, o in self.graph.triples((s, RDFS.label, None))]
            if disease_labels:
                # Prefer labels without parentheses (shorter, more common names)
                labels_without_parens = [lbl for lbl in disease_labels if "(" not in lbl]
                if labels_without_parens:
                    labels.append(labels_without_parens[0])
                else:
                    labels.append(disease_labels[0])
        
        return sorted(set(labels))  # Remove duplicates and sort

    def get_disease_uri_by_label(self, label: str) -> URIRef | None:
        """Find disease URI by label with flexible matching."""
        label_lower = label.lower().strip()
        
        def is_disease(uri: URIRef) -> bool:
            """Check if URI is a Disease type."""
            return (uri, RDF.type, WHEAT.Disease) in self.graph
        
        # First, try exact match with type verification
        for s, p, o in self.graph.triples((None, RDFS.label, None)):
            if str(o).lower().strip() == label_lower:
                if is_disease(s):
                    return s
        
        # Also try matching without parentheses content
        # e.g., "Stripe Rust (Yellow Rust)" should match "Stripe Rust"
        label_base = label_lower.split("(")[0].strip()
        if label_base and label_base != label_lower:
            for s, p, o in self.graph.triples((None, RDFS.label, None)):
                if not is_disease(s):
                    continue
                disease_label = str(o).lower().strip()
                disease_label_base = disease_label.split("(")[0].strip()
                if disease_label_base == label_base:
                    return s
        
        # If no exact match, try partial matching
        # Check if label contains or is contained in any disease label
        best_match = None
        best_score = 0
        
        for s, p, o in self.graph.triples((None, RDFS.label, None)):
            if not is_disease(s):
                continue
                
            disease_label = str(o).lower().strip()
            
            # Check if one contains the other (for cases like "Leaf Rust" matching "Leaf Rust (Brown Rust)")
            if label_lower in disease_label or disease_label in label_lower:
                # Prefer exact matches or shorter labels
                if disease_label == label_lower:
                    return s
                # Prefer when the search label is contained in disease label (more specific match)
                if label_lower in disease_label:
                    score = len(label_lower)
                else:
                    score = len(disease_label)
                if score > best_score:
                    best_score = score
                    best_match = s
        
        # Fallback: if no type-checked match, try without type check (for robustness)
        if best_match is None:
            for s, p, o in self.graph.triples((None, RDFS.label, None)):
                if str(o).lower().strip() == label_lower:
                    return s
        
        return best_match

    def get_disease_facts(self, disease_label: str) -> DiseaseFacts | None:
        uri = self.get_disease_uri_by_label(disease_label)
        if uri is None:
            return None

        g = self.graph
        pathogen = None
        symptoms: List[str] = []
        treatments: List[str] = []
        conditions: List[str] = []
        plant_parts: List[str] = []
        hosts: List[str] = []
        notes: List[str] = []

        # Pathogen
        for _, _, pathogen_uri in g.triples((uri, WHEAT.causedBy, None)):
            lab = g.value(pathogen_uri, RDFS.label)
            if lab:
                pathogen = str(lab)

        # Symptoms
        for _, _, sym_uri in g.triples((uri, WHEAT.hasSymptom, None)):
            lab = g.value(sym_uri, RDFS.label)
            if lab:
                symptoms.append(str(lab))

        # Treatments
        for _, _, tr_uri in g.triples((uri, WHEAT.hasTreatment, None)):
            lab = g.value(tr_uri, RDFS.label)
            if lab:
                treatments.append(str(lab))

        # Conditions
        for _, _, cond_uri in g.triples((uri, WHEAT.developsUnder, None)):
            lab = g.value(cond_uri, RDFS.label)
            if lab:
                conditions.append(str(lab))

        # Plant parts
        for _, _, part_uri in g.triples((uri, WHEAT.affectsPlantPart, None)):
            lab = g.value(part_uri, RDFS.label)
            if lab:
                plant_parts.append(str(lab))

        # Hosts
        for _, _, host_uri in g.triples((uri, WHEAT.affectsHost, None)):
            lab = g.value(host_uri, RDFS.label)
            if lab:
                hosts.append(str(lab))

        # Notes (optional)
        for _, _, note_lit in g.triples((uri, WHEAT.hasNote, None)):
            notes.append(str(note_lit))

        # Get the most appropriate label
        all_labels = [str(o) for _, _, o in g.triples((uri, RDFS.label, None))]
        if all_labels:
            # Prefer the label that matches the input disease_label (if provided)
            if disease_label:
                disease_label_lower = disease_label.lower().strip()
                for lbl in all_labels:
                    if lbl.lower().strip() == disease_label_lower:
                        label = lbl
                        break
                else:
                    # If no exact match, prefer labels without parentheses (shorter, more common names)
                    labels_without_parens = [lbl for lbl in all_labels if "(" not in lbl]
                    if labels_without_parens:
                        label = labels_without_parens[0]
                    else:
                        label = all_labels[0]
            else:
                # Prefer labels without parentheses (shorter, more common names)
                labels_without_parens = [lbl for lbl in all_labels if "(" not in lbl]
                if labels_without_parens:
                    label = labels_without_parens[0]
                else:
                    label = all_labels[0]
        else:
            # Fallback to URI name
            label = uri.split("#")[-1].replace("_", " ")

        return DiseaseFacts(
            uri=uri,
            label=label,
            pathogen=pathogen,
            symptoms=symptoms,
            treatments=treatments,
            conditions=conditions,
            plant_parts=plant_parts,
            hosts=hosts,
            notes=notes,
        )

    def to_dict(self, facts: DiseaseFacts | None) -> Dict[str, Any]:
        if facts is None:
            return {}
        return {
            "disease_uri": str(facts.uri),
            "disease_name": facts.label,
            "pathogen": facts.pathogen,
            "symptoms": facts.symptoms,
            "treatments": facts.treatments,
            "conditions": facts.conditions,
            "plant_parts": facts.plant_parts,
            "hosts": facts.hosts,
            "notes": facts.notes,
        }
