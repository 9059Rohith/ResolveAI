"""Download the original archive, without requiring a Kaggle account when public."""

import hashlib
import json
import shutil
import time
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

URL = "https://www.kaggle.com/api/v1/datasets/download/thoughtvector/customer-support-on-twitter"


def download_parallel(url: str, destination: Path) -> None:
    """Use byte ranges when supported, with a sequential fallback."""
    probe = urllib.request.Request(url, headers={"Range": "bytes=0-0"})
    with urllib.request.urlopen(probe, timeout=90) as response:
        content_range = response.headers.get("Content-Range", "")
    if "/" not in content_range:
        with urllib.request.urlopen(url, timeout=90) as response, destination.open("wb") as out:
            shutil.copyfileobj(response, out)
        return
    total = int(content_range.rsplit("/", 1)[1])
    chunk_size = 4 * 1024 * 1024
    destination.unlink(missing_ok=True)
    with destination.open("wb") as out:
        out.truncate(total)

    def fetch(index: int) -> None:
        start = index * chunk_size
        end = min(total, start + chunk_size) - 1
        request = urllib.request.Request(url, headers={"Range": f"bytes={start}-{end}"})
        error = None
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=90) as response:
                    data = response.read()
                if len(data) != end - start + 1:
                    raise OSError(f"Short range response for bytes {start}-{end}")
                break
            except OSError as exc:
                error = exc
                if attempt < 2:
                    time.sleep(0.5 * (2**attempt))
        else:
            raise OSError(f"Range download failed for bytes {start}-{end}") from error
        with destination.open("r+b") as out:
            out.seek(start)
            out.write(data)

    with ThreadPoolExecutor(max_workers=12) as pool:
        list(pool.map(fetch, range((total + chunk_size - 1) // chunk_size)))


def main() -> None:
    folder = Path("data/raw")
    folder.mkdir(parents=True, exist_ok=True)
    archive = folder / "twitter.zip"
    valid = False
    if archive.exists():
        try:
            with zipfile.ZipFile(archive) as existing:
                valid = (
                    any(n.endswith("twcs.csv") for n in existing.namelist())
                    and existing.testzip() is None
                )
        except zipfile.BadZipFile:
            valid = False
    if not valid:
        partial = archive.with_suffix(".partial")
        try:
            download_parallel(URL, partial)
            with zipfile.ZipFile(partial) as z:
                if not any(n.endswith("twcs.csv") for n in z.namelist()):
                    raise ValueError("The download is not the expected dataset.")
            partial.replace(archive)
        except Exception as exc:
            partial.unlink(missing_ok=True)
            raise SystemExit(
                "Download failed. Obtain twcs.csv from the cited Kaggle page and place it in data/raw/. "
                + type(exc).__name__
            ) from exc
    sha = hashlib.file_digest(archive.open("rb"), "sha256").hexdigest()
    with zipfile.ZipFile(archive) as z:
        name = next(n for n in z.namelist() if n.endswith("twcs.csv"))
        with z.open(name) as source, (folder / "twcs.csv").open("wb") as out:
            shutil.copyfileobj(source, out)
    Path("data/processed/source.json").write_text(
        json.dumps(
            dict(
                url=URL,
                archive_sha256=sha,
                license="CC-BY-NC-SA-4.0",
                dataset="thoughtvector/customer-support-on-twitter",
            ),
            indent=2,
        )
    )
    print("Downloaded and verified original dataset:", sha)


if __name__ == "__main__":
    main()
