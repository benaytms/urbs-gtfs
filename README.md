# URBS-GTFS
![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)
![Pandas](https://img.shields.io/badge/Pandas-2.0-150458?logo=pandas)
![Apache Airflow](https://img.shields.io/badge/Airflow-3.2-017CEE?logo=apacheairflow)
![Docker](https://img.shields.io/badge/Docker-blue?logo=docker)
![GTFS](https://img.shields.io/badge/GTFS-valid-brightgreen)

Curitiba has no official GTFS feed, which means the city's public transit data is inaccessible to the applications most people use to navigate. 
The General Transit Feed Specification (GTFS) is the open standard used by trip planning applications such as Google Maps, OsmAnd, and any open source developer to provide public transit directions.
Despite having one of the best urban transit systems in Brazil, Curitiba did not have an official GTFS feed. 

This project fills that gap by automatically transforming raw open data published by C3SL/UFPR into a valid, weekly-updated GTFS feed available to anyone.

***

## Diagram

This diagram aims to visually explain the full process behind the pipeline.

![Diagram](./images/full_pipeline_diagram.svg)


***

## Requirements

- Python 3.13
- Java (for the MobilityData Validator)
- [gtfs-validator-8.0.1-cli.jar](https://github.com/MobilityData/gtfs-validator/releases/download/v8.0.1/gtfs-validator-8.0.1-cli.jar) (place at urbs-gtfs)
- Requirements list at airflow/requirements.txt


***

## How to test

It's worth noting that URBS daily data release time varies a lot,
so if you get a 404 error it could be that.

```bash
git clone https://github.com/benaytms/urbs-gtfs.git
```

```bash
cd urbs-gtfs
mv .env.example .env
## change the variable to your urbs-gtfs path (not including the last '/')
```

```bash
pip install -r airflow/requirements.txt
```

```bash
python3 main.py
```
