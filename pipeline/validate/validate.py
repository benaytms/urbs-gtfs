import os
import json
import zipfile
import subprocess
import hashlib
import tempfile
from urllib.request import urlopen
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../../.env"))

TIMEZONE = ZoneInfo("America/Sao_Paulo")
PROJECT_ROOT = os.getenv("GTFS_PROJECT_ROOT", "/opt/airflow/urbs-gtfs")
OUTPUT = os.path.join(PROJECT_ROOT, "output")
SOURCE = os.path.join(PROJECT_ROOT, "source")
GTFS_ZIP = os.path.join(OUTPUT, "gtfs_curitiba.zip")
VALIDATION_DIR = os.path.join(OUTPUT, "validation")
VALIDATOR_JAR = os.path.join(PROJECT_ROOT, "gtfs-validator-8.0.1-cli.jar")
VALIDATOR_URL = "https://github.com/MobilityData/gtfs-validator/releases/download/v8.0.1/gtfs-validator-8.0.1-cli.jar"
VALIDATOR_SHA256 = "19293ddd9b6f954f216d4f12054bd8a3232921751c4484339e339764a91000e2"

GTFS_FILES = [
    "agency.txt",
    "routes.txt",
    "trips.txt",
    "stops.txt",
    "stop_times.txt",
    "shapes.txt",
    "calendar.txt",
    "calendar_dates.txt",
    "feed_info.txt",
]


def zip_gtfs(output_dir: str, zip_path: str) -> None:
    print("Zipping GTFS files...")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for fname in GTFS_FILES:
            fpath = os.path.join(output_dir, fname)
            if not os.path.isfile(fpath):
                raise FileNotFoundError(f"GTFS file not found: {fpath}")
            zf.write(fpath, arcname=fname)
    print(f"    Created {zip_path}")


def ensure_validator_jar(
    jar_path: str,
    url: str = VALIDATOR_URL,
    expected_sha256: str = VALIDATOR_SHA256,
) -> None:
    if os.path.isfile(jar_path):
        with open(jar_path, "rb") as jar:
            digest = hashlib.file_digest(jar, "sha256").hexdigest()
        if digest == expected_sha256:
            return
        print(f"Validator JAR has an unexpected checksum; downloading a fresh copy: {jar_path}")
    else:
        print(f"Downloading MobilityData GTFS validator to {jar_path}...")

    jar_dir = os.path.dirname(os.path.abspath(jar_path))
    fd, temporary_path = tempfile.mkstemp(prefix=".gtfs-validator-", suffix=".jar", dir=jar_dir)
    try:
        digest = hashlib.sha256()
        with os.fdopen(fd, "wb") as destination, urlopen(url, timeout=60) as source:
            while chunk := source.read(1024 * 1024):
                destination.write(chunk)
                digest.update(chunk)
        if digest.hexdigest() != expected_sha256:
            raise ValueError(f"Downloaded validator JAR has an unexpected SHA-256 checksum: {url}")
        os.replace(temporary_path, jar_path)
    except OSError as error:
        raise RuntimeError(f"Could not download the validator JAR from {url}: {error}") from error
    finally:
        if os.path.exists(temporary_path):
            os.remove(temporary_path)


def run_validator(jar_path: str, zip_path: str, validation_dir: str) -> None:
    ensure_validator_jar(jar_path)
    os.makedirs(validation_dir, exist_ok=True)
    print("Running MobilityData GTFS validator...")
    result = subprocess.run(
        [
            "java", "-jar", jar_path,
            "--input", zip_path,
            "--output_base", validation_dir,
        ],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"Validator failed (exit {result.returncode}): {details}")
    print("    Validator finished.")


def parse_report(validation_dir: str) -> None:
    report_path = os.path.join(validation_dir, "report.json")
    if not os.path.isfile(report_path):
        raise FileNotFoundError(f"report.json not found at {report_path}")

    with open(report_path, 'r') as f:
        report = json.load(f)

    notices = report.get("notices", [])
    errors = [n for n in notices if n.get("severity") == "ERROR"]
    warnings = [n for n in notices if n.get("severity") == "WARNING"]

    if warnings:
        print(f"\n{len(warnings)} warning(s):")
        for w in warnings:
            print(f"  [WARNING] {w.get('code')} — {w.get('totalNotices')} occurrence(s)")

    if errors:
        print(f"\n{len(errors)} error(s):")
        for e in errors:
            print(f"  [ERROR] {e.get('code')} — {e.get('totalNotices')} occurrence(s)")
        raise ValueError("Validator found errors, fix before publishing.")

    print("\nValidation passed — no errors :D")


def validate() -> None:
    zip_gtfs(OUTPUT, GTFS_ZIP)
    run_validator(VALIDATOR_JAR, GTFS_ZIP, VALIDATION_DIR)
    parse_report(VALIDATION_DIR)


if __name__ == '__main__':
    validate()
