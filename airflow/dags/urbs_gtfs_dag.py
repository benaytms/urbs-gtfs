import sys
import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from dotenv import load_dotenv

PROJECT_ROOT = os.getenv("GTFS_PROJECT_ROOT", "/opt/airflow/urbs-gtfs")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from pipeline.fetching.fetch import fetch_all
from pipeline.transform.transform import transform
from pipeline.validate.validate import validate
from pipeline.diff_check.diff_check import diff_check
from pipeline.publish.publish import publish

default_args = {
    "owner": "betomate",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

def fetch_task():
    return fetch_all()

def transform_task(**context):
    date = context["ti"].xcom_pull(task_ids="fetch")
    transform(date)

def validate_task():
    validate()

def diff_check_task(**context):
    changed = diff_check()
    context["ti"].xcom_push(key="changed", value=changed)

def publish_task(**context):
    changed = context["ti"].xcom_pull(task_ids="diff_check", key="changed")
    if changed:
        publish()
    else:
        print("No changes detected, skipping publish...")

with DAG(
    dag_id="urbs_gtfs_pipeline",
    description="Weekly GTFS static feed pipeline for Curitiba (URBS)",
    start_date=datetime(2026, 6, 15),
    schedule="0 22 * * 1",  # every Monday at 22h
    catchup=False,
    default_args=default_args,
) as dag:

    t_fetch = PythonOperator(
        task_id="fetch",
        python_callable=fetch_task,
    )

    t_transform = PythonOperator(
        task_id="transform",
        python_callable=transform_task,
    )

    t_validate = PythonOperator(
        task_id="validate",
        python_callable=validate_task,
    )

    t_diff_check = PythonOperator(
        task_id="diff_check",
        python_callable=diff_check_task,
    )

    t_publish = PythonOperator(
        task_id="publish",
        python_callable=publish_task,
    )

    t_fetch >> t_transform >> t_validate >> t_diff_check >> t_publish