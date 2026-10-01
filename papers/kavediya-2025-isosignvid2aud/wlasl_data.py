# Idempotently add missing WLASL v0.3 videos to /datasets/WLASL (shared Modal Volume `datasets`).
#
#   .agents/skills/reproduce-paper/scripts/modal_repro_sign.sh run papers/kavediya-2025-isosignvid2aud/wlasl_data.py
#
# Follows the copy's own video_downloader.py: plain public HTTP GET (same User-Agent) for
# non-YouTube URLs, default yt-dlp for YouTube, files named generate_name_from_url(url)+ext
# under videos/. Add-only: existing files are never touched. Then backs up index.csv once
# (index.2026-07-09.csv), regenerates it with the volume's own create_index.py, and writes
# provenance-<date>.json + attempts-<date>.jsonl next to it.
# Deliberately not done: aslpro.com (skipped upstream, site gone), cookies/logins/proxies,
# alternative URLs. The only URL change: https://aslsignbank.haskins.yale.edu serves a
# certificate for aslsignbank.com only, so the identical public path is fetched over http://
# (spot-checked byte-identical to two files already in the copy).
import collections, datetime, hashlib, json, os, random, re, shutil, subprocess, sys, time, urllib.error, urllib.request
import modal

ROOT = "/datasets/WLASL"
YTDLP = "2026.8.19"
image = modal.Image.debian_slim(python_version="3.12").apt_install("ffmpeg").pip_install(f"yt-dlp=={YTDLP}", "tqdm==4.67.1")
vol = modal.Volume.from_name("datasets")
app = modal.App("wlasl-populate", image=image, volumes={"/datasets": vol})
UA = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'  # video_downloader.py


def name(url):  # == generate_name_from_url in create_index.py / video_downloader.py
    return re.sub(r'_+', '_', re.sub(r'[^A-Za-z0-9._-]', '_', url)).strip('_')


def is_video(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=codec_type", "-of", "csv=p=0", path], capture_output=True, text=True)
    return r.stdout.strip() == "video"


def fetch(url):
    """Download url into /tmp/dl; return (path or None, reason)."""
    shutil.rmtree("/tmp/dl", ignore_errors=True); os.makedirs("/tmp/dl")
    base = name(url)
    for attempt in range(3):
        if 'youtube' in url or 'youtu.be' in url:
            r = subprocess.run(["yt-dlp", "--no-playlist", "-o", f"/tmp/dl/{base}.%(ext)s", url], capture_output=True, text=True, timeout=900)
            if r.returncode == 0:
                out = [f for f in os.listdir("/tmp/dl") if not f.endswith(".part")]
                return (f"/tmp/dl/{out[0]}", "ok") if len(out) == 1 else (None, f"yt-dlp output {out}")
            err = ([l for l in r.stderr.splitlines() if "ERROR" in l] or r.stderr.splitlines() or ["?"])[-1][:300]
            if "confirm you" in err or "429" in err:
                return None, "BOTCHECK " + err
            if not any(s in err for s in ("timed out", "Connection", "HTTP Error 5")):
                return None, err
        else:
            fetch_url = url.replace("https://aslsignbank.haskins.yale.edu/", "http://aslsignbank.haskins.yale.edu/")
            try:
                data = urllib.request.urlopen(urllib.request.Request(fetch_url, headers={'User-Agent': UA}), timeout=60).read()
                path = f"/tmp/dl/{base}.mp4"
                open(path, "wb").write(data)
                return (path, "ok") if is_video(path) else (None, f"not a video ({len(data)}B)")
            except urllib.error.HTTPError as e:
                if e.code < 500 and e.code != 429:
                    return None, f"HTTP {e.code}"
                err = f"HTTP {e.code}"
            except Exception as e:
                err = f"{type(e).__name__}: {e}"[:300]
        time.sleep(5 * 2 ** attempt)
    return None, "transient x3: " + err


@app.function(timeout=4 * 3600, cpu=1)
def download(urls):
    have = {f.rsplit('.', 1)[0] for f in os.listdir(f"{ROOT}/videos") if '.' in f}
    results, saved = [], 0
    for url in urls:
        if name(url) in have:
            results.append(dict(url=url, ok=True, reason="already present")); continue
        path, reason = fetch(url)
        if path:
            dest = f"{ROOT}/videos/{os.path.basename(path)}"
            if not os.path.exists(dest):  # add-only
                shutil.copyfile(path, dest); saved += 1
                if saved % 25 == 0: vol.commit()
        results.append(dict(url=url, ok=bool(path), reason=reason, file=path and os.path.basename(path)))
        print(json.dumps(results[-1]), flush=True)
        if reason.startswith("BOTCHECK"):  # do not evade; stop this host
            results += [dict(url=u, ok=False, reason="skipped after bot-check") for u in urls[len(results):]]
            break
        time.sleep(random.uniform(0.5, 1.5))  # be nice to the host (as upstream)
    vol.commit()
    return results


def counts(rows, data):
    top100 = {e['gloss'] for e in data[:100]}
    c = collections.Counter(r['split'] for r in rows)
    c100 = collections.Counter(r['split'] for r in rows if r['text'] in top100)
    return dict(total=len(rows), **c), dict(total=sum(c100.values()), **c100)


@app.function(timeout=2 * 3600, cpu=2)
def reindex(attempts, date):
    import csv
    vol.reload()
    os.chdir(ROOT)
    sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
    backup = "index.2026-07-09.csv"
    if not os.path.exists(backup):
        shutil.copyfile("index.csv", backup)
    old_sha = sha("index.csv")
    subprocess.run([sys.executable, "create_index.py"], check=True)
    rows = list(csv.DictReader(open("index.csv")))
    missing_files = [r['file'] for r in rows if not os.path.exists(r['file'])]
    data = json.load(open("WLASL_v0.3.json"))
    by_host = collections.defaultdict(collections.Counter)
    for a in attempts:
        host = a['url'].split('/')[2].replace('www.', '')
        by_host[host][a['reason'] if not a['ok'] or a['reason'] != "ok" else "downloaded"] += 1
    allc, c100 = counts(rows, data)
    prov = dict(
        date=date, script="papers/kavediya-2025-isosignvid2aud/wlasl_data.py (REPRO-SIGN repository)",
        tools=dict(python=sys.version.split()[0], yt_dlp=YTDLP, ffmpeg=subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True).stdout.splitlines()[0]),
        json_sha256=sha("WLASL_v0.3.json"), create_index_sha256=sha("create_index.py"),
        index_before_sha256=old_sha, index_backup=backup, index_backup_sha256=sha(backup), index_after_sha256=sha("index.csv"),
        video_files=len(os.listdir("videos")), index_rows=allc, index_rows_wlasl100=c100, index_files_missing=len(missing_files),
        attempts_by_host={h: dict(c) for h, c in by_host.items()}, attempts_log=f"attempts-{date}.jsonl")
    with open(f"attempts-{date}.jsonl", "w") as f:
        f.writelines(json.dumps(a) + "\n" for a in attempts)
    json.dump(prov, open(f"provenance-{date}.json", "w"), indent=1)
    vol.commit()
    return prov


@app.local_entrypoint()
def main(limit: int = 0):  # --limit N: preflight N URLs per host, no reindex
    import io
    data = json.load(io.BytesIO(b"".join(vol.read_file("WLASL/WLASL_v0.3.json"))))
    have = {e.path.rsplit('/', 1)[-1].rsplit('.', 1)[0] for e in vol.listdir("WLASL/videos")}
    groups = collections.defaultdict(list)
    for entry in data:  # JSON order: WLASL-100 glosses first
        for inst in entry['instances']:
            url = inst['url']
            host = url.split('/')[2].replace('www.', '')
            if name(url) not in have and 'aslpro' not in url and url not in groups[host]:
                groups[host].append(url)
    groups['youtube'] = groups.pop('youtube.com', []) + groups.pop('youtu.be', [])  # one polite YouTube worker
    print({h: len(u) for h, u in groups.items()})
    attempts = [a for res in download.map([u[:limit] if limit else u for u in groups.values()]) for a in res]
    if limit:
        return print(json.dumps(attempts, indent=1))
    prov = reindex.remote(attempts, datetime.date.today().isoformat())
    print(json.dumps(prov, indent=1))
