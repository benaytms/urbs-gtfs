import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../../.env"))

TIMEZONE = ZoneInfo("America/Sao_Paulo")
PROJECT_ROOT = os.getenv("GTFS_PROJECT_ROOT", "/opt/airflow/urbs-gtfs")
OUTPUT = os.path.join(PROJECT_ROOT, "output")
GTFS_ZIP = os.path.join(OUTPUT, "gtfs_curitiba.zip")
RELEASE_TAG = "latest"

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO_OWNER = os.getenv("GITHUB_REPO_OWNER")
GITHUB_REPO_NAME = os.getenv("GITHUB_REPO_NAME")
API_BASE = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}"

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}


def get_existing_release(tag: str) -> dict | None:
    response = requests.get(f"{API_BASE}/releases/tags/{tag}", headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    return None


def delete_release(release_id: int, tag: str) -> None:
    print(f"Deleting existing release {tag}...")
    requests.delete(f"{API_BASE}/releases/{release_id}", headers=HEADERS)
    requests.delete(f"{API_BASE}/git/refs/tags/{tag}", headers=HEADERS)
    print("    Done.")


def create_release(tag: str, date: str) -> dict:
    print(f"Creating release {tag}...")
    payload = {
        "tag_name": tag,
        "name": f"GTFS Curitiba — {date}",
        "body": f"Weekly GTFS static feed for Curitiba (URBS), generated on {date}.",
        "draft": False,
        "prerelease": False
    }
    response = requests.post(f"{API_BASE}/releases", headers=HEADERS, json=payload)
    response.raise_for_status()
    print("    Done.")
    return response.json()


def upload_asset(upload_url: str, zip_path: str) -> None:
    upload_url = upload_url.split("{")[0]
    print("Uploading gtfs_curitiba.zip...")
    with open(zip_path, 'rb') as f:
        response = requests.post(
            upload_url,
            headers={**HEADERS, "Content-Type": "application/zip"},
            params={"name": "gtfs_curitiba.zip"},
            data=f
        )
    response.raise_for_status()
    asset = response.json()
    print(f"    Uploaded: {asset['browser_download_url']}")


def publish() -> None:
    if not GITHUB_TOKEN or not GITHUB_REPO_OWNER or not GITHUB_REPO_NAME:
        raise EnvironmentError("Missing GITHUB_TOKEN, GITHUB_REPO_OWNER or GITHUB_REPO_NAME in .env")

    date = datetime.now(TIMEZONE).strftime('%Y_%m_%d')

    existing = get_existing_release(RELEASE_TAG)
    if existing:
        delete_release(existing['id'], RELEASE_TAG)

    release = create_release(RELEASE_TAG, date)
    upload_asset(release['upload_url'], GTFS_ZIP)

    print(f"\nPublished successfully — stable URL: https://github.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases/latest/download/gtfs_curitiba.zip")


if __name__ == '__main__':
    publish()