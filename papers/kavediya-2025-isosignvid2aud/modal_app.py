"""Modal entry points for the Kavediya 2025 IsoSignVid2Aud reproduction.

The published scripts run unchanged from /code; this file only writes their
config.yaml with Modal paths and invokes them in the authors' order.
"""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

import modal

ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = ROOT.parent.parent
CODE_COMMIT = "d4777cfdf41a24bc8c22a41c6d075ebc470c60f0"
CODE_SHA256 = "c271bb7d836b2451f1b308e640d28b12f5ec941cb50eda3b1634786575ea85e7"
PYTORCHVIDEO_COMMIT = "f3142bb05cdb56af0704ab6f0adfb0c7bbafe4a0"
PATCHES = [
    "01-train-vocabulary.patch", "02-single-gpu.patch", "03-resume.patch",
    "04-direct-decode.patch", "05-direct-decode-combined.patch",
]

app = modal.App("kavediya-2025-isosignvid2aud")
image = (
    modal.Image.from_dockerfile(REPOSITORY_ROOT / "Dockerfile", context_dir=REPOSITORY_ROOT)
    # pyproject.toml's runtime dependencies at their stated minimums, without
    # replacing the image's torch/torchvision. av is unpinned upstream; PyAV 18.1.0
    # makes pytorchvideo's get_clip get SIGKILLed on some ASL Citizen videos
    # (e.g. 42667478960180394-SIGN LANGUAGE.mp4), 12.3.0 decodes them (README).
    .run_commands(
        "pip install -c /tmp/image-versions.txt av==12.3.0"
        f" git+https://github.com/facebookresearch/pytorchvideo@{PYTORCHVIDEO_COMMIT}"
        " gtts==2.5.4 librosa==0.10.2.post1 opencv-contrib-python==4.11.0.86 pandas==2.2.3"
        " scikit-learn==1.6.1 soundfile==0.13.0 tqdm==4.66.5"
        ' numpy==$(python -c "import numpy; print(numpy.__version__)")'
    )
    .add_local_dir(ROOT / "patches", "/tmp/patches", copy=True)
    .run_commands(
        f"curl -sL -o /tmp/code.tgz https://codeload.github.com/Kugelblitz25/IsoSignVid2Aud/tar.gz/{CODE_COMMIT}"
        f" && echo '{CODE_SHA256}  /tmp/code.tgz' | sha256sum -c -"
        " && mkdir /code && tar xzf /tmp/code.tgz -C /code --strip-components 1"
        " && cd /code && " + " && ".join(f"git apply /tmp/patches/{p}" for p in PATCHES),
        "pip freeze > /code/pip-freeze.txt",
    )
)
datasets = modal.Volume.from_name("datasets", create_if_missing=False)
cache = modal.Volume.from_name("huggingface-cache", create_if_missing=False)
results = modal.Volume.from_name("kavediya-2025-isosignvid2aud-results", create_if_missing=True, version=2)
VOLUMES = {"/datasets": datasets.read_only(), "/cache/huggingface": cache, "/results": results}
# Kinetics weights for pytorchvideo's i3d_r50 come through torch.hub.
ENV = {
    "HF_HOME": "/cache/huggingface",
    "HF_HUB_CACHE": "/cache/huggingface/hub",
    "TORCH_HOME": "/cache/huggingface/torch",
    "PYTHONPATH": "/code",
}


def _config(run: Path, raw: dict[str, str], videos: str, n_words: int, overrides: dict,
            processed: Path | None = None) -> Path:
    """Write the upstream config.yaml with this run's paths and settings."""
    import yaml

    cfg = yaml.safe_load(Path("/code/config.yaml").read_text())
    p = run / "processed"
    cfg["n_words"] = n_words
    cfg["data"]["raw"] = {"videos": videos, "csvs": raw}
    cfg["data"]["processed"] = {
        "videos": str((processed or p) / "videos"),
        "csvs": {s: str(p / f"{s}.csv") for s in ("train", "test", "val")},
        "classlist": str(p / "classes.txt"),
        "specs": str(p / "specs.csv"),
        "vid_features": {s: str(p / f"features_{s}.csv") for s in ("train", "test", "val")},
    }
    for section in ("extractor", "transformer", "generator"):
        cfg[section]["checkpoints"] = str(run / "checkpoints" / section)
    cfg["combined"]["checkpoints"] = str(run / "checkpoints" / "combined")
    for dotted, value in overrides.items():
        *keys, last = dotted.split(".")
        node = cfg
        for key in keys:
            node = node[key]
        node[last] = value
    path = run / "config.yaml"
    path.write_text(yaml.safe_dump(cfg, sort_keys=False))
    return path


def _step(run: Path, script: str, *args: str) -> dict:
    """Run one upstream script from the run directory, so its logs/ land there."""
    import shutil

    start = time.time()
    smi = shutil.which("nvidia-smi") and subprocess.Popen(
        ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits", "-lms", "1000"],
        stdout=subprocess.PIPE, text=True,
    )
    proc = subprocess.run(["python", f"/code/{script}", "--config_file", str(run / "config.yaml"), *args], cwd=run)
    peak = None
    if smi:
        smi.terminate()
        peak = max((int(x) for x in smi.stdout.read().split()), default=0)
    record = {"script": script, "args": list(args), "exit_code": proc.returncode,
              "seconds": round(time.time() - start, 1), "peak_gpu_memory_mib": peak}
    print(json.dumps(record), flush=True)
    results.commit()
    if proc.returncode:
        raise RuntimeError(f"{script} exited {proc.returncode}")
    return record


ASLC = Path("/datasets/asl-citizen")
RUN = Path("/results/aslc1500")
SPLITS = ("train", "val", "test")
N_WORDS = 1500  # paper §IV.A
# Speed only (README "Environment and patches"): the paper used 4 workers; 32 keep an H100 fed.
TRAIN_OVERRIDES = {"extractor.training.num_workers": 32, "combined.num_workers": 32}


def _train_vocabulary() -> list[str]:
    """Train's top-N glosses, chosen by the authors' own create_subset (patch 01 applies it to every split)."""
    import sys

    import pandas as pd

    sys.path.insert(0, "/code")
    from utils.common import create_subset

    return sorted(pd.read_csv(create_subset(ASLC / "splits/train.csv", N_WORDS)).Gloss.unique())


@app.function(image=image, cpu=8, memory=32768, volumes=VOLUMES, env=ENV, timeout=4 * 3600)
def verify_shard(k: int, shards: int) -> dict:
    """verify.py on the glosses assigned to shard k. Sharding by gloss keeps each shard's train
    vocabulary complete, so the union of shards equals one unsharded run."""
    import pandas as pd

    glosses = set(_train_vocabulary()[k::shards])
    shard = RUN / "shards" / f"verify-{k:03d}"
    shard.mkdir(parents=True, exist_ok=True)
    raw = {}
    for split in SPLITS:
        df = pd.read_csv(ASLC / f"splits/{split}.csv")
        raw[split] = str(shard / f"raw_{split}.csv")
        df[df.Gloss.isin(glosses)].to_csv(raw[split], index=False)
    _config(shard, raw, str(ASLC / "videos"), N_WORDS, {})
    _step(shard, "models/extractor/preprocessing/verify.py")
    return {s: len(pd.read_csv(shard / f"processed/{s}.csv")) for s in SPLITS}


@app.function(image=image, cpu=4, memory=16384, volumes=VOLUMES, env=ENV, timeout=3600)
def merge_verify(shards: int) -> dict:
    """Join verified shards in the raw CSV's row order, i.e. the order an unsharded verify.py writes."""
    import pandas as pd

    (RUN / "processed").mkdir(parents=True, exist_ok=True)
    counts = {}
    for split in SPLITS:
        order = {f: i for i, f in enumerate(pd.read_csv(ASLC / f"splits/{split}.csv")["Video file"])}
        df = pd.concat([pd.read_csv(RUN / f"shards/verify-{k:03d}/processed/{split}.csv") for k in range(shards)])
        df = df.iloc[df["Video file"].map(order).argsort()]
        df.to_csv(RUN / f"processed/verified_{split}.csv", index=False)
        counts[split] = len(df)
    results.commit()
    return counts


@app.function(image=image, cpu=8, memory=65536, volumes=VOLUMES, env=ENV, timeout=6 * 3600,
              retries=modal.Retries(max_retries=2, initial_delay=10.0))
def augment_shard(k: int, shards: int) -> dict:
    """augmentation.py on contiguous chunk k of every verified split, writing into the shared video directory.
    Idempotent: a finished shard (done.json) is skipped; a retried one starts again from its verified chunk."""
    import pandas as pd

    shard = RUN / "shards" / f"augment-{k:03d}"
    if (shard / "done.json").exists():
        return json.loads((shard / "done.json").read_text())
    (shard / "processed").mkdir(parents=True, exist_ok=True)
    for split in SPLITS:
        df = pd.read_csv(RUN / f"processed/verified_{split}.csv")
        size = -(-len(df) // shards)
        df.iloc[k * size:(k + 1) * size].to_csv(shard / f"processed/{split}.csv", index=False)
    # Shard CSVs stay in the shard; videos go to the run's shared directory.
    _config(shard, {s: "" for s in SPLITS}, str(ASLC / "videos"), N_WORDS, {}, processed=RUN / "processed")
    _step(shard, "models/extractor/preprocessing/augmentation.py")
    counts = {s: len(pd.read_csv(shard / f"processed/{s}.csv")) for s in SPLITS}
    (shard / "done.json").write_text(json.dumps(counts))
    results.commit()
    return counts


@app.function(image=image, cpu=4, memory=16384, volumes=VOLUMES, env=ENV, timeout=3600)
def merge_augment(shards: int) -> dict:
    """Concatenate augmented chunks in chunk order, i.e. the CSV an unsharded augmentation.py writes."""
    import pandas as pd

    counts = {}
    for split in SPLITS:
        df = pd.concat([pd.read_csv(RUN / f"shards/augment-{k:03d}/processed/{split}.csv") for k in range(shards)])
        df.to_csv(RUN / f"processed/{split}.csv", index=False)
        counts[split] = len(df)
    results.commit()
    return counts


@app.function(image=image, cpu=1, memory=4096, volumes=VOLUMES, env=ENV, timeout=12 * 3600)
def prepare_aslc_remote(verify_shards: int, augment_shards: int) -> dict:
    """Steps 2-3 of trainer.sh (verify, augment) for ASL-Citizen-1500, sharded across CPU containers."""
    out = {}
    if not all((RUN / f"processed/verified_{s}.csv").exists() for s in SPLITS):
        out["verify_shards"] = list(verify_shard.starmap((k, verify_shards) for k in range(verify_shards)))
        out["verified"] = merge_verify.remote(verify_shards)
    else:
        import pandas as pd

        out["verified"] = {s: len(pd.read_csv(RUN / f"processed/verified_{s}.csv")) for s in SPLITS}
    print(json.dumps(out), flush=True)
    for round_ in range(3):
        todo = [k for k in range(augment_shards) if not (RUN / f"shards/augment-{k:03d}/done.json").exists()]
        if not todo:
            break
        failed = [r for r in augment_shard.starmap(((k, augment_shards) for k in todo), return_exceptions=True)
                  if isinstance(r, Exception)]
        print(json.dumps({"round": round_, "shards": len(todo), "failed": len(failed),
                          "errors": sorted({repr(e)[:200] for e in failed})}), flush=True)
        results.reload()
    missing = [k for k in range(augment_shards) if not (RUN / f"shards/augment-{k:03d}/done.json").exists()]
    if missing:
        raise RuntimeError(f"augmentation shards unfinished after 3 rounds: {missing}")
    out["augment_shards"] = [json.loads((RUN / f"shards/augment-{k:03d}/done.json").read_text()) for k in range(augment_shards)]
    out["augmented"] = merge_augment.remote(augment_shards)
    (RUN / "prepare.json").write_text(json.dumps(out, indent=2))
    results.commit()
    print(json.dumps({"verified": out["verified"], "augmented": out["augmented"]}), flush=True)
    return out


@app.local_entrypoint()
def prepare_aslc(verify_shards: int = 32, augment_shards: int = 96) -> None:
    prepare_aslc_remote.remote(verify_shards, augment_shards)


def _write_train_config(run: Path, overrides: dict) -> None:
    _config(run, {s: str(ASLC / f"splits/{s}.csv") for s in SPLITS}, str(ASLC / "videos"), N_WORDS,
            {**TRAIN_OVERRIDES, **overrides}, processed=RUN / "processed")
    import yaml

    cfg = yaml.safe_load((run / "config.yaml").read_text())
    cfg["data"]["processed"]["csvs"] = {s: str(RUN / f"processed/{s}.csv") for s in SPLITS}
    cfg["data"]["processed"]["specs"] = str(RUN / "processed/specs.csv")
    (run / "config.yaml").write_text(yaml.safe_dump(cfg, sort_keys=False))


SEGMENT_SECONDS = 23 * 3600  # Modal's 24 h function limit, less a margin
STAGE = Path("/stage/videos")  # container-local copy of the clips (speed only; README)


def _stage(splits: tuple[str, ...]) -> dict:
    """Copy the augmented clips of the given splits from the Volume to local disk (64 threads)."""
    import shutil
    from concurrent.futures import ThreadPoolExecutor

    import pandas as pd

    STAGE.mkdir(parents=True, exist_ok=True)
    files = sorted({f for s in splits for f in pd.read_csv(RUN / f"processed/{s}.csv")["Video file"]})
    start = time.time()
    with ThreadPoolExecutor(64) as ex:
        list(ex.map(lambda f: (STAGE / f).exists() or shutil.copyfile(RUN / "processed/videos" / f, STAGE / f), files))
    return {"staged_files": len(files), "stage_seconds": round(time.time() - start, 1)}


def _train_segment(run: Path, script: str, resume: Path, log: Path) -> dict:
    """Run one training script until it exits, or stop it at an epoch boundary (after resume.pt
    is rewritten) when another epoch would not fit in this segment."""
    import shutil

    start = time.time()
    smi = shutil.which("nvidia-smi") and subprocess.Popen(
        ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits", "-lms", "5000"],
        stdout=subprocess.PIPE, text=True,
    )
    proc = subprocess.Popen(["python", f"/code/{script}", "--config_file", str(run / "config.yaml")], cwd=run)
    epoch_ends, stopped = [], False
    seen = log.read_text().count("Train Loss") if log.exists() else 0
    while proc.poll() is None:
        time.sleep(30)
        done = log.read_text().count("Train Loss") if log.exists() else 0
        if done > seen:
            seen = done
            epoch_ends.append(time.time())
            results.commit()
            span = epoch_ends[-1] - (epoch_ends[-2] if len(epoch_ends) > 1 else start)
            if time.time() - start + 1.15 * span > SEGMENT_SECONDS:
                mark = epoch_ends[-1]
                while proc.poll() is None and (not resume.exists() or resume.stat().st_mtime < mark - 60):
                    time.sleep(10)
                if proc.poll() is None:
                    proc.terminate()
                    proc.wait()
                    stopped = True
    peak = None
    if smi:
        smi.terminate()
        peak = max((int(x) for x in smi.stdout.read().split()), default=0)
    results.commit()
    return {"script": script, "exit_code": proc.returncode, "stopped_for_next_segment": stopped,
            "seconds": round(time.time() - start, 1), "epochs_this_segment": len(epoch_ends),
            "peak_gpu_memory_mib": peak}


@app.function(image=image, gpu="H100", cpu=64, memory=262144, volumes=VOLUMES, env=ENV, ephemeral_disk=600 * 1024, timeout=24 * 3600)
def train_extractor(name: str, segment: int = 1, overrides: dict | None = None) -> dict:
    """models/extractor/train.py in <=23 h segments; each segment resumes from resume.pt."""
    import yaml

    run = RUN / name
    run.mkdir(parents=True, exist_ok=True)
    if segment == 1:
        _write_train_config(run, overrides or {})
    staged = _stage(("train", "val"))
    cfg = yaml.safe_load((run / "config.yaml").read_text())
    cfg["data"]["processed"]["videos"] = str(STAGE)
    (run / "config.yaml").write_text(yaml.safe_dump(cfg, sort_keys=False))
    record = _train_segment(run, "models/extractor/train.py", run / "checkpoints/extractor/resume.pt",
                            run / "logs/extractor_training.log")
    record["segment"] = segment
    record.update(staged)
    with (run / "segments.jsonl").open("a") as f:
        f.write(json.dumps(record) + "\n")
    results.commit()
    print(json.dumps(record), flush=True)
    return record


@app.function(image=image, cpu=4, memory=32768, volumes=VOLUMES, env=ENV, timeout=6 * 3600)
def spec_gen() -> dict:
    """Step 1 of trainer.sh: gTTS spectrograms for train's top-N glosses (network: Google TTS)."""
    run = RUN / "specgen"
    run.mkdir(parents=True, exist_ok=True)
    _write_train_config(run, {})
    record = _step(run, "models/generator/preprocessing/spec_gen.py")
    import pandas as pd

    record["glosses"] = len(pd.read_csv(RUN / "processed/specs.csv", usecols=["Gloss"]))
    return record


@app.function(image=image, gpu="H100", cpu=64, memory=262144, volumes=VOLUMES, env=ENV, ephemeral_disk=600 * 1024, timeout=24 * 3600)
def train_combined(name: str, segment: int = 1, overrides: dict | None = None) -> dict:
    """models/train.py (joint extractor + spectrogram generator) in <=23 h resumable segments."""
    import yaml

    run = RUN / name
    run.mkdir(parents=True, exist_ok=True)
    if segment == 1:
        _write_train_config(run, overrides or {})
    staged = _stage(("train", "val"))
    cfg = yaml.safe_load((run / "config.yaml").read_text())
    cfg["data"]["processed"]["videos"] = str(STAGE)
    (run / "config.yaml").write_text(yaml.safe_dump(cfg, sort_keys=False))
    record = _train_segment(run, "models/train.py", run / "checkpoints/combined/resume.pt",
                            run / "logs/combined_training.log")
    record["segment"] = segment
    record.update(staged)
    with (run / "segments.jsonl").open("a") as f:
        f.write(json.dumps(record) + "\n")
    results.commit()
    print(json.dumps(record), flush=True)
    return record


@app.function(image=image, gpu="H100", cpu=64, memory=262144, volumes=VOLUMES, env=ENV, ephemeral_disk=600 * 1024, timeout=12 * 3600)
def test_extractor(name: str, weights: str = "checkpoints/extractor/full_best_i3d.pt") -> dict:
    """models/extractor/test.py on the best (lowest validation loss) checkpoint."""
    import yaml

    run = RUN / name
    staged = _stage(("test",))
    cfg = yaml.safe_load((run / "config.yaml").read_text())
    cfg["data"]["processed"]["videos"] = str(STAGE)
    (run / "config.yaml").write_text(yaml.safe_dump(cfg, sort_keys=False))
    record = _step(run, "models/extractor/test.py", "--model_weights", str(run / weights),
                   "--output_path", str(run / "test_results"))
    record.update(staged)
    import pandas as pd

    record["summary"] = pd.read_csv(run / "test_results/test_results_summary.csv").to_dict("records")
    return record


@app.function(image=image, gpu="H100", cpu=64, memory=262144, volumes=VOLUMES, env=ENV, timeout=3600)
def preflight_resume() -> dict:
    """Patch 03 on the preflight sample: 1 epoch, then the same run directory with epochs=2."""
    import torch
    import yaml

    pre = Path("/results/preflight-aslc")
    run = pre / "resume-test"
    run.mkdir(parents=True, exist_ok=True)
    cfg = yaml.safe_load((pre / "config.yaml").read_text())
    cfg["extractor"]["checkpoints"] = str(run / "checkpoints/extractor")
    cfg["extractor"]["training"]["num_workers"] = 32
    out = {}
    for epochs in (1, 2):
        cfg["extractor"]["training"]["epochs"] = epochs
        (run / "config.yaml").write_text(yaml.safe_dump(cfg, sort_keys=False))
        out[f"epochs={epochs}"] = _step(run, "models/extractor/train.py")
        state = torch.load(run / "checkpoints/extractor/resume.pt", weights_only=False, map_location="cpu")
        out[f"epochs={epochs}"]["resume_epoch"] = state["epoch"]
        out[f"epochs={epochs}"]["lr"] = state["optimizers"][0]["param_groups"][0]["lr"]
        out[f"epochs={epochs}"]["early_stopping"] = {k: v for k, v in state["early_stopping"].items() if k != "verbose"}
    out["log_resumed"] = [l for l in (run / "logs/extractor_training.log").read_text().splitlines() if "Resumed" in l or "Train Loss" in l]
    return out


@app.local_entrypoint()
def resume_check() -> None:
    print(json.dumps(preflight_resume.remote(), default=str))


@app.function(image=image, cpu=4, memory=16384, volumes=VOLUMES, env=ENV, timeout=3600)
def identity_chunk(paths: list[str], full_duration: bool) -> list[str]:
    """Paths where patches 04/05 differ from pytorchvideo after the full transform.
    full_duration=False: WLASLDataset's get_clip(0, clip_duration); True: S2S_Dataset's get_clip(0, duration)."""
    import torch
    from pytorchvideo.data.encoded_video import EncodedVideo

    from models.extractor import dataset as D

    bad = []
    for path in paths:
        def original():
            v = EncodedVideo.from_path(path)
            return D.transform(v.get_clip(start_sec=0, end_sec=v.duration if full_duration else D.clip_duration))["video"]

        out = []
        for fn in (original, lambda: D.transform({"video": D.decode_clip(path, None if full_duration else D.clip_duration)})["video"]):
            try:
                out.append(fn())
            except Exception as e:
                out.append(type(e).__name__)
        ref, new = out
        if not (ref == new if isinstance(ref, str) or isinstance(new, str) else torch.equal(ref, new)):
            bad.append(path)
    return bad


@app.function(image=image, cpu=2, memory=8192, volumes=VOLUMES, env=ENV, timeout=3600)
def verify_decode_identity(n: int = 1000) -> dict:
    """Patch 04 and 05 on n random augmented ASL-Citizen-1500 clips (and patch 04 on n raw videos)."""
    import random

    import pandas as pd

    random.seed(0)
    aug = [str(RUN / "processed/videos" / f) for f in
           random.sample([f for s in SPLITS for f in pd.read_csv(RUN / f"processed/{s}.csv")["Video file"]], n)]
    raw = [str(ASLC / "videos" / f) for f in
           random.sample([f for s in SPLITS for f in pd.read_csv(RUN / f"processed/verified_{s}.csv")["Video file"]], n)]
    out = {}
    for label, paths, full in (("patch05_augmented", aug, True), ("patch04_augmented", aug, False), ("patch04_raw", raw, False)):
        bad = [p for r in identity_chunk.starmap((paths[i:i + 50], full) for i in range(0, len(paths), 50)) for p in r]
        out[label] = {"checked": len(paths), "mismatches": len(bad), "examples": bad[:5]}
    (RUN / "decode_identity.json").write_text(json.dumps(out, indent=2))
    results.commit()
    return out


@app.local_entrypoint()
def run_table1(row: str, max_segments: int = 3, start_segment: int = 1) -> None:
    """Train one Table I row in resumable <=23 h segments, then test its best checkpoint.
    row: "standalone" (IsoSignVid2Aud) or "combined" (combined training)."""
    train = {"standalone": train_extractor, "combined": train_combined}[row]
    weights = {"standalone": "checkpoints/extractor/full_best_i3d.pt",
               "combined": "checkpoints/combined/extractor_best.pt"}[row]
    for segment in range(start_segment, max_segments + 1):
        record = train.remote(row, segment)
        if not record["stopped_for_next_segment"]:
            break
    if record["exit_code"] == 0 and not record["stopped_for_next_segment"]:
        print(json.dumps(test_extractor.remote(row, weights), default=str))


@app.function(image=image, cpu=2, memory=4096, volumes=VOLUMES, env=ENV, timeout=1800)
def file_sha256(path: str) -> dict:
    import hashlib

    h, n = hashlib.sha256(), 0
    with open(path, "rb") as f:
        while chunk := f.read(1 << 24):
            h.update(chunk)
            n += len(chunk)
    return {"path": path, "sha256": h.hexdigest(), "size_bytes": n}


@app.local_entrypoint()
def sha256(path: str) -> None:
    print(json.dumps(file_sha256.remote(path)))
