"""Export an explicit allowlist of metadata from a private workspace map."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from build_style_map import ROOT, VERDICTS, validate


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def export(source, ledger=(), status=None):
    verdicts = {entry["receipt"]: entry.get("server_verdict") for entry in ledger}
    for entry in (status or {}).get("recent", []):
        verdicts[entry["id"]] = entry.get("verdict") or "pending"
    records = {}
    for key, record in source["evidence"].items():
        verdict = verdicts.get(record.get("submission_id"), record.get("server_verdict"))
        check = record["local_check"]
        records[key] = {
            "id": key, "address": record["address"], "size": record["size"],
            "source_sha256": record["current_source_sha256"], "hash_check": record["source_hash_check"],
            "local_check": {"status": check["status"], "diffs": check["diffs"], "checker": check["checker"], "reviewed_diagnostic_count": len(check.get("reviewed_diagnostics", []))},
            "server_verdict": verdict if verdict in VERDICTS else "unknown",
        }
    clusters = []
    for group in source["clusters"]:
        public = {key: group[key] for key in ("id", "label", "developer_guess", "attribution_confidence")}
        public["patterns"] = [{key: pattern[key] for key in ("id", "habit", "evidence", "pattern_confidence", "use", "limit")} for pattern in group["patterns"]]
        clusters.append(public)
    data = {
        "schema_version": 1, "project": "f3decomp coding-style map",
        "exported_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scope": "Selected source-pattern observations from a contributor workspace; not an exhaustive author analysis.",
        "attribution_warning": "The six clusters are tentative style or library groupings, not identified developers. Original names, formatting and authorship cannot be recovered from matching compiler output alone.",
        "provenance_limit": "Metadata records private checker results and retained server verdicts. Candidate source, game bytes, context packs and raw diagnostics are not published. These documents cannot independently reproduce or attest the historical binary matches.",
        "unrecoverable_from_this_evidence": source["unrecoverable_from_this_evidence"],
        "clusters": clusters, "evidence": records,
    }
    validate(data)
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("map", type=Path)
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--status", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "data/style-map.json")
    args = parser.parse_args()
    data = export(read(args.map), read(args.ledger) if args.ledger else (), read(args.status) if args.status else None)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"Exported {len(data['evidence'])} public evidence records.")


if __name__ == "__main__":
    main()
