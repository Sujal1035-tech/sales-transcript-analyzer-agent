import json
import time

import pandas as pd

from src.analyzer import analyze_transcript
from src.logger import setup_logger
from src.preprocessor import preprocess

logger = setup_logger("processor")

# All 6 output columns
OUTPUT_COLUMNS = [
    "summary",
    "key_takeaways",
    "intent",
    "customer_objection",
    "agent_resolution",
    "call_rating",
]


def _is_already_analyzed(row: pd.Series) -> bool:
    """
    Return True if this row already has a valid summary (not blank, not an error).
    Used to skip rows in resume mode.
    """
    summary = str(row.get("summary", "")).strip()
    # str(NaN) == "nan" which is truthy — treat it as empty
    if summary.lower() == "nan":
        return False
    return bool(summary) and not summary.upper().startswith("ERROR")


def _init_output_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add all output columns if they don't exist yet, with correct dtypes."""
    for col in OUTPUT_COLUMNS:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].astype("object")
    return df


def process_csv(input_file: str) -> None:
    """
    Process a CSV file of call transcripts and populate 6 analysis columns.

    Args:
        input_file: Path to the CSV file (modified in-place)

    The CSV must have a `segments` column containing a JSON array of utterances.
    Each utterance: {"speaker": "...", "start": 0.0, "stop": 1.0, "transcription": "..."}
    """
    logger.info(f"{'='*60}")
    logger.info(f"Starting processing: {input_file}")

    # --- Detect file format (magic bytes) and Read ---
    # Files named .csv but saved as .xlsx (Excel) are common from Windows exports
    try:
        with open(input_file, "rb") as f:
            magic = f.read(4)
        is_xlsx = magic[:2] == b'PK'  # ZIP/XLSX magic header

        if is_xlsx:
            logger.warning("File has XLSX magic bytes despite .csv extension — reading as Excel")
            df = pd.read_excel(input_file)
        else:
            try:
                df = pd.read_csv(input_file, encoding="utf-8-sig")
            except UnicodeDecodeError:
                logger.warning("UTF-8 read failed — retrying with latin-1")
                try:
                    df = pd.read_csv(input_file, encoding="latin-1")
                except Exception:
                    logger.warning("C parser failed — retrying with Python engine")
                    df = pd.read_csv(input_file, encoding="latin-1", engine="python")
    except FileNotFoundError:
        logger.error(f"File not found: {input_file}")
        raise
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        raise

    total_rows = len(df)
    logger.info(f"Loaded {total_rows} rows from CSV")

    # --- Initialize output columns ---
    df = _init_output_columns(df)

    # --- Enforce column order: original cols → analysis cols ---
    original_cols = [c for c in df.columns if c not in OUTPUT_COLUMNS]
    analysis_cols = [
        "summary",
        "key_takeaways",
        "intent",
        "customer_objection",
        "agent_resolution",
        "call_rating",
    ]
    df = df[original_cols + analysis_cols]

    # --- Count rows to process ---
    to_process = [i for i, row in df.iterrows() if not _is_already_analyzed(row)]
    already_done = total_rows - len(to_process)
    if already_done > 0:
        logger.info(f"Resume mode: {already_done} rows already analyzed — skipping them")
    logger.info(f"Rows to analyze: {len(to_process)}")

    # --- Process each row ---
    processed = 0
    failed = 0

    for position, index in enumerate(to_process, start=1):
        logger.info(f"[{position}/{len(to_process)}] Analyzing row {index + 1}/{total_rows}...")

        # Rate-limit sleep (skip before the very first request)
        if position > 1:
            from src.config import BASE_RATE_LIMIT_SLEEP
            logger.debug(f"Waiting {BASE_RATE_LIMIT_SLEEP}s (rate limit buffer)...")
            time.sleep(BASE_RATE_LIMIT_SLEEP)

        try:
            # --- Parse raw segments JSON ---
            raw_segments = df.at[index, "segments"]
            segments = json.loads(raw_segments)

            # --- Preprocess: clean and structure dialogue ---
            dialogue = preprocess(segments)
            if not dialogue.strip():
                raise ValueError("Preprocessor returned empty dialogue — transcript may be all noise")

            logger.debug(f"Preprocessed dialogue ({len(dialogue)} chars, {dialogue.count(chr(10))+1} turns)")

            # --- Analyze with Gemini ---
            insights = analyze_transcript(dialogue)

            # --- Check for analysis failure ---
            if "error" in insights:
                error_msg = f"[{insights['error']}] {insights.get('last_error', 'unknown')}"
                logger.warning(f"Row {index + 1} — Analysis failed: {error_msg}")
                failed += 1
            else:
                # Write all 6 columns
                df.at[index, "summary"] = insights["summary"]
                df.at[index, "key_takeaways"] = " | ".join(insights["key_takeaways"])
                df.at[index, "intent"] = insights["intent"]
                df.at[index, "customer_objection"] = insights["customer_objection"]
                df.at[index, "agent_resolution"] = insights["agent_resolution"]
                df.at[index, "call_rating"] = insights["call_rating"]

                logger.info(
                    f"Row {index + 1} ✓ | intent={insights['intent']} | "
                    f"rating={insights['call_rating']} | "
                    f"objection='{insights['customer_objection']}'"
                )
                processed += 1

        except json.JSONDecodeError as e:
            logger.error(f"Row {index + 1} — Bad segments JSON: {e}")
            failed += 1

        except Exception as e:
            logger.error(f"Row {index + 1} — Unexpected error: {e}")
            failed += 1

        finally:
            # Save after EVERY row to prevent data loss on crash
            df.to_csv(input_file, index=False, encoding="utf-8-sig")
            logger.debug(f"Row {index + 1} saved to disk")

    # --- Final summary ---
    logger.info(f"{'='*60}")
    logger.info(f"complete: {processed} succeeded, {failed} failed, {already_done} skipped")

    intent_dist = df["intent"].value_counts().to_dict()
    logger.info(f"Intent distribution: {intent_dist}")

    if failed > 0:
        logger.warning(f"Total failed rows: {failed}")

    logger.info(f"Output saved to: {input_file}")
