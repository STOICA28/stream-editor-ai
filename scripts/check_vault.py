#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vault consistency checker.

Run before every commit and as part of CI:
    python scripts/check_vault.py

Exits 0 on success, 1 on any errors.
Warnings (missing frontmatter on non-required docs, broken wikilinks) go to
stderr but do not cause a non-zero exit.
"""
import io
import re
import sys
from pathlib import Path

# Force UTF-8 output on Windows to handle Unicode characters in output
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

VAULT_ROOT = Path(__file__).parent.parent / "knowledge-vault"

# Documents that MUST exist and MUST have valid frontmatter.
# Missing any of these is a hard error.
REQUIRED_DOCS: list[str] = [
    "00_HOME/README.md",
    "00_HOME/PROJECT_STATUS.md",
    "01_PRODUCT/PRODUCT_VISION.md",
    "01_PRODUCT/MVP_ACCEPTANCE_CRITERIA.md",
    "01_PRODUCT/PRODUCT_PRINCIPLES.md",
    "02_ARCHITECTURE/SYSTEM_OVERVIEW.md",
    "02_ARCHITECTURE/JOB_SYSTEM.md",
    "02_ARCHITECTURE/MEDIA_PIPELINE.md",
    "02_ARCHITECTURE/MODEL_PROVIDER_ARCHITECTURE.md",
    "03_EDITORIAL_BIBLE/EDITORIAL_PHILOSOPHY.md",
    "03_EDITORIAL_BIBLE/KEEP_VS_CUT.md",
    "05_SCHEMAS/TIMELINE_EVENT.md",
    "05_SCHEMAS/EDIT_PLAN.md",
    "05_SCHEMAS/EFFECTS.md",
    "07_ADR/ADR-001-obsidian-as-source-of-truth.md",
    "07_ADR/ADR-002-structured-edit-plan.md",
]

VALID_STATUSES = {"draft", "research", "proposal", "canonical", "deprecated"}

REQUIRED_FRONTMATTER_FIELDS = ["id:", "title:", "status:"]


def check_frontmatter(path: Path) -> list[str]:
    """
    Validate YAML frontmatter in a vault document.

    Returns a list of error strings (empty if valid).
    """
    errors: list[str] = []
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"{path.relative_to(VAULT_ROOT)}: cannot read file: {exc}"]

    if not content.startswith("---"):
        errors.append(
            f"{path.relative_to(VAULT_ROOT)}: missing YAML frontmatter (must start with ---)"
        )
        return errors

    # Find closing ---
    try:
        end = content.index("---", 3)
    except ValueError:
        errors.append(
            f"{path.relative_to(VAULT_ROOT)}: frontmatter not closed (no closing ---)"
        )
        return errors

    fm = content[3:end]

    # Required fields
    for field in REQUIRED_FRONTMATTER_FIELDS:
        if field not in fm:
            errors.append(
                f"{path.relative_to(VAULT_ROOT)}: frontmatter missing field '{field}'"
            )

    # Validate status value
    status_match = re.search(r"status:\s*(\S+)", fm)
    if status_match:
        status_val = status_match.group(1).strip('"').strip("'")
        if status_val not in VALID_STATUSES:
            errors.append(
                f"{path.relative_to(VAULT_ROOT)}: invalid status '{status_val}' "
                f"(valid: {', '.join(sorted(VALID_STATUSES))})"
            )

    return errors


def check_internal_links(path: Path, vault_stems: set[str]) -> list[str]:
    """
    Check that [[wikilinks]] in the document resolve to existing vault files.

    Obsidian wikilinks can be:
      [[Filename]]           → matches by stem (filename without extension)
      [[Folder/Filename]]    → matches by path stem (last component)
      [[Filename|alias]]     → the alias part is stripped

    Only warns; does not error.
    """
    warnings: list[str] = []
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return warnings

    wikilinks = re.findall(r"\[\[([^\]|#]+)", content)
    for link in wikilinks:
        link_clean = link.strip()
        # For path-style links like [[00_HOME/PROJECT_STATUS]], check the last component
        link_stem = Path(link_clean).stem  # e.g., "PROJECT_STATUS"
        if link_stem not in vault_stems:
            warnings.append(
                f"WARNING: {path.relative_to(VAULT_ROOT)}: "
                f"broken wikilink [[{link_clean}]]"
            )
    return warnings


def main() -> None:
    errors: list[str] = []
    warnings: list[str] = []

    if not VAULT_ROOT.exists():
        print(
            f"ERROR: knowledge-vault not found at {VAULT_ROOT}\n"
            "Create the vault directory and run the vault setup first.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Collect all markdown files in vault for link checking
    all_vault_files = set(VAULT_ROOT.rglob("*.md"))
    vault_stems = {f.stem for f in all_vault_files}

    # -------------------------------------------------------------------------
    # 1. Check all required documents exist and have valid frontmatter
    # -------------------------------------------------------------------------
    present = 0
    for doc in REQUIRED_DOCS:
        path = VAULT_ROOT / doc
        if not path.exists():
            errors.append(f"MISSING required document: {doc}")
        else:
            present += 1
            doc_errors = check_frontmatter(path)
            errors.extend(doc_errors)

    # -------------------------------------------------------------------------
    # 2. Warn on any .md file in vault that lacks frontmatter
    # -------------------------------------------------------------------------
    required_paths = {VAULT_ROOT / doc for doc in REQUIRED_DOCS}
    for md_file in all_vault_files:
        if md_file in required_paths:
            continue  # Already checked above
        try:
            content = md_file.read_text(encoding="utf-8")
        except OSError:
            continue
        if not content.startswith("---"):
            rel = md_file.relative_to(VAULT_ROOT)
            warnings.append(
                f"WARNING: {rel}: missing frontmatter (not required, but recommended)"
            )

    # -------------------------------------------------------------------------
    # 3. Check internal wikilinks (warn only)
    # -------------------------------------------------------------------------
    for md_file in all_vault_files:
        warnings.extend(check_internal_links(md_file, vault_stems))

    # -------------------------------------------------------------------------
    # Output
    # -------------------------------------------------------------------------
    if warnings:
        for w in warnings:
            print(w, file=sys.stderr)

    if errors:
        print("\n[FAIL] VAULT CONSISTENCY ERRORS:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        print(
            f"\nFound {len(errors)} error(s). Fix these before committing.",
            file=sys.stderr,
        )
        sys.exit(1)
    else:
        warn_count = len([w for w in warnings if w.startswith("WARNING:")])
        print(
            f"[OK] Vault: {present}/{len(REQUIRED_DOCS)} required docs present and valid"
            + (f"  ({warn_count} warnings)" if warn_count else "")
        )
        sys.exit(0)


if __name__ == "__main__":
    main()