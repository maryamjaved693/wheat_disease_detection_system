# Treatment Update Commands

## Update RDF with Treatments from CSV

To add treatments from the CSV file to the RDF knowledge base, run:

```bash
python update_rdf_with_treatments.py
```

## What it does:

1. Reads the `app/data/csv_with_disease_specific_treatments.csv` file
2. Extracts treatment data from the `treatments` column
3. Adds treatments to the RDF file (`app/rdf/cimmyt_wheat_diseases.ttl`)
4. Links treatments to their respective diseases using `wheat:hasTreatment` property

## Adding More Treatments

1. Edit `app/data/csv_with_disease_specific_treatments.csv`
2. Add treatments to the `treatments` column (separate multiple treatments with semicolons `;`)
3. Run the update script again:
   ```bash
   python update_rdf_with_treatments.py
   ```

## Example CSV Format

```csv
disease_name,treatments
Leaf Rust (Brown Rust),"Use resistant cultivars; Apply fungicides; Practice crop rotation"
```

## Verification

After running the script, you can verify treatments were added by checking:
- The RDF file: `app/rdf/cimmyt_wheat_diseases.ttl`
- The treatments will be linked to diseases via `wheat:hasTreatment` property

