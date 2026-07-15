# URBS-GTFS
![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)
![Pandas](https://img.shields.io/badge/Pandas-2.0-150458?logo=pandas)
![Apache Airflow](https://img.shields.io/badge/Airflow-3.2-017CEE?logo=apacheairflow)
![Docker](https://img.shields.io/badge/Docker-blue?logo=docker)
![GTFS](https://img.shields.io/badge/GTFS-valid-brightgreen)

Curitiba had no official GTFS feed, which means the city's public transit data is inaccessible to the open standard most applications use to navigate. 
The General Transit Feed Specification (GTFS) is the open standard used by trip planning applications such as Google Maps, OsmAnd, and any open source developer to provide public transit directions.
Despite having one of the best urban transit systems in Brazil, Curitiba did not have an official GTFS feed. 

This project fills that gap by automatically transforming raw open data published by C3SL/UFPR into a valid, weekly-updated GTFS feed available to anyone.

***

Mobility Database Feed [link](https://mobilitydatabase.org/feeds/gtfs/mdb-3225)

***

## Diagram

This diagram aims to visually explain the full process behind the pipeline.

![Diagram](./images/full_pipeline_diagram.svg)

***

## Design Choices

There were a few specific choices that i made in this project, i'll explain them here.<br>

**Streamed downloads**: URBS often releases very heavy files that could end up using
too much memory, causing issues for people batch-fetching them, so to avoid
issues like that i use streamed downloads in the fetch.py and transform.py step. 
Making sure it reads file by chunks when fetching and also when converting
the csv files.

**Diff checks**: To avoid publishing unchanged same day files - the diff_check.py step
creates a hash string of the zip file, and if the hash string hasn't changed, means the
zip hasn't changed, so it skips the publish.py step entirely.

**Dated folder structure**: Here in the remote repository, it's not possible to see
the source directory which is the directory with all the source files, but this
directory is separated by 'static' and "non-static" directories, the static one
doesn't change at all through feeds, but the other ones do, and each different one has a different
date to uniquely identify each week's feed data.

***

## Requirements

- Python 3.13 (with a virtual environment or with --break-system-packages flag)
- Java (for the MobilityData Validator)
- [gtfs-validator-8.0.1-cli.jar](https://github.com/MobilityData/gtfs-validator/releases/download/v8.0.1/gtfs-validator-8.0.1-cli.jar) (place at urbs-gtfs)
- Requirements list at airflow/requirements.txt


***

## How to test

It's worth noting that URBS daily data release time varies a lot, so if you get a 404 error it could be that.

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

***

## License

The pipeline code is licensed under **Apache 2.0**.
The GTFS data comes from open data published by C3SL/UFPR and is subject to their terms.
