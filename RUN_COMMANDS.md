# Commands to Update RDF with Treatments

## Main Command

To update the RDF knowledge base with treatments from the CSV file:

```bash
python update_rdf_with_treatments.py
```

## What This Does

- Reads treatments from `app/data/csv_with_disease_specific_treatments.csv`
- Adds them to `app/rdf/cimmyt_wheat_diseases.ttl`
- Links treatments to diseases using `wheat:hasTreatment` property
- Skips diseases that already have the same treatments (avoids duplicates)

## Expected Output

When treatments are found and added, you'll see:
```
Loaded RDF graph with XXX triples
Added treatment for [Disease Name]: [Treatment text]
...
Successfully added X treatments to RDF file
Updated X diseases with treatments
```

## Adding New Treatments

1. Edit `app/data/csv_with_disease_specific_treatments.csv`
2. Add treatments to the `treatments` column
   - Separate multiple treatments with semicolons (`;`)
   - Example: `"Treatment 1; Treatment 2; Treatment 3"`
3. Run the update script:
   ```bash
   python update_rdf_with_treatments.py
   ```

## Quick Check

To verify treatments are in the CSV:
```bash
python -c "import csv; rows = list(csv.DictReader(open('app/data/csv_with_disease_specific_treatments.csv', 'r', encoding='utf-8'))); print('Diseases with treatments:', sum(1 for r in rows if r.get('treatments', '').strip()))"
```

