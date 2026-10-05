# Machine checks for Library\engineering\correlations\*.json
#
# Run with no arguments to check every record:
#     python Library\tools\check_correlations.py
#
# Exit code 0 = all checks pass, 1 = at least one failure.
# Intended to be run periodically: check 2 is the VR-11 integrity check and
# only fails once an archive that is supposed to be immutable has changed.
#
# ASCII-only per project rule P-7. Encoding is explicit on every read.

import hashlib
import json
import os
import sys

# This file lives in <workspace>\Library\tools\, so the workspace root is two
# levels up. Kept relative so the check survives the tree being moved.
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.abspath(os.path.join(TOOLS_DIR, os.pardir, os.pardir))
CORR_DIR = os.path.join(WORKSPACE, "Library", "engineering", "correlations")

# Field order from the registration format in validity_range.md.
KNOWN_FIELDS = [
    "key", "form", "variables", "common_name", "source_origin",
    "source_refs",
    "basis", "validity_range",
    "validity_gate", "validity_gate_ref",
    "limitations", "limitations_ref", "limitations_basis",
    "limitations_inference",
    "limitations_candidate", "candidate_basis", "candidate_author",
    "note",
]

# Present in every record, even when the value is null.
ALWAYS_REQUIRED = [
    "key", "form", "variables", "common_name", "source_origin",
    "source_refs", "basis", "validity_range",
    "validity_gate", "validity_gate_ref",
    "limitations", "limitations_ref",
    "limitations_candidate", "candidate_basis", "candidate_author",
    "note",
]

REF_FIELDS = ["limitations_ref", "validity_gate_ref"]
REF_TO_FIELD = {"limitations_ref": "limitations",
                "validity_gate_ref": "validity_gate"}

ENTRY_FIELDS = {"id", "path", "lines", "sha256", "referenced_by"}

BASIS_VALUES = {"published", "measured", "judgment", "unverified"}
LIM_BASIS_VALUES = {"explicit", "inferred"}


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    if not os.path.isdir(CORR_DIR):
        print("FAIL: correlations dir not found: %s" % CORR_DIR)
        return 1

    names = sorted(f for f in os.listdir(CORR_DIR) if f.endswith(".json"))
    if not names:
        print("FAIL: no records found in %s" % CORR_DIR)
        return 1

    fail = []          # (check_number, message)
    loaded = {}
    path_hashes = {}   # path -> {sha256: [record:entry, ...]}
    checked_files = {}  # path -> "ok" / "missing" / "mismatch"

    # --- check 4: json.load passes on every record -------------------------
    for name in names:
        full = os.path.join(CORR_DIR, name)
        try:
            with open(full, "r", encoding="utf-8") as fh:
                loaded[name] = json.load(fh)
        except Exception as exc:
            fail.append((4, "%s: json.load failed: %s" % (name, exc)))

    for name in sorted(loaded):
        rec = loaded[name]
        refs = rec.get("source_refs")

        # --- check 3: field hygiene ---------------------------------------
        unknown = [k for k in rec if k not in KNOWN_FIELDS]
        if unknown:
            fail.append((3, "%s: unknown fields %s" % (name, unknown)))

        missing = [k for k in ALWAYS_REQUIRED if k not in rec]
        if missing:
            fail.append((3, "%s: missing required fields %s" % (name, missing)))

        if rec.get("key") and not name.startswith(rec["key"]):
            fail.append((3, "%s: key %r does not match filename"
                         % (name, rec["key"])))

        if rec.get("basis") not in BASIS_VALUES:
            fail.append((3, "%s: basis %r not in %s"
                         % (name, rec.get("basis"), sorted(BASIS_VALUES))))

        # VR-8: limitations_basis required unless limitations is null.
        if rec.get("limitations") is not None:
            lb = rec.get("limitations_basis")
            if lb not in LIM_BASIS_VALUES:
                fail.append((3, "%s: limitations set but limitations_basis "
                             "is %r (VR-8)" % (name, lb)))
            if lb == "inferred" and not rec.get("limitations_inference"):
                fail.append((3, "%s: limitations_basis=inferred needs "
                             "limitations_inference (VR-8)" % name))

        if not isinstance(refs, list) or not refs:
            fail.append((3, "%s: source_refs must be a non-empty list" % name))
            continue

        ids = []
        for i, entry in enumerate(refs):
            if not isinstance(entry, dict):
                fail.append((3, "%s: source_refs[%d] is not an object"
                             % (name, i)))
                continue
            extra = set(entry) - ENTRY_FIELDS
            lack = ENTRY_FIELDS - set(entry)
            if extra:
                fail.append((3, "%s: source_refs[%d] extra keys %s"
                             % (name, i, sorted(extra))))
            if lack:
                fail.append((3, "%s: source_refs[%d] missing keys %s"
                             % (name, i, sorted(lack))))
                continue
            ids.append(entry["id"])
            if not isinstance(entry["referenced_by"], list) or not entry["referenced_by"]:
                fail.append((3, "%s: source_refs[%s].referenced_by must be a "
                             "non-empty list" % (name, entry["id"])))

            # --- check 2: hash matches the real file ----------------------
            target = os.path.join(WORKSPACE, entry["path"])
            if not os.path.isfile(target):
                checked_files[entry["path"]] = "missing"
                fail.append((2, "%s: source_refs[%s] path not found: %s"
                             % (name, entry["id"], entry["path"])))
            else:
                actual = sha256_of(target)
                if actual != entry["sha256"]:
                    checked_files[entry["path"]] = "mismatch"
                    fail.append((2, "%s: source_refs[%s] sha256 mismatch for "
                                 "%s\n      recorded %s\n      actual   %s"
                                 % (name, entry["id"], entry["path"],
                                    entry["sha256"], actual)))
                else:
                    checked_files.setdefault(entry["path"], "ok")

            # VR-11a hazard guard: one file must have one hash everywhere.
            slot = path_hashes.setdefault(entry["path"], {})
            slot.setdefault(entry["sha256"], []).append(
                "%s:%s" % (name, entry["id"]))

        dupes = sorted(set(x for x in ids if ids.count(x) > 1))
        if dupes:
            fail.append((3, "%s: duplicate source_refs ids %s" % (name, dupes)))

        # --- check 1: every *_ref resolves to an existing id --------------
        for field in REF_FIELDS:
            val = rec.get(field)
            owner = REF_TO_FIELD[field]
            if val is None:
                if rec.get(owner) is not None:
                    fail.append((1, "%s: %s is set but %s is null"
                                 % (name, owner, field)))
                continue
            if val not in ids:
                fail.append((1, "%s: %s=%r not found in source_refs ids %s"
                             % (name, field, val, ids)))
                continue
            entry = [e for e in refs if e.get("id") == val][0]
            if owner not in entry.get("referenced_by", []):
                fail.append((1, "%s: %s points at %r but its referenced_by "
                             "%s does not list %r"
                             % (name, field, val,
                                entry.get("referenced_by"), owner)))

        # referenced_by must not claim a field that is null.
        for entry in refs:
            if not isinstance(entry, dict):
                continue
            for claimed in entry.get("referenced_by") or []:
                if claimed == "form":
                    continue
                if rec.get(claimed) is None:
                    fail.append((1, "%s: source_refs[%s].referenced_by lists "
                                 "%r but that field is null"
                                 % (name, entry.get("id"), claimed)))

    # --- check 5 (VR-11a): same path never carries two different hashes ----
    for path, by_hash in sorted(path_hashes.items()):
        if len(by_hash) > 1:
            detail = "; ".join("%s used by %s" % (h[:12], sorted(users))
                               for h, users in sorted(by_hash.items()))
            fail.append((5, "path %s has %d different hashes: %s"
                         % (path, len(by_hash), detail)))

    total_entries = sum(len(r.get("source_refs") or []) for r in loaded.values())
    gated = sorted(n for n, r in loaded.items()
                   if r.get("validity_gate") is not None)

    print("records:              %d" % len(names))
    print("source_refs entries:  %d" % total_entries)
    print("distinct files cited: %d" % len(path_hashes))
    print("records with a gate:  %d  %s" % (len(gated), gated))
    print("")

    labels = {
        1: "check 1  every *_ref resolves to a source_refs id",
        2: "check 2  every sha256 matches the real file (VR-11)",
        3: "check 3  field hygiene: no unknown / no missing",
        4: "check 4  json.load passes on every record",
        5: "check 5  one file, one hash (VR-11a hazard guard)",
    }
    for num in sorted(labels):
        bad = [m for n, m in fail if n == num]
        print("%-58s %s" % (labels[num],
                            "PASS" if not bad else "FAIL (%d)" % len(bad)))

    if fail:
        print("")
        print("FAILURES:")
        for num, msg in fail:
            print("  [check %d] %s" % (num, msg))
        return 1

    print("")
    print("cited files verified:")
    for path in sorted(checked_files):
        print("  %s  %s" % (checked_files[path], path))
    print("")
    print("ALL CHECKS PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
