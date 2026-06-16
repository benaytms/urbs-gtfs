from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import pandas as pd
import requests
import lzma
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../../.env"))

URL_URBS = r"https://dadosabertos.c3sl.ufpr.br/curitibaurbs/"
URL_FERIADOS_CURITIBA = r"https://raw.githubusercontent.com/joaopbini/feriados-brasil/refs/heads/master/dados/feriados/municipal/csv/"
URL_FERIADOS_NACIONAIS = r"https://www.anbima.com.br/feriados/arqs/"

TIMEZONE = ZoneInfo("America/Sao_Paulo")

FILES_NAMES = ['linhas', 'pontosLinha', 'shapeLinha', 'tabelaLinha']

PROJECT_ROOT = os.getenv("GTFS_PROJECT_ROOT", "/opt/airflow/urbs-gtfs")
SOURCE = os.path.join(PROJECT_ROOT, "source")
STATIC_DIR = os.path.join(SOURCE, "static")

os.makedirs(SOURCE, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)



def get_current_date() -> (str, str):
    CURRENT_DATE = datetime.now(TIMEZONE).strftime('%Y_%m_%d')
    YEAR = str(datetime.now(TIMEZONE).year)
    return (CURRENT_DATE, YEAR)


def fetch_urbs_files(date) -> None:
    file_ext = ".json.xz"
    files_to_get = [(date[0] + '_' + f + file_ext) for f in FILES_NAMES]

    destination_field = os.path.join(SOURCE, date[0])
    os.makedirs(destination_field, exist_ok=True)

    for file in files_to_get:
        current_compressed_file = os.path.join(destination_field, file)
        current_uncompressed_file = os.path.join(destination_field, file.replace(".xz", ""))
        current_converted_file = os.path.join(destination_field, file.replace(".json.xz", ".csv"))
        current_file_url = URL_URBS + file

        if os.path.isfile(current_converted_file):
            print(f"{current_converted_file} already in place, skipping...")
            continue

        if not os.path.isfile(current_compressed_file):
            try:
                requests.head(URL_URBS, timeout=5)
                print("Connection established")
            except requests.RequestException:
                print(f"{URL_URBS} is not reachable at this time...")
                raise
            print(f"Fetching {file}...")
            response = requests.get(current_file_url, stream=True)
            response.raise_for_status()
            with open(current_compressed_file, 'wb') as wfile:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        wfile.write(chunk)

        if not os.path.isfile(current_uncompressed_file):
            try:
                with lzma.open(current_compressed_file, 'rb') as f_in, open(current_uncompressed_file, 'wb') as f_out:
                    print(f"Uncompressing {file}...")
                    f_out.write(f_in.read())
                    print("    Done.")
            except lzma.LZMAError as e:
                raise RuntimeError(f"Failed to decompress {current_uncompressed_file}: {e}") from e

        if not os.path.isfile(current_converted_file):
            print(f"Converting {current_uncompressed_file} to CSV")
            temp = pd.read_json(current_uncompressed_file)
            temp.to_csv(current_converted_file, index=False)
            print("    Done.")

        print("Cleaning up compressed and unconverted files")
        if os.path.isfile(current_compressed_file):
            os.remove(current_compressed_file)
        if os.path.isfile(current_uncompressed_file):
            os.remove(current_uncompressed_file)


def build_feed_info(date) -> None:
    now = datetime.now(TIMEZONE)
    start_date = now.strftime('%Y%m%d')
    end_date = (now + timedelta(weeks=1)).strftime('%Y%m%d')

    destination_field = os.path.join(SOURCE, date[0])
    os.makedirs(destination_field, exist_ok=True)

    feed_info = pd.DataFrame([{
        'feed_publisher_name': 'Benay Tomas',
        'feed_publisher_url': 'https://github.com/benaytms',
        'feed_lang': 'pt-BR',
        'feed_start_date': start_date,
        'feed_end_date': end_date,
        'feed_version': '1.0',
        'feed_contact_email': 'benaytomas@proton.me'
    }])
    feed_info.to_csv(os.path.join(destination_field, 'feed_info.csv'), index=False)
    print(f"feed_info.csv done. ({start_date} → {end_date})")


def build_agency() -> None:
    agency_path = os.path.join(STATIC_DIR, 'agency.csv')
    if not os.path.isfile(agency_path):
        print("agency.csv not found, creating...")
        agency = pd.DataFrame([{
            'agency_id': 1,
            'agency_name': 'Urbanização de Curitiba S/A',
            'agency_url': 'https://www.urbs.curitiba.pr.gov.br/',
            'agency_timezone': 'America/Sao_Paulo',
            'agency_lang': 'pt-BR',
            'agency_phone': '+554133206900',
            'agency_email': 'ouvidoriaurbs@urbs.curitiba.pr.gov.br'
        }])
        agency.to_csv(agency_path, index=False)
        print("agency.csv created.")
    else:
        print("agency.csv already in place, skipping...")


def fetch_feriados_municipais(date) -> None:
    holidays_file = os.path.join(STATIC_DIR, f"municipais_{date[1]}.csv")

    if not os.path.isfile(holidays_file):
        holidays_url = URL_FERIADOS_CURITIBA + date[1] + ".csv"
        try:
            requests.head(URL_FERIADOS_CURITIBA, timeout=5)
            print("Connection established")
        except requests.RequestException:
            print(f"{URL_FERIADOS_CURITIBA} is not reachable at this time...")
            raise
        print(f"Fetching municipais_{date[1]}.csv...")
        response = requests.get(holidays_url, stream=True)
        response.raise_for_status()
        with open(holidays_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"    Saved to {holidays_file}")
    else:
        print(f"municipais_{date[1]}.csv already in place, skipping...")


def fetch_feriados_nacionais() -> None:
    nacionais_path = os.path.join(STATIC_DIR, 'feriados_nacionais.xls')

    if not os.path.isfile(nacionais_path):
        nacionais_url = URL_FERIADOS_NACIONAIS + "feriados_nacionais.xls"
        try:
            requests.head(URL_FERIADOS_NACIONAIS, timeout=5)
            print("Connection established")
        except requests.RequestException:
            print(f"{URL_FERIADOS_NACIONAIS} is not reachable at this time...")
            raise
        print("Fetching feriados_nacionais.xls...")
        response = requests.get(nacionais_url, stream=True)
        response.raise_for_status()
        with open(nacionais_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"    Saved to {nacionais_path}")
    else:
        print("feriados_nacionais.xls already in place, skipping...")

def fetch_all():
    today = get_current_date()
    fetch_urbs_files(today)
    build_feed_info(today)
    fetch_feriados_municipais(today)
    fetch_feriados_nacionais()
    build_agency()
    return datetime.now(TIMEZONE).strftime('%Y_%m_%d')


if __name__ == '__main__':
    fetch_all()