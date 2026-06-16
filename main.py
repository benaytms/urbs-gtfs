from pipeline.fetching.fetch import fetch_all 
from pipeline.transform.transform import transform
from pipeline.validate.validate import validate
from pipeline.diff_check.diff_check import diff_check
from pipeline.publish.publish import publish
from datetime import datetime
from zoneinfo import ZoneInfo

TIMEZONE = ZoneInfo("America/Sao_Paulo")

if __name__ == '__main__':
    # fetches all source data, including:
    # pontosLinha, linhas, tabelaLinha, shapeLinha
    # feriados_nacionais e feriados_municipais
    # also creates static data for GTFS, like feed_info and agency
    fetch_all()
    # transforms all of the source data to fit the GTFS
    # feed correctly
    date = datetime.now(TIMEZONE).strftime('%Y_%m_%d')
    transform(date)
    # validates the transformed data against the GTFS validator
    validate()
    # check for any changes in the zip file, if there are changes, publish
    # new release.
    diff_check()

    ## the publish function is only for me, for testing locally just diff_check is necessary
    #if diff_check():
    #    publish()
