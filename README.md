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
