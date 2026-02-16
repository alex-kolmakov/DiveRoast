"""CLI script to parse dive logs and extract features."""

import sys

from src.analysis.feature_engineering import extract_features
from src.parsers import get_parser

if __name__ == "__main__":
    file_path = sys.argv[1] if len(sys.argv) > 1 else "anonymized_subsurface_export.ssrf"
    parser = get_parser(file_path)
    df = parser.parse(file_path)
    features = extract_features(df)
    print(f"Processed {len(features)} dives from {file_path}")
