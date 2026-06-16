FROM apache/airflow:3.2.2

USER root
RUN apt-get update && apt-get install -y default-jre && apt-get clean

USER airflow
RUN pip install pandas numpy requests xlrd openpyxl python-dotenv cryptography