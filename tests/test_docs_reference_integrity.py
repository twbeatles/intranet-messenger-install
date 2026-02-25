# -*- coding: utf-8 -*-

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SESSION_DOCS = ('claude.md', 'gemini.md')
LEGACY_REFERENCES = ('TRANSITION_CHECKLIST.md', 'FUNCTIONAL_REVIEW_20260223.md')


def _has_deprecation_marker(line: str) -> bool:
    lowered = line.lower()
    return (
        'deprecated' in lowered
        or '대체' in line
        or '폐기' in line
        or 'removed' in lowered
    )


def test_docs_references_exist_or_are_marked_deprecated():
    for session_doc_name in SESSION_DOCS:
        session_doc_path = ROOT / session_doc_name
        text = session_doc_path.read_text(encoding='utf-8')
        lines = text.splitlines()

        for ref in LEGACY_REFERENCES:
            marker = f'`{ref}`'
            if marker not in text:
                continue

            if (ROOT / ref).exists():
                continue

            matched_lines = [line for line in lines if marker in line]
            assert matched_lines, f"{session_doc_name} must contain a line for {ref}"
            assert any(_has_deprecation_marker(line) for line in matched_lines), (
                f"{session_doc_name} references missing {ref} without a deprecation/replacement marker"
            )
