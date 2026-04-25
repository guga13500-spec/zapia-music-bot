"""Fix: reescreve ttsdk_downloader.py para usar SDK v5.22a diretamente."""
import importlib.util
import os
import sys

spec = importlib.util.find_spec("teamtalk")
if spec is None:
    print("[fix_sdk] teamtalk nao instalado, pulando")
    sys.exit(0)

pkg_dir = os.path.dirname(spec.origin)
target = os.path.join(pkg_dir, "tools", "ttsdk_downloader.py")

if not os.path.exists(target):
    print(f"[fix_sdk] arquivo nao encontrado: {target}")
    sys.exit(0)

NEW_CONTENT = '''"""Downloader fixado para SDK v5.22a (URL direta, sem scraping)."""
import os
import platform
import shutil
import sys

import patoolib
import requests

from . import downloader

cd = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_url_suffix_from_platform() -> str:
    machine = platform.machine()
    if sys.platform == "win32":
        architecture = platform.architecture()
        if machine == "AMD64" or machine == "x86":
            if architecture[0] == "64bit":
                return "win64"
            else:
                return "win32"
        else:
            sys.exit("Native Windows on ARM is not supported")
    elif sys.platform == "darwin":
        sys.exit("Darwin is not supported")
    else:
        if machine == "AMD64" or machine == "x86_64":
            return "ubuntu22_x86_64"
        elif "arm" in machine:
            return "raspbian_armhf"
        else:
            sys.exit("Your architecture is not supported")


def download() -> None:
    suffix = get_url_suffix_from_platform()
    sdk_url = f"https://bearware.dk/teamtalksdk/v5.22a/tt5sdk_v5.22a_{suffix}.7z"
    print(f"[fix] Baixando SDK: {sdk_url}")
    downloader.download_file(sdk_url, os.path.join(cd, "ttsdk.7z"))
    print("[fix] Download OK")


def extract() -> None:
    try:
        os.mkdir(os.path.join(cd, "ttsdk"))
    except FileExistsError:
        shutil.rmtree(os.path.join(cd, "ttsdk"))
        os.mkdir(os.path.join(cd, "ttsdk"))
    patoolib.extract_archive(os.path.join(cd, "ttsdk.7z"), outdir=os.path.join(cd, "ttsdk"))


def move() -> None:
    path = os.path.join(cd, "ttsdk", os.listdir(os.path.join(cd, "ttsdk"))[0])
    libraries = ["TeamTalk_DLL", "TeamTalkPy"]
    try:
        os.makedirs(os.path.join(cd, "implementation"))
    except FileExistsError:
        shutil.rmtree(os.path.join(cd, "implementation"))
        os.makedirs(os.path.join(cd, "implementation"))
    for library in libraries:
        try:
            os.rename(
                os.path.join(path, "Library", library),
                os.path.join(cd, "implementation", library),
            )
        except OSError:
            shutil.rmtree(os.path.join(cd, "implementation", library))
            os.rename(
                os.path.join(path, "Library", library),
                os.path.join(cd, "implementation", library),
            )
        try:
            os.remove(os.path.join(cd, "implementation", "__init__.py"))
        except OSError:
            pass
        finally:
            with open(os.path.join(cd, "implementation", "__init__.py"), "w") as f:
                f.write("")


def clean() -> None:
    os.remove(os.path.join(cd, "ttsdk.7z"))
    shutil.rmtree(os.path.join(cd, "ttsdk"))
    shutil.rmtree(os.path.join(cd, "implementation", "TeamTalkPy", "test"))


def install() -> None:
    print("Installing TeamTalk sdk components")
    try:
        print("Downloading latest sdk version")
        download()
    except Exception as e:
        print("Failed to download sdk. Error: ", e)
        sys.exit(1)
    try:
        print("Downloaded. extracting")
        extract()
    except patoolib.util.PatoolError as e:
        print("Failed to extract sdk. Error: ", e)
        sys.exit(1)
    print("Extracted. moving")
    move()
    if not os.path.exists(os.path.join(cd, "implementation", "TeamTalk_DLL")):
        print("Failed to move TeamTalk_DLL")
        sys.exit(1)
    if not os.path.exists(os.path.join(cd, "implementation", "TeamTalkPy")):
        print("Failed to move TeamTalkPy")
        sys.exit(1)
    print("moved. cleaning")
    clean()
    print("cleaned.")
    print("Installed")
    sys.exit(0)
'''

with open(target, "w") as f:
    f.write(NEW_CONTENT)

# Limpa cache
import glob
pycache = os.path.join(os.path.dirname(target), "__pycache__")
if os.path.exists(pycache):
    for old in glob.glob(os.path.join(pycache, "ttsdk_downloader*.pyc")):
        os.remove(old)

print(f"[fix_sdk] OK - {target} reescrito para v5.22a")
