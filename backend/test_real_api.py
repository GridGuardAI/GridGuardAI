"""
Usage:
    python test_real_api.py                          # text-only test
    python test_real_api.py /path/to/bill_photo.jpg   # text + vision test
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_text_call():
    print("=" * 60)
    print("TEST 1: Plain text LLM call")
    print("=" * 60)
    from agents.llm_client import call_llm
    try:
        response = call_llm(
            "In one sentence, what does a power factor below 0.8 usually indicate?",
            system="You are an electrical engineering assistant.",
            max_tokens=100,
        )
        print("✅ SUCCESS")
        print("Response:", response)
        return True
    except Exception as e:
        print("❌ FAILED")
        print("Error:", repr(e))
        print("\nCommon causes:")
        print("  - GEMINI_API_KEY missing/invalid in .env")
        print("  - .env not in the same folder you're running this from")
        print("  - Model name outdated (check GEMINI_MODEL in .env if you set one)")
        return False


def test_pipeline_with_real_llm():
    print("\n" + "=" * 60)
    print("TEST 2: Full pipeline (engine + real agents, no vision)")
    print("=" * 60)
    from engine.engineering_engine import EngineInput
    from agents.orchestrator import run_full_pipeline
    try:
        inp = EngineInput(
            current_consumption_kwh=1250,
            previous_consumption_kwh=850,
            billing_days=30,
            supply_voltage_v=246,
            current_a=10,
            power_factor=0.76,
            num_phases=1,
            tariff_pkr_per_kwh=45.0,
        )
        report = run_full_pipeline(inp)
        print("✅ SUCCESS")
        print(f"Anomalies found: {len(report['diagnosis'])}")
        for d in report["diagnosis"]:
            print(f"  - {d['type']} ({d['severity']}) -> {d['confidence']}")
            print(f"    {d['explanation'][:150]}")
        print(f"\nRecommendations:\n{report['recommendations']}")
        return True
    except Exception as e:
        print("❌ FAILED")
        print("Error:", repr(e))
        return False


def test_vision_call(image_path):
    print("\n" + "=" * 60)
    print(f"TEST 3: Bill extraction (vision) on {image_path}")
    print("=" * 60)
    from extraction.bill_extraction import extract_bill_fields

    if not os.path.exists(image_path):
        print(f"❌ File not found: {image_path}")
        return False

    ext = os.path.splitext(image_path)[1].lower()
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".pdf": "application/pdf"}
    mime_type = mime_map.get(ext, "image/jpeg")

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    try:
        result = extract_bill_fields(image_bytes, mime_type)
        print("✅ SUCCESS (call completed - check output below for extraction quality)")
        print("\nExtracted fields:")
        for k, v in result.items():
            if k not in ("fields_found", "fields_missing"):
                print(f"  {k}: {v}")
        print(f"\nFields found: {result['fields_found']}")
        print(f"Fields missing: {result['fields_missing']}")

        if not result["fields_found"]:
            print("\n⚠️  WARNING: Zero fields extracted. The call succeeded but the")
            print("   model couldn't read anything useful from this image. Check:")
            print("   - Is the image clear/high-resolution enough?")
            print("   - Is it actually a bill (not a random photo)?")
            print("   - Try a different bill photo or a cleaner scan/PDF.")
        return True
    except Exception as e:
        print("❌ FAILED")
        print("Error:", repr(e))
        return False


if __name__ == "__main__":
    ok1 = test_text_call()
    if not ok1:
        print("\nStopping here - fix the text LLM call before testing vision.")
        sys.exit(1)

    ok2 = test_pipeline_with_real_llm()

    if len(sys.argv) > 1:
        ok3 = test_vision_call(sys.argv[1])
    else:
        print("\n(Skipping vision test - pass a bill image path as an argument to test it,")
        print(" e.g. python test_real_api.py sample_bill.jpg)")
        ok3 = None

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Text LLM call:     {'PASS' if ok1 else 'FAIL'}")
    print(f"Full pipeline:     {'PASS' if ok2 else 'FAIL'}")
    if ok3 is not None:
        print(f"Vision extraction: {'PASS' if ok3 else 'FAIL'}")
