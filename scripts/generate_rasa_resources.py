import yaml
import os
import shutil
from collections import defaultdict

GENERATED_DIR = "src/data/nlu/.generated"

SSOT_FILES = [
    {
        "ssot_path": "src/shared/SSOT/kpi.yml",
        "root_key": "kpi",
        "entity": "kpi",
        "output_base": "kpi",
    },
    {
        "ssot_path": "src/shared/SSOT/comparisonTypes.yml",
        "root_key": "comparisonTypes",
        "entity": "comparison_type",
        "output_base": "comparison",
    },
    {
        "ssot_path": "src/shared/SSOT/booleanTypes.yml",
        "root_key": "booleanTypes",
        "entity": "boolean_type",
        "output_base": "boolean",
    },
    {
        "ssot_path": "src/shared/SSOT/sexTypes.yml",
        "root_key": "sexTypes",
        "entity": "sex",
        "output_base": "sex",
    },
    {
        "ssot_path": "src/shared/SSOT/strokeTypes.yml",
        "root_key": "strokeTypes",
        "entity": "stroke_type",
        "output_base": "stroke",
    },
    {
        "ssot_path": "src/shared/SSOT/groupBy.yml",
        "root_key": "groupBy",
        "entity": "group_by",
        "output_base": "groupby",
    },
    {
        "ssot_path": "src/shared/SSOT/chartTypes.yml",
        "root_key": "chartTypes",
        "entity": "chart_types",
        "output_base": "chart",
    },
]

# Clean up old generated folder
if os.path.exists(GENERATED_DIR):
    shutil.rmtree(GENERATED_DIR)
os.makedirs(GENERATED_DIR, exist_ok=True)

def generate_rasa_files(ssot_path, root_key, entity, output_base):
    with open(ssot_path, "r") as f:
        items = yaml.safe_load(f)[root_key]

    grouped_synonyms = defaultdict(list)
    lookup_entries = []

    for item in items:
        canonical = item["canonical"]
        grouped_synonyms[canonical].extend(item["synonyms"])
        lookup_entries.append(canonical)  # Only add canonical names to lookup

    # Create grouped synonym entries
    synonym_entries = []
    for canonical, synonyms in grouped_synonyms.items():
        lines = "\n    - ".join(synonyms)
        synonym_entries.append(f"- synonym: {canonical}\n  examples: |\n    - {lines}")

    # Write synonyms
    synonyms_out = os.path.join(GENERATED_DIR, f"{output_base}_synonyms.yml")
    with open(synonyms_out, "w") as f:
        f.write("version: \"3.1\"\n\nnlu:\n")
        f.write("\n".join(synonym_entries))

    # Write lookup table
    lookup_out = os.path.join(GENERATED_DIR, f"{output_base}_lookup.yml")
    with open(lookup_out, "w") as f:
        f.write("version: \"3.1\"\n\nnlu:\n")
        f.write(f"- lookup: {entity}\n  examples: |\n")
        for entry in lookup_entries:
            f.write(f"    - {entry}\n")

# Write all to Rasa files
for ssot in SSOT_FILES:
    print(f"Generating for {ssot['ssot_path']} → {ssot['output_base']}")
    generate_rasa_files(**ssot)
