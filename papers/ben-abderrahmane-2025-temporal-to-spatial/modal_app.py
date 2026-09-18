"""Modal entry points for the Ben-Abderrahmane 2025 ArSL ResNet reproduction."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
import urllib.request
from pathlib import Path

import modal


PAPER_ID = "8b224ecbd42da766efba45d17b34b3a1255c2345"
DATASET_SLUG = "arab-sign"
RGB_DIR = Path("/datasets") / DATASET_SLUG / "RGB"
SOURCE_FOLDER = "https://drive.google.com/drive/folders/1twRzL8fqjbq5dp6jV-V00-O8gD1BZMTN"
# Drive file ids with the exact byte sizes read from Content-Range on 2026-09-18.
# The paper's ArabSign row "Total Size 18 GB" matches this modality alone.
RGB_ARCHIVES = {
    "01.7z": ("1jsjy4Fe9BffXxarBEFtTCGedRaVinJVt", 3471839354),
    "02.7z": ("1la1ePLMd8dxNDORvYaqOX3Y9jf8HMNot", 3465471202),
    "03.7z": ("1tqc_tFjWlVHqooir-69zJaj2v4UAMaiA", 3173623708),
    "04.7z": ("1Ge6N4LMRbCaTD5gBZXqdwQHxD3PdKlcU", 3164859125),
    "05.7z": ("15OHkXbJu0lyBQtP_9XD1ToMNW9Ixeplz", 3272313079),
    "06.7z": ("1D9q7yBFTgGdTLYV3NGjBL0acAvENjvLx", 3074093776),
}

app = modal.App("repro-ben-abderrahmane-2025")
# A download and archive-inspection job needs no GPU base image.
image = modal.Image.debian_slim(python_version="3.12").apt_install("p7zip-full")
datasets = modal.Volume.from_name("datasets", create_if_missing=False)
cache = modal.Volume.from_name("huggingface-cache", create_if_missing=False)


def _download(file_id: str, destination: Path) -> str:
    """Stream one public Drive file to destination, returning its SHA-256."""
    url = f"https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t"
    partial = destination.with_suffix(destination.suffix + ".part")
    digest = hashlib.sha256()
    with urllib.request.urlopen(url) as response:
        if response.status != 200:
            raise RuntimeError(f"{destination.name}: HTTP {response.status}")
        with partial.open("wb") as handle:
            while chunk := response.read(8 * 1024 * 1024):
                digest.update(chunk)
                handle.write(chunk)
    partial.rename(destination)
    return digest.hexdigest()


def _mp4_count(archive: Path) -> int:
    """Count .mp4 entries from the archive listing without extracting."""
    listing = subprocess.run(
        ["7z", "l", "-ba", str(archive)],
        check=True, capture_output=True, text=True,
    ).stdout
    return sum(1 for line in listing.splitlines() if line.rstrip().endswith(".mp4"))


@app.function(
    image=image,
    volumes={"/datasets": datasets, "/cache/huggingface": cache},
    cpu=4,
    memory=8192,
    timeout=6 * 60 * 60,
    env={"HF_HOME": "/cache/huggingface", "HF_HUB_CACHE": "/cache/huggingface/hub"},
)
def populate_arabsign_rgb() -> dict[str, object]:
    """Idempotently add the six ArabSign RGB signer archives to the shared Volume.

    An earlier transfer populated Skeleton in full, Depth partially, and RGB with
    only its two text files. The paper runs MediaPipe pose over colour frames, so
    RGB is the modality the reproduction needs.
    """
    RGB_DIR.mkdir(parents=True, exist_ok=True)
    files, skipped = {}, []

    for name, (file_id, expected_size) in sorted(RGB_ARCHIVES.items()):
        target = RGB_DIR / name
        if target.exists() and target.stat().st_size == expected_size:
            skipped.append(name)
            sha256 = hashlib.sha256(target.read_bytes()).hexdigest()
        else:
            if target.exists():
                raise RuntimeError(
                    f"{name}: refusing to overwrite an existing file of "
                    f"{target.stat().st_size} bytes, expected {expected_size}"
                )
            sha256 = _download(file_id, target)
            actual = target.stat().st_size
            if actual != expected_size:
                target.unlink()
                raise RuntimeError(f"{name}: got {actual} bytes, expected {expected_size}")
            datasets.commit()

        files[name] = {
            "drive_file_id": file_id,
            "size": expected_size,
            "sha256": sha256,
            "mp4_count": _mp4_count(target),
        }

    record = {
        "source_url": SOURCE_FOLDER,
        "source_folder": "ArabSign/RGB",
        "destination": f"{DATASET_SLUG}/RGB",
        "paper_id": PAPER_ID,
        "transferred_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "modal_function_call_id": modal.current_function_call_id(),
        "permission_basis": (
            "Public download links published on the official ArabSign project page "
            "https://hamzah-luqman.github.io/ArabSign/. Licence recorded by the REPRO-SIGN "
            "dataset record as non-commercial only; the archives carry a citation request "
            "and no licence text. Transfer requested by the assignee on 2026-09-18."
        ),
        "scope": (
            "Preserve supplied files only. Verified by exact byte size against Content-Range, "
            "SHA-256 of the received bytes, and a 7z listing that parses the archive footer. "
            "No full archive extraction test was run. No redistribution, dataset identity, "
            "split, or training-readiness claim."
        ),
        "files": files,
        "skipped_already_present": skipped,
        "total_bytes": sum(entry["size"] for entry in files.values()),
        "total_mp4_count": sum(entry["mp4_count"] for entry in files.values()),
    }

    import_id = hashlib.sha256(f"{SOURCE_FOLDER}/RGB".encode()).hexdigest()[:16]
    import_dir = Path("/datasets") / DATASET_SLUG / "_drive_imports" / import_id
    import_dir.mkdir(parents=True, exist_ok=True)
    (import_dir / "manifest.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    datasets.commit()
    return record


def _missing_vs_skeleton(videos: list[tuple[str, str]]) -> dict[str, object]:
    """Name the RGB entries absent relative to the complete Skeleton modality."""
    def key(path: str) -> str:
        # RGB entries end "_c.mp4", Skeleton entries "_c_s.mat"; compare on the shared stem.
        head, _, stem = path.rpartition("/")
        stem = stem.rsplit(".", 1)[0]
        if stem.endswith("_s"):
            stem = stem[:-2]
        return f"{head}/{stem}"

    rgb = {key(path) for _, path in videos}
    skeleton, samples = set(), []
    for archive in sorted((Path("/datasets") / DATASET_SLUG / "Skeleton").glob("*.7z")):
        for path in _entries(archive):
            skeleton.add(key(path))
            if len(samples) < 3:
                samples.append(path)
    return {
        "skeleton_path_samples": samples,
        "rgb_keys": len(rgb),
        "skeleton_keys": len(skeleton),
        "missing_from_rgb": sorted(skeleton - rgb),
        "extra_in_rgb": sorted(rgb - skeleton)[:10],
        "missing_count": len(skeleton - rgb),
    }


def _component_tally(videos: list[tuple[str, str]]) -> dict[str, dict[str, int]]:
    """Tally the second path component per archive, e.g. a train/test directory level."""
    tally: dict[str, dict[str, int]] = {}
    for archive, path in videos:
        parts = path.split("/")
        key = parts[1] if len(parts) > 1 else "(flat)"
        tally.setdefault(key, {})[archive] = tally.setdefault(key, {}).get(archive, 0) + 1
    return tally


def _entries(archive: Path) -> list[str]:
    """Return non-directory entry paths from an archive listing."""
    listing = subprocess.run(
        ["7z", "l", "-ba", "-slt", str(archive)],
        check=True, capture_output=True, text=True,
    ).stdout
    paths, current = [], None
    for line in listing.splitlines():
        if line.startswith("Path = "):
            current = line[len("Path = "):]
        elif line.startswith("Attributes = ") and current is not None:
            if "D" not in line[len("Attributes = "):].split("_")[0]:
                paths.append(current)
            current = None
    return paths


@app.function(
    image=image,
    volumes={"/datasets": datasets.read_only(), "/cache/huggingface": cache},
    cpu=4,
    memory=8192,
    timeout=60 * 60,
    env={"HF_HOME": "/cache/huggingface", "HF_HUB_CACHE": "/cache/huggingface/hub"},
)
def verify_arabsign_rgb() -> dict[str, object]:
    """Read-only audit of the RGB archives: counts, naming scheme, label files."""
    extensions: dict[str, int] = {}
    per_archive: dict[str, object] = {}
    samples: list[str] = []
    all_videos: list[tuple[str, str]] = []  # (archive, path)

    for name in sorted(RGB_ARCHIVES):
        paths = _entries(RGB_DIR / name)
        videos = []
        for path in paths:
            suffix = Path(path).suffix.lower() or "(none)"
            extensions[suffix] = extensions.get(suffix, 0) + 1
            if suffix == ".mp4":
                videos.append(path)
        samples.extend(sorted(paths)[:3])
        all_videos.extend((name, p) for p in videos)
        per_archive[name] = {"entries": len(paths), "videos": len(videos)}

    # Sentence id is expected somewhere in the path as a zero-padded 1..50.
    import re
    per_sentence: dict[str, dict[str, int]] = {}
    unparsed: list[str] = []
    for archive, path in all_videos:
        found = [m for m in re.findall(r"(?<!\d)(\d{4})(?!\d)", path) if 1 <= int(m) <= 50]
        if not found:
            unparsed.append(f"{archive}:{path}")
            continue
        per_sentence.setdefault(found[-1], {})[archive] = (
            per_sentence.setdefault(found[-1], {}).get(archive, 0) + 1
        )

    signers = sorted(RGB_ARCHIVES)
    coverage = {
        sid: {"total": sum(counts.values()),
              "per_signer": {s: counts.get(s, 0) for s in signers}}
        for sid, counts in sorted(per_sentence.items())
    }
    totals = [v["total"] for v in coverage.values()]
    thin = {sid: v for sid, v in coverage.items()
            if v["total"] != max(totals, default=0) and min(v["per_signer"].values()) < 31}

    # Cross-check the claimed 9,335 against the other modalities already on the Volume.
    other_modalities: dict[str, object] = {}
    for modality in ("Skeleton", "Depth"):
        directory = Path("/datasets") / DATASET_SLUG / modality
        archives = sorted(p for p in directory.glob("*.7z"))
        counts, per_ext = {}, {}
        for archive in archives:
            paths = _entries(archive)
            for path in paths:
                suffix = Path(path).suffix.lower() or "(none)"
                per_ext[suffix] = per_ext.get(suffix, 0) + 1
            counts[archive.name] = len(paths)
        other_modalities[modality] = {
            "archives_present": [a.name for a in archives],
            "entries_per_archive": counts,
            "total_entries": sum(counts.values()),
            "extensions": dict(sorted(per_ext.items())),
        }

    labels = {}
    for modality in ("RGB", "Depth", "Skeleton"):
        candidate = Path("/datasets") / DATASET_SLUG / modality / "ArabSignGroundTruth.txt"
        if candidate.exists():
            raw = candidate.read_bytes()
            labels[modality] = {"size": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}

    return {
        "per_archive": per_archive,
        "total_videos": len(all_videos),
        "extensions": dict(sorted(extensions.items())),
        "path_samples": samples[:18],
        "sentence_ids_seen": len(coverage),
        "unparsed_paths": unparsed[:20],
        "unparsed_count": len(unparsed),
        "sentences_below_full_count": thin,
        "label_files": labels,
        "other_modalities": other_modalities,
        "path_component_2": _component_tally(all_videos),
        "rgb_missing_vs_skeleton": _missing_vs_skeleton(all_videos),
    }


@app.local_entrypoint()
def main() -> None:
    print(json.dumps(populate_arabsign_rgb.remote(), indent=2, sort_keys=True))


@app.local_entrypoint()
def verify() -> None:
    print(json.dumps(verify_arabsign_rgb.remote(), indent=2, sort_keys=True))
