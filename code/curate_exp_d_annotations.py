"""Curate high-confidence EXP-D slots and propagate them to paired variants."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def number(surface: str, value: int, kind: str = "quantity") -> dict:
    return {"surface": surface, "normalized_value": value, "kind": kind, "confidence": "high"}


def date(surface: str, value: str) -> dict:
    return {"surface": surface, "normalized_value": value, "confidence": "high"}


def entity(surface: str, entity_type: str, canonical: str | None = None) -> dict:
    return {
        "surface": surface,
        "type": entity_type,
        "canonical": canonical or surface,
        "confidence": "high",
    }


CURATED = {
    "regional-bho-001": {
        "numbers": [number("तिरानबे हजार", 93000, "amount")],
        "currency": [{"surface": "रुपिया", "currency": "INR", "confidence": "high"}],
    },
    "regional-bho-002": {
        "numbers": [number("तीन तीन पाच सात नौ छौ पांच जीरो छौ पांच छौ आठ पांच चार पाच पाच", 3357965065685455, "identifier"), number("नौ नौ तीन", 993, "cvv")],
        "dates": [date("अक्टूबर दू हजार अठाईस", "2028-10")],
    },
    "regional-bho-003": {
        "entities": [entity("पी एच सी", "organization", "PHC"), entity("डॉ मुथुलक्ष्मी", "person")],
        "review_required": True,
    },
    "regional-bho-004": {
        "numbers": [number("डबल जीरो छह डबल जीरो पैतीस डबल जीरो डबल जीरो चार छब्बीस", 60035000426, "account_identifier")],
    },
    "fleurs-hi-1602": {"entities": [entity("मेजरकेन", "cuisine", "Mexican")], "review_required": False},
    "fleurs-hi-1601": {"entities": [entity("ओसेलोट्स", "animal")], "review_required": True},
    "fleurs-hi-1608": {"entities": [entity("आर्मंड वर्सास", "person")], "review_required": True},
    "fleurs-hi-1607": {"numbers": [number("आधे घंटे", 30, "duration_minutes")]},
    "fleurs-kn-1620": {"entities": [entity("ಜಾವಾನೀಸ್", "cultural_group"), entity("ಜಾವಾ", "location")]},
    "fleurs-kn-1516": {"entities": [entity("ಹೋಲೋಕಾಸ್ಟ್", "historical_event"), entity("ನಾಜಿಗಳ", "group")], "review_required": True},
    "fleurs-kn-1625": {"entities": [entity("ಶ್ರೀ ಶ್ಯಾಮ್", "person_or_deity")], "review_required": True},
    "fleurs-kn-1574": {"entities": [entity("ಥರ್ಮಾಮೀಟರ್", "technical")], "review_required": True},
    "regional-mai-001": {"entities": [entity("मधुबनी", "location")]},
    "regional-mai-002": {},
    "regional-mai-003": {},
    "regional-mai-004": {},
    "fleurs-ml-1538": {"entities": [entity("പോയിൻ്റ് മരിയൻ", "location"), entity("ഫെയർമോണ്ട്", "location"), entity("ബഫല്ലോ-പിറ്റ്സ്ബർഗ് ഹൈവേ", "location")]},
    "fleurs-ml-1549": {},
    "fleurs-ml-1524": {},
    "fleurs-ml-1622": {"entities": [entity("യുഎസ്", "country", "United States"), entity("ജോർജ്ജ് ഡബ്ല്യു ബുഷ്", "person", "George W. Bush")]},
    "fleurs-ta-1623": {},
    "fleurs-ta-1644": {"entities": [entity("மைக்", "person", "Mike"), entity("மில்லர்", "person", "Miller")]},
    "fleurs-ta-1544": {},
    "fleurs-ta-1635": {},
    "fleurs-te-1519": {},
    "fleurs-te-1577": {},
    "fleurs-te-1538": {"entities": [entity("point marion", "location"), entity("fairmont", "location"), entity("buffalo-pittsburgh", "location"), entity("backwoods", "location")]},
    "fleurs-te-1652": {"entities": [entity("మోల్డోవాలో", "location", "Moldova"), entity("ఆర్థోడాక్స్ క్రిస్టియన్", "religion")]},
    "fleurs-ur-1537": {},
    "fleurs-ur-1643": {"numbers": [number("19،500", 19500, "area_quantity"), number("14", 14, "count")], "review_required": True},
    "fleurs-ur-1538": {"entities": [entity("پوائنٹ میرین", "location"), entity("فیئرماؤنٹ", "location"), entity("بفیلو-پٹسبرگ ہائیوے", "location")]},
    "fleurs-ur-1539": {},
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    clean_ids = {row["sample_id"] for row in rows if row["conditions"]["audio"] == ["clean"]}
    missing = clean_ids - CURATED.keys()
    if missing:
        raise ValueError(f"missing curated rows: {sorted(missing)}")
    by_id = {row["sample_id"]: row for row in rows}
    output = []
    for row in rows:
        parent = row["conditions"].get("clean_twin") or row["sample_id"]
        slots = CURATED[parent]
        output.append(
            {
                "sample_id": row["sample_id"],
                "clean_twin": parent,
                "language": row["language"],
                "reference": row["reference"],
                "verified_slots": {
                    "numbers": slots.get("numbers", []),
                    "dates": slots.get("dates", []),
                    "currency": slots.get("currency", []),
                },
                "verified_entities": slots.get("entities", []),
                "review_required": bool(slots.get("review_required", False)),
                "annotation_status": "curated_v1_agent_reviewed",
                "annotation_note": "Agent-reviewed labels; transliteration and compositional numeric equivalence remain conservative limitations.",
            }
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in output) + "\n", encoding="utf-8")
    print(json.dumps({"sample_count": len(output), "unique_clean_count": len(clean_ids), "review_rows": sum(row["review_required"] for row in output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
