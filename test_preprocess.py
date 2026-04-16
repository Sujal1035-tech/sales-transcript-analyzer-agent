"""
test_preprocess.py
------------------
Runs ONLY the preprocessing step on the SAMPLE_TRANSCRIPT in test_one.py.
No Gemini call, no API key needed.

Usage:
    python test_preprocess.py
"""

from test_one import SAMPLE_TRANSCRIPT
from src.preprocessor import preprocess

dialogue = preprocess(SAMPLE_TRANSCRIPT)
turns = dialogue.count("\n") + 1 if dialogue else 0

print(f"Turns after preprocessing: {turns}")
print("=" * 60)
print(dialogue)
