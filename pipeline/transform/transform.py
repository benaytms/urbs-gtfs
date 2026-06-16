import pandas as pd
import numpy as np
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../../.env"))

TIMEZONE = ZoneInfo("America/Sao_Paulo")
PROJECT_ROOT = os.getenv("GTFS_PROJECT_ROOT", "/opt/airflow/urbs-gtfs")
SOURCE = os.path.join(PROJECT_ROOT, "source")
OUTPUT = os.path.join(PROJECT_ROOT, "output")


def transform(date: str) -> None:
    # date: YYYY_MM_DD
    YEAR = int(date[:4])
    source_dir = os.path.join(SOURCE, date)
    static_dir = os.path.join(SOURCE, "static")

    #loading sources
    agency      = pd.read_csv(os.path.join(static_dir, "agency.csv"))
    linhas      = pd.read_csv(os.path.join(source_dir, f"{date}_linhas.csv"))
    tabelaLinha = pd.read_csv(os.path.join(source_dir, f"{date}_tabelaLinha.csv"))
    pontosLinha = pd.read_csv(os.path.join(source_dir, f"{date}_pontosLinha.csv"))
    shapeLinha  = pd.read_csv(os.path.join(source_dir, f"{date}_shapeLinha.csv"))

    #feed_info.txt
    feed_info = pd.read_csv(os.path.join(source_dir, "feed_info.csv"))
    feed_info.to_csv(os.path.join(OUTPUT, "feed_info.txt"), index=False)
    print("feed_info.txt done.")

    #agency.txt
    urbs = agency[agency['agency_name'] == 'Urbanização de Curitiba S/A']
    urbs_id = urbs['agency_id'].iloc[0].astype('int8')
    agency.to_csv(os.path.join(OUTPUT, "agency.txt"), index=False)
    print("agency.txt done.")

    #routes.txt
    linhas['agency_id'] = urbs_id
    linhas['route_type'] = np.int16(3)
    linhas = linhas.rename(columns={
        'COD': 'route_id',
        'NOME': 'route_long_name',
        'NOME_COR': 'route_color_name',
        'SOMENTE_CARTAO': 'only_card',
        'CATEGORIA_SERVICO': 'service_category',
    })
    linhas = linhas[['route_id', 'agency_id', 'route_long_name', 'route_type']]
    routes = linhas.copy()
    routes['route_long_name'] = routes['route_long_name'].str.title()
    routes.to_csv(os.path.join(OUTPUT, "routes.txt"), index=False)
    print("routes.txt done.")

    #shapes.txt
    shapeLinha = shapeLinha.rename(columns={
        'SHP': 'shape_id',
        'LAT': 'shape_pt_lat',
        'LON': 'shape_pt_lon',
        'COD': 'route_id'
    })
    shapeLinha['shape_pt_lat'] = shapeLinha['shape_pt_lat'].astype(str).str.replace(',', '.').astype('float64')
    shapeLinha['shape_pt_lon'] = shapeLinha['shape_pt_lon'].astype(str).str.replace(',', '.').astype('float64')
    shapeLinha['shape_pt_sequence'] = shapeLinha.groupby('shape_id').cumcount() + 1
    shapes = shapeLinha.drop('route_id', axis=1)
    shapes.to_csv(os.path.join(OUTPUT, "shapes.txt"), index=False)
    print("shapes.txt done.")

    #calendar.txt
    calendar = pd.DataFrame({
        'service_id': ['dias_uteis', 'sabado', 'domingo'],
        'monday':    [1, 0, 0],
        'tuesday':   [1, 0, 0],
        'wednesday': [1, 0, 0],
        'thursday':  [1, 0, 0],
        'friday':    [1, 0, 0],
        'saturday':  [0, 1, 0],
        'sunday':    [0, 0, 1],
        'start_date': [f'{YEAR}0101'] * 3,
        'end_date':   [f'{YEAR}1231'] * 3,
    })
    calendar.to_csv(os.path.join(OUTPUT, "calendar.txt"), index=False)
    print("calendar.txt done.")

    #calendar_dates.txt
    nacionais = pd.read_excel(os.path.join(static_dir, "feriados_nacionais.xls"))
    municipais = pd.read_csv(os.path.join(static_dir, f"municipais_{YEAR}.csv"),
                             names=['Data', 'tipo', 'escopo', 'tipo2', 'estado', 'ibge'])

    nacionais = nacionais[0:nacionais.tail(9).index[0]]
    nacionais['Data'] = pd.to_datetime(nacionais['Data'], errors='coerce')
    nacionais_ano = nacionais[nacionais['Data'].dt.year == YEAR]['Data'].copy()

    municipais['Data'] = pd.to_datetime(municipais['Data'], errors='coerce', dayfirst=True)
    municipais = municipais[municipais['ibge'] == 4106902]['Data']

    feriados_ano = (
        pd.concat([nacionais_ano, municipais], axis=0)
        .drop_duplicates()
        .reset_index(drop=True)
    )

    calendar_dates = pd.DataFrame(feriados_ano).copy()
    calendar_dates['service_id'] = 'domingo'
    calendar_dates['date'] = calendar_dates['Data'].dt.strftime('%Y%m%d')
    calendar_dates['exception_type'] = 1
    calendar_dates = calendar_dates.drop('Data', axis=1)
    calendar_dates = (
        calendar_dates[['service_id', 'date', 'exception_type']]
        .sort_values(by='date', ascending=True)
        .reset_index(drop=True)
    )
    calendar_dates.to_csv(os.path.join(OUTPUT, "calendar_dates.txt"), index=False)
    print("calendar_dates.txt done.")

    #stops, trips, stop_times
    pontosLinha['LAT'] = pontosLinha['LAT'].str.replace(',', '.').astype('float64')
    pontosLinha['LON'] = pontosLinha['LON'].str.replace(',', '.').astype('float64')

    stops = pontosLinha.drop_duplicates(subset=['NUM'], ignore_index=True)
    stops = stops.rename(columns={
        'NOME': 'stop_name',
        'NUM': 'stop_id',
        'LAT': 'stop_lat',
        'LON': 'stop_lon'
    })
    stops = stops[['stop_id', 'stop_name', 'stop_lat', 'stop_lon']]
    stops['location_type'] = 0
    stops['stop_name'] = stops['stop_name'].str.title()

    dia_map = {'1': 'dias_uteis', '2': 'sabado', '3': 'domingo'}
    trips = tabelaLinha.drop_duplicates().copy()
    trips['service_id'] = trips['DIA'].astype(str).map(dia_map)
    trips['trip_id'] = (
        trips['COD'].astype(str) + '_' +
        trips['DIA'].astype(str) + '_' +
        trips['NUM'].astype(str) + '_' +
        trips['HORA'].str.replace(':', '')
    )
    trips = trips.rename(columns={'COD': 'route_id'})
    trips = trips[['route_id', 'service_id', 'trip_id', 'NUM', 'HORA']]

    itinerary_start = (
        pontosLinha.sort_values('SEQ')
        .groupby(['COD', 'NUM'])
        .first()
        .reset_index()[['COD', 'NUM', 'ITINERARY_ID']]
    )

    trips_with_itinerary = trips.merge(
        itinerary_start,
        left_on=['route_id', 'NUM'],
        right_on=['COD', 'NUM'],
        how='left'
    ).drop('COD', axis=1)

    stop_times = trips_with_itinerary.merge(
        pontosLinha[['NUM', 'SEQ', 'ITINERARY_ID', 'COD']],
        left_on=['ITINERARY_ID', 'route_id'],
        right_on=['ITINERARY_ID', 'COD'],
        how='left'
    ).drop('COD', axis=1)

    stop_times = stop_times.rename(columns={
        'NUM_x': 'departure_terminal',
        'NUM_y': 'stop_id',
        'SEQ': 'stop_sequence'
    })

    stop_times = stop_times.dropna(subset=['stop_id', 'stop_sequence'])
    stop_times['stop_id'] = stop_times['stop_id'].astype(int)
    stop_times['stop_sequence'] = stop_times['stop_sequence'].astype(int)

    stop_times['arrival_time'] = np.where(
        stop_times['stop_id'] == stop_times['departure_terminal'],
        stop_times['HORA'] + ':00', ''
    )
    stop_times['departure_time'] = stop_times['arrival_time']
    stop_times['timepoint'] = np.where(
        stop_times['stop_id'] == stop_times['departure_terminal'], 1, 0
    )

    trip_times = stop_times[stop_times['timepoint'] == 1].groupby('trip_id')['arrival_time'].first()
    trip_min   = stop_times.groupby('trip_id')['stop_sequence'].min()
    trip_max   = stop_times.groupby('trip_id')['stop_sequence'].max()

    stop_times['_known_time'] = stop_times['trip_id'].map(trip_times)
    stop_times['_min_seq']    = stop_times['trip_id'].map(trip_min)
    stop_times['_max_seq']    = stop_times['trip_id'].map(trip_max)

    is_edge = (
        (stop_times['stop_sequence'] == stop_times['_min_seq']) |
        (stop_times['stop_sequence'] == stop_times['_max_seq'])
    )
    stop_times.loc[is_edge & (stop_times['arrival_time'] == ''), 'arrival_time'] = \
        stop_times.loc[is_edge & (stop_times['arrival_time'] == ''), '_known_time']
    stop_times.loc[is_edge & (stop_times['departure_time'] == ''), 'departure_time'] = \
        stop_times.loc[is_edge & (stop_times['departure_time'] == ''), '_known_time']
    stop_times.loc[is_edge, 'timepoint'] = 1

    stop_times = stop_times.drop(columns=[
        '_known_time', '_min_seq', '_max_seq',
        'departure_terminal', 'ITINERARY_ID', 'HORA',
        'service_id', 'route_id'
    ])
    stop_times = stop_times[['trip_id', 'arrival_time', 'departure_time', 'stop_id', 'stop_sequence', 'timepoint']]
    stop_times = stop_times.sort_values(['trip_id', 'stop_sequence'])

    stops = stops[stops['stop_id'].isin(stop_times['stop_id'].unique())]

    trips[['route_id', 'service_id', 'trip_id']].to_csv(os.path.join(OUTPUT, "trips.txt"), index=False)
    stops.to_csv(os.path.join(OUTPUT, "stops.txt"), index=False)
    stop_times.to_csv(os.path.join(OUTPUT, "stop_times.txt"), index=False)
    print("trips.txt, stops.txt, stop_times.txt done.")

    print("\nTransform complete.")


if __name__ == '__main__':
    date = datetime.now(TIMEZONE).strftime('%Y_%m_%d')
    transform(date)