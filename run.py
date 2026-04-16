"""
run.py
------
Single CLI entry point for the Sales Transcript Analyzer.

Usage:
    python run.py <path_to_csv>

Example:
    python run.py data/sales.csv
    python run.py "data/Sales testing - Sheet1.csv"

The script will:
    1. Validate configuration (API key check)
    2. Process all unanalyzed rows in the CSV
    3. Write 6 analysis columns back to the same file
    4. Save structured logs to the logs/ directory
"""

import sys

from src.config import validate
from src.logger import setup_logger
from src.processor import process_csv

logger = setup_logger("run")


def main() -> None:
    # --- Startup config validation (fails fast if API key is missing) ---
    try:
        validate()
    except EnvironmentError as e:
        print(str(e))
        sys.exit(1)

    # --- Argument check ---
    if len(sys.argv) < 2:
        print("\nUsage:   python run.py <csv_file>")
        print("Example: python run.py data/sales.csv\n")
        print("Output columns added to the CSV:")
        print("  summary           — Detailed 3-4 sentence call recap")
        print("  key_takeaways     — 2 short bullets, pipe-separated")
        print("  intent            — high / medium / low")
        print("  customer_objection— Primary reason for hesitation")
        print("  agent_resolution  — How agent handled the objection")
        print("  call_rating       — 1 (worst) to 5 (best)")
        print("  processing_error  — Populated only on failure\n")
        sys.exit(0)

    input_file = sys.argv[1]

    logger.info(f"Transcript Analyzer started")
    logger.info(f"Target file: {input_file}")

    try:
        process_csv(input_file)
    except FileNotFoundError:
        logger.error(f"File not found: {input_file}")
        print(f"\n[ERROR] File not found: {input_file}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.warning("Run interrupted by user (Ctrl+C). Progress has been saved.")
        print("\n\n⚠️  Interrupted. Progress saved — rerun the same command to resume.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n[FATAL ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
