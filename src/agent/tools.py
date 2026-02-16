import contextlib
import io

import pandas as pd
from google.genai import types

from src.analysis.feature_engineering import extract_features
from src.observability import get_tracer
from src.rag.search import create_text_report, retrieve_context

# --- Tool implementations ---


def search_dan_incidents(query: str) -> str:
    """Search the DAN database for diving incident reports matching the query."""
    tracer = get_tracer()
    with tracer.start_as_current_span(
        "tool.search_dan_incidents",
        attributes={"openinference.span.kind": "TOOL"},
    ):
        prefixed_query = f"diving incident: {query}"
        return retrieve_context(prefixed_query)


def search_dan_guidelines(query: str) -> str:
    """Search the DAN database for diving safety guidelines matching the query."""
    tracer = get_tracer()
    with tracer.start_as_current_span(
        "tool.search_dan_guidelines",
        attributes={"openinference.span.kind": "TOOL"},
    ):
        prefixed_query = f"diving safety guideline: {query}"
        return retrieve_context(prefixed_query)


def _filter_dive(df: pd.DataFrame, dive_number: str) -> pd.DataFrame:
    """Filter a DataFrame to rows matching dive_number, handling type coercion."""
    # dive_number column may be int or str depending on JSON round-trip
    result = df[df["dive_number"] == dive_number]
    if result.empty:
        with contextlib.suppress(ValueError, TypeError):
            result = df[df["dive_number"] == int(dive_number)]
    return result


def analyze_dive_profile(dive_number: str, dive_data_json: str) -> str:
    """Analyze a specific dive's profile and flag safety issues."""
    tracer = get_tracer()
    with tracer.start_as_current_span(
        "tool.analyze_dive_profile",
        attributes={"openinference.span.kind": "TOOL"},
    ):
        df = pd.read_json(io.StringIO(dive_data_json))
        dive_df = _filter_dive(df, dive_number)

        if dive_df.empty:
            return f"No data found for dive number {dive_number}."

        features = extract_features(dive_df)
        if features.empty:
            return f"Could not extract features for dive {dive_number}."

        row = features.iloc[0]
        issues = []

        if row.get("max_ascend_speed", 0) > 10:
            issues.append(
                f"HIGH ASCENT RATE: Max ascent speed was {row['max_ascend_speed']:.1f} m/min "
                f"(recommended: <10 m/min). {int(row.get('high_ascend_speed_count', 0))} "
                f"instances of excessive speed detected."
            )
        if row.get("min_ndl", float("inf")) < 5:
            issues.append(
                f"DANGEROUSLY LOW NDL: Minimum NDL dropped to {row['min_ndl']:.0f} minutes. "
                f"This is cutting it extremely close to mandatory decompression."
            )
        if row.get("sac_rate", 0) > 20:
            issues.append(
                f"HIGH AIR CONSUMPTION: SAC rate of {row['sac_rate']:.1f} l/min is above average. "
                f"Consider working on breathing technique and buoyancy."
            )
        if row.get("max_depth", 0) > 30:
            issues.append(
                f"DEEP DIVE: Maximum depth of {row['max_depth']:.1f}m. "
                f"Ensure you have appropriate training and gas planning for this depth."
            )
        if row.get("adverse_conditions", 0) == 1:
            issues.append(
                "This dive was flagged as having ADVERSE CONDITIONS (rating < 3)."
            )

        summary = create_text_report(row.to_dict())
        if issues:
            return (
                f"Dive {dive_number} Analysis:\n{summary}\n\nIssues Found:\n"
                + "\n".join(f"- {issue}" for issue in issues)
            )
        else:
            return f"Dive {dive_number} Analysis:\n{summary}\n\nNo major safety issues detected. Dive looks clean."


def get_dive_summary(dive_number: str, dive_data_json: str) -> str:
    """Get a summary of a specific dive including location, depth, duration, and rating."""
    tracer = get_tracer()
    with tracer.start_as_current_span(
        "tool.get_dive_summary",
        attributes={"openinference.span.kind": "TOOL"},
    ):
        df = pd.read_json(io.StringIO(dive_data_json))
        dive_df = _filter_dive(df, dive_number)

        if dive_df.empty:
            return f"No data found for dive number {dive_number}."

        first_row = dive_df.iloc[0]
        max_depth = dive_df["depth"].max()
        duration = dive_df["time"].max()
        sac_rate = first_row.get("sac_rate", "N/A")
        rating = first_row.get("rating", "N/A")
        site = first_row.get("dive_site_name", "Unknown")
        trip = first_row.get("trip_name", "Unknown")

        return (
            f"Dive {dive_number}:\n"
            f"  Location: {site} ({trip})\n"
            f"  Max Depth: {max_depth:.1f}m\n"
            f"  Duration: {duration:.0f} seconds\n"
            f"  SAC Rate: {sac_rate}\n"
            f"  Rating: {rating}/5"
        )


# --- Gemini function declarations ---

TOOL_DECLARATIONS = [
    types.FunctionDeclaration(
        name="search_dan_incidents",
        description="Search the DAN (Divers Alert Network) database for diving incident reports. Use this to find real incidents related to the diver's behavior.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "query": types.Schema(
                    type=types.Type.STRING,
                    description="Search query describing the incident type (e.g., 'rapid ascent decompression sickness')",
                ),
            },
            required=["query"],
        ),
    ),
    types.FunctionDeclaration(
        name="search_dan_guidelines",
        description="Search the DAN database for diving safety guidelines and best practices.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "query": types.Schema(
                    type=types.Type.STRING,
                    description="Search query for safety guidelines (e.g., 'ascent rate recommendations')",
                ),
            },
            required=["query"],
        ),
    ),
    types.FunctionDeclaration(
        name="analyze_dive_profile",
        description="Analyze a specific dive's profile data and flag any safety issues like high ascent rate, low NDL, or high air consumption.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "dive_number": types.Schema(
                    type=types.Type.STRING,
                    description="The dive number to analyze",
                ),
                "dive_data_json": types.Schema(
                    type=types.Type.STRING,
                    description="JSON string of the dive data DataFrame",
                ),
            },
            required=["dive_number", "dive_data_json"],
        ),
    ),
    types.FunctionDeclaration(
        name="get_dive_summary",
        description="Get a quick summary of a specific dive including location, max depth, duration, SAC rate, and rating.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "dive_number": types.Schema(
                    type=types.Type.STRING,
                    description="The dive number to summarize",
                ),
                "dive_data_json": types.Schema(
                    type=types.Type.STRING,
                    description="JSON string of the dive data DataFrame",
                ),
            },
            required=["dive_number", "dive_data_json"],
        ),
    ),
]

TOOL_FUNCTIONS = {
    "search_dan_incidents": search_dan_incidents,
    "search_dan_guidelines": search_dan_guidelines,
    "analyze_dive_profile": analyze_dive_profile,
    "get_dive_summary": get_dive_summary,
}
