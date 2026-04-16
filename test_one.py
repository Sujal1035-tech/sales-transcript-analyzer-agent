import json
import sys

from src.config import validate
from src.preprocessor import preprocess
from src.analyzer import analyze_transcript

# ─────────────────────────────────────────────
# Paste your test transcript here (or leave as is to use the sample)
# ─────────────────────────────────────────────
SAMPLE_TRANSCRIPT = [
{"speaker":"SPEAKER_00","start":0.03,"stop":1.33,"transcription":"हलो हलो हाँ जी"},{"speaker":"SPEAKER_01","start":1.35,"stop":2.39,"transcription":"जी गुड ईवनिंग सर"},{"speaker":"SPEAKER_00","start":2.39,"stop":3.81,"transcription":"ओ आंजी को"},{"speaker":"SPEAKER_01","start":3.42,"stop":6.51,"transcription":"जी मैं आयुष की बात कर रही हूँ व्यापार अप्लीकेशन से"},{"speaker":"SPEAKER_00","start":6.68,"stop":7.22,"transcription":"श्री सन्"},{"speaker":"SPEAKER_01","start":7.22,"stop":11.59,"transcription":"मेरा आप ऐसी बात है ना उस ना व्यापार एप्लीकेशन के डेमो के रिगार्डिंग"},{"speaker":"SPEAKER_00","start":11.59,"stop":12.48,"transcription":"हाँजी मैम"},{"speaker":"SPEAKER_01","start":12.48,"stop":15.62,"transcription":"तो आपको अभी तक व्यापारी फ्लिक्स उनका डेवो मिला या नहीं मिला"},{"speaker":"SPEAKER_00","start":15.71,"stop":16.8,"transcription":"हाँ मैं नि"},{"speaker":"SPEAKER_01","start":16.8,"stop":19.88,"transcription":"मिल चुका है ठीक है तो कोई डाउट या कोई नहीं सर आपको"},{"speaker":"SPEAKER_00","start":19.88,"stop":21.7,"transcription":"नहीं मैम कोई डाउट इंक्वायरी नहीं है"},{"speaker":"SPEAKER_01","start":21.7,"stop":23.55,"transcription":"बिजनेस किस चीज़ की है सर आपकी"},{"speaker":"SPEAKER_00","start":23.55,"stop":24.31,"transcription":"मैम ई कमर्स"},{"speaker":"SPEAKER_01","start":24.69,"stop":30.81,"transcription":"जी कॉमर्स तो सर लाइसेंस परचेज करने का क्या प्लान है मतलब क्योंकि आपको आपका टेल्थ रेट भी एक्सपायर हो चुका है ना"},{"speaker":"SPEAKER_00","start":30.81,"stop":31.32,"transcription":"ऐसा"},{"speaker":"SPEAKER_01","start":31.32,"stop":32.43,"transcription":"जी तो बताइए सर"},{"speaker":"SPEAKER_00","start":31.84,"stop":34.24,"transcription":"अभी मैंने डिसाइड नहीं किया"},{"speaker":"SPEAKER_00","start":34.44,"stop":39.18,"transcription":"जो मेरे पार्टनर थे मुझे एक बार डिसाइड कर मैं एक बार आपको कंफर्म कर दूंगा"},{"speaker":"SPEAKER_01","start":34.52,"stop":34.62,"transcription":"ए"},{"speaker":"SPEAKER_01","start":39.18,"stop":39.92,"transcription":"अच्छा"},{"speaker":"SPEAKER_00","start":39.48,"stop":49,"transcription":"वैसे तो मुझे हमें व्यापार है पसंद आया हमने लाइक लेने का सोचा लिया बट अभी डिसीजन मेरे वो जो पार्टनर है वो लेंगे उसके बाद ऐसा"},{"speaker":"SPEAKER_01","start":44.41,"stop":45.86,"transcription":"डिसीजन मेरे"},{"speaker":"SPEAKER_01","start":49,"stop":53.39,"transcription":"ओके क्योंकि क्या है ना सर दो फरवरी से प्राइवेटिंग भी इंक्रीज हो रही है"},{"speaker":"SPEAKER_00","start":53.54,"stop":54.39,"transcription":"ओके ओके"},{"speaker":"SPEAKER_00","start":54.52,"stop":56.58,"transcription":"मैं पोलिंग पाकिंगे"},{"speaker":"SPEAKER_01","start":54.59,"stop":55.23,"transcription":"सें बोलिए"},{"speaker":"SPEAKER_00","start":56.9,"stop":59.06,"transcription":"हाँ हाँ हम करेंगे बहुत मैं"},{"speaker":"SPEAKER_01","start":59.45,"stop":62.76,"transcription":"ठीक है तो कब तक कुछ एक्सपेक्टेड डेट वगैरह बता सकते हैं क्या"},{"speaker":"SPEAKER_00","start":62.27,"stop":70.38,"transcription":"मैम एक्चुअली मैम मैं अभी ट्रैवल कर रहा हूँ तो मेरे को टाइम लगेगा वन वीक तक टाइम लगेगा मैं आपको वन वीक तक आपको कन्फर्म करता हूँ"},{"speaker":"SPEAKER_01","start":70.38,"stop":76.17,"transcription":"ठीक है ठीक है वो मेरा इस नंबर पर तो कॉल बैक नहीं आ पाएगा मैं व्हाट्सएप पे मैसेज डालती हूँ उस नंबर पर"},{"speaker":"SPEAKER_00","start":75.66,"stop":76.05,"transcription":"हाँ"}]


def print_divider(char="─", width=60):
    print(char * width)


def print_result(result: dict):
    print_divider("═")  
    print("  ANALYSIS RESULT")
    print_divider("═")

    print(f"\n📝  SUMMARY")
    print(f"    {result.get('summary', 'N/A')}\n")

    print(f"💡  KEY TAKEAWAYS")
    for i, t in enumerate(result.get("key_takeaways", []), 1):
        print(f"    {i}. {t}")

    intent = result.get("intent", "N/A")
    intent_emoji = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(intent, "⚪")
    print(f"\n🎯  INTENT       {intent_emoji}  {intent.upper()}")

    rating = result.get("call_rating", "N/A")
    stars = "⭐" * int(rating) if isinstance(rating, int) else ""
    print(f"⭐  CALL RATING  {rating}/5  {stars}")

    print(f"\n⚠️   CUSTOMER OBJECTION")
    print(f"    {result.get('customer_objection', 'N/A')}")

    print(f"\n🛠️   AGENT RESOLUTION")
    print(f"    {result.get('agent_resolution', 'N/A')}")

    print_divider("═")


def main():
    # Step 1: Validate API key
    try:
        validate()
    except EnvironmentError as e:
        print(str(e))
        sys.exit(1)

    # Step 2: Load transcript
    print("\n" + "─" * 60)
    print("  TRANSCRIPT ANALYZER — Single Test Mode")
    print("─" * 60)
    print("Using built-in SAMPLE_TRANSCRIPT (edit test_one.py to change it)")
    print("─" * 60)

    segments = SAMPLE_TRANSCRIPT

    # Step 3: Preprocess
    print("\n[1/3] Preprocessing transcript...")
    dialogue = preprocess(segments)

    if not dialogue.strip():
        print("ERROR: Preprocessor returned empty dialogue. Check your transcript.")
        sys.exit(1)

    print(f"      ✓ {len(dialogue.splitlines())} dialogue turns | {len(dialogue)} chars")
    print("\n── Cleaned Dialogue ──────────────────────────────────")
    print(dialogue)
    print("──────────────────────────────────────────────────────")

    # Step 4: Analyze
    print("\n[2/3] Sending to Gemini (gemini-2.5-flash)...")
    result = analyze_transcript(dialogue)

    if "error" in result:
        print(f"\nERROR: Analysis failed — {result.get('last_error', 'unknown')}")
        sys.exit(1)

    # Step 5: Print result
    print("\n[3/3] Done!\n")
    print_result(result)


if __name__ == "__main__":
    main()
