"""
Phase 2 rebuild — Step 00: download real public datasets.

This script is intentionally deterministic and idempotent:
- it skips any file that already exists at the target path,
- it verifies SHA256 after download (if a known checksum is registered),
- it writes a JSON manifest of (url, path, size_bytes, sha256, downloaded_at).

NO data transformation happens here. Real raw bytes only.

Run from the repository root:
    python phase2_rebuild/scripts/00_download_datasets.py

Network access is required. If a source is unreachable, the script records the
failure in the manifest under "errors" and exits non-zero so CI can flag it.
The script will NEVER substitute a synthetic file for a missing real one.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
import urllib.request
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "phase2_rebuild" / "data" / "raw"
MANIFEST_PATH = REPO_ROOT / "phase2_rebuild" / "data" / "download_manifest.json"

USER_AGENT = "DataFlowAI-Phase2-Rebuild/1.0 (academic research; contact: berlin.ma@vit.ac.in)"


@dataclass
class Source:
    dataset_id: str
    url: str
    rel_path: str  # under RAW_DIR
    expected_sha256: Optional[str] = None  # fill in after first verified download
    fallback_urls: tuple[str, ...] = ()
    # Allowed leading bytes; rejects HTML error pages masquerading as data.
    # Default = ZIP magic (PK\x03\x04). Override per-source for CSV / other.
    expected_magic: tuple[bytes, ...] = (b"PK\x03\x04",)


SOURCES: list[Source] = [
    Source(
        dataset_id="D1_sec_edgar_2024q4",
        url="https://www.sec.gov/files/dera/data/financial-statement-data-sets/2024q4.zip",
        rel_path="sec_edgar/2024q4.zip",
        expected_sha256=None,
    ),
    Source(
        dataset_id="D2_nyc_payroll",
        url="https://data.cityofnewyork.us/api/views/k397-673e/rows.csv?accessType=DOWNLOAD",
        rel_path="nyc_payroll/citywide_payroll.csv",
        expected_sha256=None,
        expected_magic=(b",", b"\"", b"F"),  # CSV starts with header text
    ),
    Source(
        dataset_id="D3_uci_credit_default",
        url="https://archive.ics.uci.edu/static/public/350/default+of+credit+card+clients.zip",
        rel_path="uci_credit_default/default_of_credit_card_clients.zip",
        expected_sha256=None,
    ),
]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as resp, dest.open("wb") as out:
        while True:
            chunk = resp.read(1 << 20)
            if not chunk:
                break
            out.write(chunk)


def main() -> int:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    manifest: dict = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "user_agent": USER_AGENT,
        "entries": [],
        "errors": [],
    }

    exit_code = 0
    for src in SOURCES:
        dest = RAW_DIR / src.rel_path
        attempted = []
        ok = False
        last_err: Optional[str] = None

        def _valid_magic(p: Path) -> bool:
            with p.open("rb") as f:
                head = f.read(8)
            # CSV: accept any printable ASCII leading byte that is not '<' (HTML).
            if src.expected_magic == (b",", b"\"", b"F"):
                return len(head) > 0 and head[:1] != b"<"
            return any(head.startswith(m) for m in src.expected_magic)

        if dest.exists() and dest.stat().st_size > 0:
            print(f"[skip] {src.dataset_id}: already at {dest}")
            ok = True
        else:
            for url in (src.url, *src.fallback_urls):
                attempted.append(url)
                try:
                    print(f"[get ] {src.dataset_id}: {url}")
                    _download(url, dest)
                    if not _valid_magic(dest):
                        last_err = "magic_byte_mismatch (likely HTML error page returned)"
                        print(f"[fail] {src.dataset_id}: {last_err}", file=sys.stderr)
                        dest.unlink(missing_ok=True)
                        continue
                    ok = True
                    break
                except Exception as e:  # noqa: BLE001 — network errors are heterogeneous
                    last_err = f"{type(e).__name__}: {e}"
                    print(f"[fail] {src.dataset_id}: {last_err}", file=sys.stderr)
                    if dest.exists():
                        dest.unlink(missing_ok=True)

        entry: dict = {
            "dataset_id": src.dataset_id,
            "rel_path": src.rel_path,
            "urls_attempted": attempted or [src.url],
            "ok": ok,
        }
        if ok:
            entry["size_bytes"] = dest.stat().st_size
            entry["sha256"] = _sha256(dest)
            if src.expected_sha256 and entry["sha256"] != src.expected_sha256:
                entry["checksum_mismatch"] = True
                manifest["errors"].append(
                    {
                        "dataset_id": src.dataset_id,
                        "reason": "sha256_mismatch",
                        "expected": src.expected_sha256,
                        "actual": entry["sha256"],
                    }
                )
                exit_code = 2
            print(
                f"[ok  ] {src.dataset_id}: {entry['size_bytes']:,} bytes, sha256={entry['sha256']}"
            )
        else:
            manifest["errors"].append(
                {"dataset_id": src.dataset_id, "reason": "download_failed", "detail": last_err}
            )
            exit_code = 1
        manifest["entries"].append(entry)

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\nManifest written to {MANIFEST_PATH}")
    print(f"Exit code: {exit_code}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
