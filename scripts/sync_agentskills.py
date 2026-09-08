#!/usr/bin/env python3
"""Check and synchronize the local AgentSkills.io documentation mirror.

Check mode is read-only and safe to run locally.
Write mode is intentionally restricted to the controlled GitHub Actions workflow.
Only Python's standard library is used.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

LLMS_URL = "https://agentskills.io/llms.txt"
SOURCE_DOMAIN = "https://agentskills.io"
UPSTREAM_REPOSITORY = "https://github.com/agentskills/agentskills"
UPSTREAM_DOCS_COMMITS_API = (
    "https://api.github.com/repos/agentskills/agentskills/commits?path=docs&per_page=1"
)
USER_AGENT = "agentskills-docs-sync/1.0"
LLMS_ENTRY_RE = re.compile(
    r"^- \[(?P<title>[^\]]+)\]\((?P<url>https://agentskills\.io/[^\s)]+\.md)\):\s*(?P<description>.*)$"
)


@dataclass(frozen=True)
class RemoteDocument:
    title: str
    description: str
    canonical_md_url: str
    source_url: str
    file_name: str
    content: str


def _request_text(url: str, token: str | None = None) -> str:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/plain, text/markdown, application/json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=30) as response:
            raw = response.read()
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"Failed to retrieve {url}: {exc}") from exc
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RuntimeError(f"Expected UTF-8 content from {url}") from exc


def parse_llms(text: str) -> list[dict[str, str]]:
    documents: list[dict[str, str]] = []
    for line in text.replace("\r\n", "\n").splitlines():
        match = LLMS_ENTRY_RE.match(line.strip())
        if not match:
            continue
        canonical = match.group("url")
        documents.append(
            {
                "title": match.group("title"),
                "description": match.group("description"),
                "canonical_md_url": canonical,
                "source_url": canonical[:-3],
                "file_name": local_filename(canonical),
            }
        )
    if not documents:
        raise RuntimeError(f"No documentation entries were found in {LLMS_URL}")
    urls = [item["canonical_md_url"] for item in documents]
    if len(urls) != len(set(urls)):
        raise RuntimeError("Duplicate canonical documentation URLs found in llms.txt")
    return documents


def local_filename(canonical_md_url: str) -> str:
    if not canonical_md_url.startswith(f"{SOURCE_DOMAIN}/") or not canonical_md_url.endswith(".md"):
        raise ValueError(f"Unsupported canonical documentation URL: {canonical_md_url}")
    relative = canonical_md_url[len(SOURCE_DOMAIN) + 1 : -3]
    if not relative or relative.startswith("/") or ".." in relative.split("/"):
        raise ValueError(f"Unsafe documentation path: {canonical_md_url}")
    return relative.replace("/", "-") + ".md"


def _strip_mintlify_ai_navigation_banner(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\n") != "> ## Documentation Index":
        return normalized

    i = 0
    block: list[str] = []
    while i < len(lines) and lines[i].lstrip().startswith(">"):
        block.append(lines[i])
        i += 1

    banner = "".join(block)
    if "llms.txt" not in banner or "discover all available pages" not in banner.lower():
        return normalized

    while i < len(lines) and not lines[i].strip():
        i += 1
    return "".join(lines[i:])


def normalize_markdown(raw_markdown: str, source_url: str) -> str:
    body = _strip_mintlify_ai_navigation_banner(raw_markdown)
    body = body.lstrip("\n")
    if not body.endswith("\n"):
        body += "\n"
    return f"# Source: {source_url}\n\n{body}"


def sha256_text(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def document_metrics(content: str) -> dict[str, int | str]:
    return {
        "local_sha256": sha256_text(content),
        "byte_size": len(content.encode("utf-8")),
        "character_count": len(content),
        "line_count": len(content.splitlines()),
    }


def fetch_upstream_docs_commit(token: str | None = None) -> str:
    raw = _request_text(UPSTREAM_DOCS_COMMITS_API, token=token)
    try:
        payload = json.loads(raw)
        return payload[0]["sha"]
    except (json.JSONDecodeError, IndexError, KeyError, TypeError) as exc:
        raise RuntimeError("Unable to determine latest upstream docs commit") from exc


def fetch_remote_documents(llms_text: str) -> list[RemoteDocument]:
    entries = parse_llms(llms_text)
    documents: list[RemoteDocument] = []
    for entry in entries:
        raw = _request_text(entry["canonical_md_url"])
        documents.append(
            RemoteDocument(
                title=entry["title"],
                description=entry["description"],
                canonical_md_url=entry["canonical_md_url"],
                source_url=entry["source_url"],
                file_name=entry["file_name"],
                content=normalize_markdown(raw, entry["source_url"]),
            )
        )
    return documents


def compute_diff(
    repo_root: Path,
    expected_contents: dict[str, str],
    current_scope: Iterable[str],
) -> dict[str, list[str]]:
    scope = set(current_scope)
    expected = set(expected_contents)
    added = sorted(expected - scope)
    removed = sorted(scope - expected)
    changed: list[str] = []
    for file_name in sorted(expected & scope):
        path = repo_root / file_name
        if not path.is_file() or path.read_text(encoding="utf-8") != expected_contents[file_name]:
            changed.append(file_name)
    return {"changed": changed, "added": added, "removed": removed}


def build_manifest(
    previous: dict,
    documents: list[dict],
    upstream_docs_commit: str,
    capture_date: str | None = None,
) -> dict:
    retrieval_date = capture_date or previous.get("retrieval_date")
    if not retrieval_date:
        retrieval_date = datetime.now(timezone.utc).date().isoformat()

    normalized_documents: list[dict] = []
    for item in documents:
        content = item["content"]
        normalized_documents.append(
            {
                "file_name": item["file_name"],
                "title": item["title"],
                "source_url": item["source_url"],
                "canonical_md_url": item["canonical_md_url"],
                "description": item["description"],
                **document_metrics(content),
            }
        )

    return {
        "repository": previous.get("repository", "agentskills-docs"),
        "mirror_type": "derived_snapshot",
        "retrieval_date": retrieval_date,
        "source_domain": SOURCE_DOMAIN,
        "scope_source": LLMS_URL,
        "upstream_repository": UPSTREAM_REPOSITORY,
        "upstream_docs_commit_at_capture": upstream_docs_commit,
        "upstream_license": previous.get("upstream_license", "Apache-2.0"),
        "extraction_method": "canonical_markdown_normalized",
        "normalization": {
            "source_header_added": True,
            "source_header_format": "# Source: <published page URL>",
            "mintlify_ai_navigation_banner_removed": True,
            "substantive_content_rewritten": False,
        },
        "total_documentation_pages": len(normalized_documents),
        "documents": normalized_documents,
    }


def build_index(documents: list[dict], llms_text: str) -> str:
    lines = [
        "# agentskills.io Documentation Bundle — Index",
        "",
        "Complete verbatim extraction of the agentskills.io documentation domain.",
        "Source of scope: https://agentskills.io/llms.txt (cross-checked against /sitemap.xml and a full internal-link crawl at the original capture).",
        "",
        "| # | Page title | Source URL | Local file |",
        "| --- | --- | --- | --- |",
    ]
    for number, doc in enumerate(documents, start=1):
        lines.append(
            f"| {number} | {doc['title']} | {doc['source_url']} | `{doc['file_name']}` |"
        )
    lines.extend(
        [
            "",
            f"Total: {len(documents)} documentation pages + this index.",
            "",
            "## Notes",
            "",
            "- Each file begins with `# Source: <original URL>`, followed by the page's canonical Markdown content.",
            "- The non-substantive Mintlify `Documentation Index → llms.txt` AI-navigation banner is removed during normalization; no substantive content is rewritten.",
            "- Canonical `.md` endpoints are authoritative for this mirror rather than rendered HTML.",
            "",
            "## Appendix: llms.txt (as served at https://agentskills.io/llms.txt)",
            "",
            "```",
            llms_text.replace("\r\n", "\n").rstrip("\n"),
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def build_readme_catalog(documents: list[dict]) -> str:
    lines = [
        "| Document | Title | Scope & Description | Source URL |",
        "| :--- | :--- | :--- | :--- |",
        "| [`00-index.md`](./00-index.md) | **Documentation Index** | Master index table, extraction methodology notes, and raw upstream `llms.txt`. | [llms.txt](https://agentskills.io/llms.txt) |",
    ]
    for doc in documents:
        source_path = doc["source_url"][len(SOURCE_DOMAIN):] or "/"
        lines.append(
            f"| [`{doc['file_name']}`](./{doc['file_name']}) | **{doc['title']}** | {doc['description']} | [{source_path}]({doc['source_url']}) |"
        )
    return "\n".join(lines)


def update_readme_catalog(readme: str, documents: list[dict]) -> str:
    start_heading = "## Documentation Catalog\n"
    end_heading = "\n---\n\n## Agent & RAG Ingestion Guide"
    if start_heading not in readme or end_heading not in readme:
        raise RuntimeError("README documentation catalog boundaries were not found")
    before, remainder = readme.split(start_heading, 1)
    _, after = remainder.split(end_heading, 1)
    return before + start_heading + "\n" + build_readme_catalog(documents) + "\n" + end_heading + after


def _document_dicts(documents: list[RemoteDocument]) -> list[dict]:
    return [
        {
            "title": doc.title,
            "description": doc.description,
            "canonical_md_url": doc.canonical_md_url,
            "source_url": doc.source_url,
            "file_name": doc.file_name,
            "content": doc.content,
        }
        for doc in documents
    ]


def load_manifest(repo_root: Path) -> dict:
    path = repo_root / "sources.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Unable to read valid manifest: {path}") from exc


def audit(repo_root: Path, token: str | None = None) -> tuple[dict, list[RemoteDocument], str, str]:
    previous = load_manifest(repo_root)
    llms_text = _request_text(LLMS_URL)
    remote_documents = fetch_remote_documents(llms_text)
    upstream_commit = fetch_upstream_docs_commit(token=token)

    expected = {doc.file_name: doc.content for doc in remote_documents}
    current_scope = [
        item["file_name"]
        for item in previous.get("documents", [])
        if isinstance(item, dict) and item.get("file_name")
    ]
    diff = compute_diff(repo_root, expected, current_scope)
    signal_at_capture = previous.get("upstream_docs_commit_at_capture")
    result = {
        "changed": any(diff.values()),
        "published_document_count": len(remote_documents),
        "local_manifest_document_count": len(current_scope),
        "changed_files": diff["changed"],
        "added_files": diff["added"],
        "removed_files": diff["removed"],
        "upstream_docs_commit": upstream_commit,
        "upstream_signal_changed": bool(signal_at_capture and signal_at_capture != upstream_commit),
    }
    return result, remote_documents, llms_text, upstream_commit


def apply_update(
    repo_root: Path,
    previous: dict,
    remote_documents: list[RemoteDocument],
    llms_text: str,
    upstream_commit: str,
    result: dict,
) -> list[str]:
    if os.environ.get("GITHUB_ACTIONS") != "true" or os.environ.get("AGENTSKILLS_SYNC_WRITE") != "1":
        raise RuntimeError("Write mode is allowed only in the controlled GitHub Actions workflow")

    touched: list[str] = []
    by_name = {doc.file_name: doc for doc in remote_documents}

    for file_name in result["changed_files"] + result["added_files"]:
        (repo_root / file_name).write_text(by_name[file_name].content, encoding="utf-8", newline="\n")
        touched.append(file_name)

    for file_name in result["removed_files"]:
        path = repo_root / file_name
        if path.exists():
            path.unlink()
            touched.append(file_name)

    docs = _document_dicts(remote_documents)
    capture_date = datetime.now(timezone.utc).date().isoformat()
    manifest = build_manifest(previous, docs, upstream_commit, capture_date=capture_date)
    (repo_root / "sources.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )
    touched.append("sources.json")

    (repo_root / "00-index.md").write_text(build_index(docs, llms_text), encoding="utf-8", newline="\n")
    touched.append("00-index.md")

    if result["added_files"] or result["removed_files"]:
        readme_path = repo_root / "README.md"
        updated = update_readme_catalog(readme_path.read_text(encoding="utf-8"), docs)
        readme_path.write_text(updated, encoding="utf-8", newline="\n")
        touched.append("README.md")

    return sorted(set(touched))


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Read-only comparison (default)")
    mode.add_argument("--write", action="store_true", help="Apply a verified proposed update in GitHub Actions")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    repo_root = args.repo_root.resolve()
    token = os.environ.get("GITHUB_TOKEN")

    try:
        previous = load_manifest(repo_root)
        result, remote_documents, llms_text, upstream_commit = audit(repo_root, token=token)

        if args.write and result["changed"]:
            result["touched_files"] = apply_update(
                repo_root, previous, remote_documents, llms_text, upstream_commit, result
            )
        elif args.write:
            result["touched_files"] = []

        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            state = "changes detected" if result["changed"] else "mirror current"
            print(f"AgentSkills.io sync check: {state}")
            print(f"Published pages: {result['published_document_count']}")
            if result["changed"]:
                for key in ("changed_files", "added_files", "removed_files"):
                    if result[key]:
                        print(f"{key}: {', '.join(result[key])}")
        return 0
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
