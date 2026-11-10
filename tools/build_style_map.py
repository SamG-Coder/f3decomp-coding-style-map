"""Validate public evidence metadata and render deterministic Markdown documents."""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERDICTS = {"verified", "unfit", "pending", "unknown", "failed", "rejected"}


def validate(data):
    if data.get("schema_version") != 1:
        raise ValueError("Unsupported schema version")
    expected = {"schema_version", "project", "exported_at", "scope", "attribution_warning", "provenance_limit", "unrecoverable_from_this_evidence", "clusters", "evidence"}
    if set(data) != expected:
        raise ValueError("Unexpected or missing public document fields")
    records = data["evidence"]
    allowed = {"id", "address", "size", "source_sha256", "hash_check", "local_check", "server_verdict"}
    for key, record in records.items():
        if set(record) != allowed or record["id"] != key:
            raise ValueError(f"Invalid evidence fields: {key}")
        if not re.fullmatch(r"[0-9]+[a-z0-9]*", key):
            raise ValueError(f"Invalid evidence ID: {key}")
        if not re.fullmatch(r"0x[0-9a-fA-F]{8}", record["address"]):
            raise ValueError(f"Invalid address: {key}")
        if type(record["size"]) is not int or record["size"] <= 0:
            raise ValueError(f"Invalid extent: {key}")
        if not re.fullmatch(r"[0-9a-f]{64}", record["source_sha256"]):
            raise ValueError(f"Invalid hash: {key}")
        check = record["local_check"]
        if set(check) != {"status", "diffs", "checker", "reviewed_diagnostic_count"}:
            raise ValueError(f"Unexpected local check fields: {key}")
        if check["status"] != "match" or type(check["diffs"]) is not int or check["diffs"] != 0:
            raise ValueError(f"Evidence is not a recorded exact local match: {key}")
        if type(check["reviewed_diagnostic_count"]) is not int or check["reviewed_diagnostic_count"] < 0:
            raise ValueError(f"Invalid diagnostic count: {key}")
        if record["server_verdict"] not in VERDICTS:
            raise ValueError(f"Unknown verdict label: {key}")
    cluster_ids, pattern_ids = set(), set()
    for group in data["clusters"]:
        if set(group) != {"id", "label", "developer_guess", "attribution_confidence", "patterns"}:
            raise ValueError("Unexpected cluster fields")
        if group["id"] in cluster_ids:
            raise ValueError("Duplicate cluster ID")
        cluster_ids.add(group["id"])
        for pattern in group["patterns"]:
            if set(pattern) != {"id", "habit", "evidence", "pattern_confidence", "use", "limit"}:
                raise ValueError("Unexpected pattern fields")
            if pattern["id"] in pattern_ids:
                raise ValueError("Duplicate observation ID")
            pattern_ids.add(pattern["id"])
            if not pattern["evidence"] or any(key not in records for key in pattern["evidence"]):
                raise ValueError(f"Missing evidence: {pattern['id']}")
    text = json.dumps(data)
    if re.search(r"(?:[A-Za-z]:[\\/]|/mnt/|/home/|/Users/|private/practice|Bearer\s|gh[pousr]_[A-Za-z0-9]{20})", text):
        raise ValueError("Private path or credential-like text in public data")


def cell(value):
    return str(value).replace("|", "\\|").replace("\r", "").replace("\n", " ")


def render(data):
    validate(data)
    records = data["evidence"]
    count = sum(len(group["patterns"]) for group in data["clusters"])
    lines = ["# Coding-style evidence map", "", f"{len(records)} locally exact examples · {count} observations · {len(data['clusters'])} tentative clusters", "", f"Exported: {data['exported_at']}", "", data["scope"], "", data["attribution_warning"], "", data["provenance_limit"], "", "Evidence links lead to public metadata, not private candidate source. Server verdicts are recorded independently of local matches.", ""]
    for group in data["clusters"]:
        lines += [f"## Cluster {group['id']}: {group['label']}", "", group["developer_guess"], "", f"Author attribution confidence: **{group['attribution_confidence']}**.", "", "| Observation | Evidence | How to use it | Limits |", "| --- | --- | --- | --- |"]
        for pattern in group["patterns"]:
            refs = ", ".join(f"[{records[key]['address']} ({key})](evidence.md#evidence-{key})" for key in pattern["evidence"])
            lines.append(f"| **{pattern['id']}** — {cell(pattern['habit'])} Evidence: {cell(pattern['pattern_confidence'])}. | {refs} | {cell(pattern['use'])} | {cell(pattern['limit'])} |")
        lines.append("")
    lines += ["## Not recoverable from this evidence", ""] + [f"- {item}" for item in data["unrecoverable_from_this_evidence"]]
    evidence = ["# Evidence metadata", "", data["provenance_limit"], "", "Verdicts describe the exported snapshot. An unknown verdict is not a verification. Nonzero reviewed-diagnostic counts mean the private workflow recorded diagnostics requiring review; their text is not published.", ""]
    for key, record in records.items():
        check = record["local_check"]
        evidence += [f"## Evidence {key}", "", f"- Function: `{record['address']}`; extent: {record['size']} bytes.", f"- Recorded local result: **{check['status']}**, {check['diffs']} differences.", f"- Recorded server verdict: **{record['server_verdict']}**.", f"- Checker: {check['checker']}.", f"- Reviewed diagnostics: {check['reviewed_diagnostic_count']}.", f"- Source SHA-256: `{record['source_sha256']}`.", f"- Hash provenance: {record['hash_check']}.", ""]
    return {"coding-style-map.md": "\n".join(lines).rstrip() + "\n", "evidence.md": "\n".join(evidence).rstrip() + "\n"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if generated documents differ")
    args = parser.parse_args()
    data = json.loads((ROOT / "data/style-map.json").read_text(encoding="utf-8"))
    for name, content in render(data).items():
        path = ROOT / "docs" / name
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                raise SystemExit(f"Stale generated document: {path.name}")
        else:
            path.parent.mkdir(exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")
    print(f"{'Checked' if args.check else 'Built'} {len(data['evidence'])} evidence records across {len(data['clusters'])} clusters.")


if __name__ == "__main__":
    main()
