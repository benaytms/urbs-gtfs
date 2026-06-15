import os
import json
import zipfile
import subprocess
from datetime import datetime
from zoneinfo import ZoneInfo

TIMEZONE = ZoneInfo("America/Sao_Paulo")
OUTPUT = "../../output/"
VALIDATOR_JAR = "../../gtfs-validator-8.0.1-cli.jar"
GTFS_ZIP = os.path.join(OUTPUT, "gtfs_curitiba.zip")
VALIDATION_DIR = os.path.join(OUTPUT, "validation")

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


def run_validator(jar_path: str, zip_path: str, validation_dir: str) -> None:
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
        print(result.stderr)
        raise RuntimeError("Validator returned an error.")
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