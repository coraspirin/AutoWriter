# powered by mucahid erdogan
"""GitHub Releases uzerinden guncelleme kontrolu, indirme ve kurulum.

Akis:
1. fetch_latest_release(): son release'i GitHub API'den okur.
2. download_asset(): exe'yi gecici dosyaya indirir, SHA-256 ozetini dogrular.
3. install_and_restart(): calisan exe'yi ".old" olarak yeniden adlandirir (Windows
   calisan bir exe'nin silinmesine izin vermez ama yeniden adlandirilmasina izin
   verir), yeni exe'yi yerine koyar ve yeni sureci baslatir. Yeni surec, eski
   surec kapanana kadar bekler (tek ornek kilidi yuzunden) ve .old dosyasini siler.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from threading import Event
from typing import Callable

from app.config import APP_VERSION, GITHUB_REPO

API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
USER_AGENT = "AutoWriter-Updater"
REQUEST_TIMEOUT_SECONDS = 15
DOWNLOAD_CHUNK_BYTES = 256 * 1024

# Yeni surece "eski surec su PID; kapanmasini bekle" demek icin kullanilir.
UPDATED_FROM_PID_ARG = "--updated-from-pid"

ProgressCallback = Callable[[int, int], None]


class UpdateError(Exception):
    pass


@dataclass(frozen=True)
class ReleaseInfo:
    version: str
    tag: str
    page_url: str
    notes: str
    asset_name: str
    asset_url: str
    asset_size: int
    asset_sha256: str | None


def parse_version(text: str) -> tuple[int, ...]:
    """'v1.2.3' -> (1, 2, 3). Sayi olmayan kisimlar (ornegin '-beta') atilir."""
    cleaned = text.strip().lstrip("vV")
    parts: list[int] = []
    for piece in cleaned.split("."):
        digits = ""
        for char in piece:
            if not char.isdigit():
                break
            digits += char
        if not digits:
            break
        parts.append(int(digits))
    return tuple(parts)


def is_newer(remote_version: str, local_version: str = APP_VERSION) -> bool:
    remote = parse_version(remote_version)
    local = parse_version(local_version)
    width = max(len(remote), len(local))
    return remote + (0,) * (width - len(remote)) > local + (0,) * (width - len(local))


def is_frozen() -> bool:
    """PyInstaller ile paketlenmis exe olarak mi calisiyoruz? Kaynaktan
    (python main.py) calisirken exe degistirilemez; release sayfasi acilir."""
    return bool(getattr(sys, "frozen", False))


def _request(url: str, accept: str) -> urllib.request.Request:
    return urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})


def fetch_latest_release() -> ReleaseInfo | None:
    """Son release'i dondurur; exe iceren bir release yoksa None."""
    try:
        with urllib.request.urlopen(
            _request(API_URL, "application/vnd.github+json"),
            timeout=REQUEST_TIMEOUT_SECONDS,
        ) as response:
            data = json.load(response)
    except Exception as exc:  # ag hatasi, 404 (hic release yok), rate limit...
        raise UpdateError(f"Güncelleme bilgisi alınamadı: {exc}") from exc

    asset = next(
        (item for item in data.get("assets", []) if item.get("name", "").lower().endswith(".exe")),
        None,
    )
    if asset is None:
        return None

    digest = asset.get("digest") or ""
    sha256 = digest.split(":", 1)[1].lower() if digest.startswith("sha256:") else None

    tag = data.get("tag_name", "")
    return ReleaseInfo(
        version=tag.lstrip("vV"),
        tag=tag,
        page_url=data.get("html_url", f"https://github.com/{GITHUB_REPO}/releases"),
        notes=(data.get("body") or "").strip(),
        asset_name=asset["name"],
        asset_url=asset["browser_download_url"],
        asset_size=int(asset.get("size") or 0),
        asset_sha256=sha256,
    )


def check_for_update() -> ReleaseInfo | None:
    release = fetch_latest_release()
    if release is not None and is_newer(release.version):
        return release
    return None


def download_asset(
    release: ReleaseInfo,
    progress_callback: ProgressCallback | None = None,
    cancel_event: Event | None = None,
) -> Path:
    """Exe'yi gecici klasore indirir ve ozetini dogrular. Indirilen dosyanin yolunu doner."""
    target_dir = Path(tempfile.gettempdir()) / "AutoWriterUpdate"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"AutoWriter-{release.version}.exe"
    partial = target.with_suffix(".part")

    hasher = hashlib.sha256()
    received = 0
    try:
        with urllib.request.urlopen(
            _request(release.asset_url, "application/octet-stream"),
            timeout=REQUEST_TIMEOUT_SECONDS,
        ) as response, open(partial, "wb") as output:
            total = int(response.headers.get("Content-Length") or release.asset_size or 0)
            while True:
                if cancel_event is not None and cancel_event.is_set():
                    raise UpdateError("İndirme iptal edildi.")
                chunk = response.read(DOWNLOAD_CHUNK_BYTES)
                if not chunk:
                    break
                output.write(chunk)
                hasher.update(chunk)
                received += len(chunk)
                if progress_callback is not None:
                    progress_callback(received, total)
    except UpdateError:
        partial.unlink(missing_ok=True)
        raise
    except Exception as exc:
        partial.unlink(missing_ok=True)
        raise UpdateError(f"İndirme başarısız: {exc}") from exc

    if release.asset_size and received != release.asset_size:
        partial.unlink(missing_ok=True)
        raise UpdateError("İndirilen dosya eksik, tekrar deneyin.")

    if release.asset_sha256 and hasher.hexdigest() != release.asset_sha256:
        partial.unlink(missing_ok=True)
        raise UpdateError("İndirilen dosya doğrulanamadı (SHA-256 uyuşmuyor).")

    os.replace(partial, target)
    return target


def install_and_restart(new_exe: Path) -> None:
    """Calisan exe'yi yenisiyle degistirir ve yeni sureci baslatir. Cagiran taraf
    bu fonksiyondan sonra uygulamayi kapatmalidir."""
    if not is_frozen():
        raise UpdateError("Otomatik kurulum yalnızca exe sürümünde çalışır.")

    current = Path(sys.executable)
    old = current.with_name(current.name + ".old")

    try:
        old.unlink(missing_ok=True)
        os.replace(current, old)
    except OSError as exc:
        raise UpdateError(
            f"Uygulama dosyası değiştirilemedi ({exc}). Klasöre yazma izni olmayabilir."
        ) from exc

    try:
        os.replace(new_exe, current)
    except OSError as exc:
        # Geri al: eski exe yerine donsun ki uygulama bozulmasin.
        os.replace(old, current)
        raise UpdateError(f"Yeni sürüm yerleştirilemedi: {exc}") from exc

    # PyInstaller onefile exe'den baska bir PyInstaller exe baslatirken ortam
    # degiskenleri sifirlanmali; yoksa yeni surec eskinin gecici klasorunu kullanir.
    env = dict(os.environ)
    env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"

    subprocess.Popen(
        [str(current), UPDATED_FROM_PID_ARG, str(os.getpid())],
        env=env,
        close_fds=True,
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
    )


def finish_pending_update(argv: list[str]) -> None:
    """Yeni surecin basinda cagrilir: eski surec kapanana kadar bekler ve
    geride kalan .old dosyasini siler. Guncelleme yoksa sadece temizlik yapar."""
    if UPDATED_FROM_PID_ARG in argv:
        index = argv.index(UPDATED_FROM_PID_ARG)
        try:
            _wait_for_process_exit(int(argv[index + 1]), timeout_seconds=15)
        except (IndexError, ValueError):
            pass

    if not is_frozen():
        return

    old = Path(sys.executable).with_name(Path(sys.executable).name + ".old")
    for _attempt in range(10):
        try:
            old.unlink(missing_ok=True)
            return
        except OSError:
            time.sleep(0.3)


def _wait_for_process_exit(pid: int, timeout_seconds: float) -> None:
    import ctypes
    from ctypes import wintypes

    synchronize = 0x00100000
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.WaitForSingleObject.argtypes = (wintypes.HANDLE, wintypes.DWORD)
    kernel32.WaitForSingleObject.restype = wintypes.DWORD
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel32.CloseHandle.restype = wintypes.BOOL
    handle = kernel32.OpenProcess(synchronize, False, pid)
    if not handle:
        return  # surec zaten kapanmis
    try:
        kernel32.WaitForSingleObject(handle, int(timeout_seconds * 1000))
    finally:
        kernel32.CloseHandle(handle)
