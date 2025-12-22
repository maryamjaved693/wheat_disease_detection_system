"""
Script to update RDF knowledge base with treatments from CSV file.
Reads treatments from csv_with_disease_specific_treatments.csv and adds them to cimmyt_wheat_diseases.ttl
"""

import csv
from pathlib import Path
from rdflib import Graph, Namespace, RDF, RDFS, Literal, URIRef

# Namespace
WHEAT = Namespace("http://example.org/wheat#")

# File paths
CSV_FILE = Path("app/data/csv_with_disease_specific_treatments.csv")
RDF_FILE = Path("app/rdf/cimmyt_wheat_diseases.ttl")

def normalize_disease_name(name: str) -> str:
    """Normalize disease name to match RDF naming convention."""
    # Remove special characters and replace spaces with underscores
    name = name.replace(" ", "_").replace("(", "").replace(")", "").replace(".", "").replace(",", "")
    name = name.replace("-", "_").replace("/", "_").replace("'", "").replace('"', '')
    # Remove multiple underscores
    while "__" in name:
        name = name.replace("__", "_")
    # Remove leading/trailing underscores
    name = name.strip("_")
    return name

def get_disease_uri_from_label(graph: Graph, disease_label: str) -> URIRef | None:
    """Find disease URI by label."""
    disease_label_lower = disease_label.lower().strip()
    
    # Try exact match first
    for s, p, o in graph.triples((None, RDFS.label, None)):
        if str(o).lower().strip() == disease_label_lower:
            if (s, RDF.type, WHEAT.Disease) in graph:
                return s
    
    # Try matching without parentheses
    label_base = disease_label_lower.split("(")[0].strip()
    if label_base and label_base != disease_label_lower:
        for s, p, o in graph.triples((None, RDFS.label, None)):
            if (s, RDF.type, WHEAT.Disease) in graph:
                disease_label_str = str(o).lower().strip()
                disease_label_base = disease_label_str.split("(")[0].strip()
                if disease_label_base == label_base:
                    return s
    
    # Try partial matching
    best_match = None
    best_score = 0
    
    for s, p, o in graph.triples((None, RDFS.label, None)):
        if (s, RDF.type, WHEAT.Disease) in graph:
            disease_label_str = str(o).lower().strip()
            if disease_label_lower in disease_label_str or disease_label_str in disease_label_lower:
                if disease_label_str == disease_label_lower:
                    return s
                score = len(disease_label_lower) if disease_label_lower in disease_label_str else len(disease_label_str)
                if score > best_score:
                    best_score = score
                    best_match = s
    
    return best_match

def add_treatments_to_rdf():
    """Read treatments from CSV and add them to RDF file."""
    # Load RDF graph
    graph = Graph()
    if not RDF_FILE.exists():
        print(f"Error: RDF file not found at {RDF_FILE}")
        return
    
    graph.parse(RDF_FILE, format="turtle")
    print(f"Loaded RDF graph with {len(graph)} triples")
    
    # Read CSV
    if not CSV_FILE.exists():
        print(f"Error: CSV file not found at {CSV_FILE}")
        return
    
    treatments_added = 0
    diseases_with_treatments = 0
    diseases_not_found = []
    
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            disease_name = row.get('disease_name', '').strip()
            treatments_str = row.get('treatments', '').strip()
            
            if not disease_name:
                continue
            
            if not treatments_str:
                continue  # Skip if no treatments
            
            diseases_with_treatments += 1
            
            # Find disease URI in RDF
            disease_uri = get_disease_uri_from_label(graph, disease_name)
            
            if disease_uri is None:
                diseases_not_found.append(disease_name)
                print(f"Warning: Disease not found in RDF: {disease_name}")
                continue
            
            # Parse treatments (assuming they might be separated by semicolons or newlines)
            # Split by common delimiters
            treatment_list = []
            for delimiter in [';', '\n', '|', '•']:
                if delimiter in treatments_str:
                    treatment_list = [t.strip() for t in treatments_str.split(delimiter) if t.strip()]
                    break
            
            if not treatment_list:
                # If no delimiter found, treat entire string as one treatment
                treatment_list = [treatments_str]
            
            # Add each treatment to RDF
            for treatment_text in treatment_list:
                if not treatment_text:
                    continue
                
                # Create treatment URI
                treatment_id = normalize_disease_name(disease_name) + "_Treatment_" + str(treatments_added + 1)
                treatment_uri = WHEAT[treatment_id]
                
                # Check if treatment already exists (avoid duplicates)
                existing = False
                for _, _, tr_uri in graph.triples((disease_uri, WHEAT.hasTreatment, None)):
                    existing_label = graph.value(tr_uri, RDFS.label)
                    if existing_label and str(existing_label).strip() == treatment_text.strip():
                        existing = True
                        break
                
                if not existing:
                    # Add treatment as a Treatment instance
                    graph.add((treatment_uri, RDF.type, WHEAT.Treatment))
                    graph.add((treatment_uri, RDFS.label, Literal(treatment_text)))
                    
                    # Link treatment to disease
                    graph.add((disease_uri, WHEAT.hasTreatment, treatment_uri))
                    
                    treatments_added += 1
                    print(f"Added treatment for {disease_name}: {treatment_text[:80]}")
    
    # Save updated RDF
    if treatments_added > 0:
        graph.serialize(destination=RDF_FILE, format="turtle")
        print(f"\nSuccessfully added {treatments_added} treatments to RDF file")
        print(f"Updated {diseases_with_treatments} diseases with treatments")
    else:
        print(f"\nWarning: No treatments found in CSV file to add")
        print(f"  (Found {diseases_with_treatments} diseases with treatment column, but all were empty)")
    
    if diseases_not_found:
        print(f"\nWarning: Could not find {len(diseases_not_found)} diseases in RDF:")
        for disease in diseases_not_found:
            print(f"  - {disease}")

if __name__ == "__main__":
    add_treatments_to_rdf()

