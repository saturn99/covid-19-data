import os
import re
import time

from bs4 import BeautifulSoup
import dateparser
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from vax.utils.incremental import enrich_data, increment, clean_count


def read(source: str) -> pd.Series:
    op = Options()
    op.add_argument("--headless")

    with webdriver.Chrome(options=op) as driver:
        driver.get(source)
        time.sleep(1)

        for h5 in driver.find_elements_by_tag_name("h5"):

            if "Primera dosis" in h5.text:
                people_vaccinated = clean_count(
                    h5.find_element_by_xpath("./preceding-sibling::div").text
                )

            elif "Total dosis aplicadas" in h5.text:
                total_vaccinations = clean_count(
                    h5.find_element_by_xpath("./preceding-sibling::div").text
                )

            elif "Población completamente vacunada" in h5.text:
                people_fully_vaccinated = clean_count(
                    h5.find_element_by_xpath("./preceding-sibling::div").text
                )

            elif "Acumulados al" in h5.text:
                date = h5.text.replace("Acumulados al ", "")
                date = str(dateparser.parse(date, languages=["es"]).date())


    data = {
        "date": date,
        "people_vaccinated": people_vaccinated,
        "people_fully_vaccinated": people_fully_vaccinated,
        "total_vaccinations": total_vaccinations,
    }
    return pd.Series(data=data)


def enrich_location(ds: pd.Series) -> pd.Series:
    return enrich_data(ds, "location", "Dominican Republic")


def enrich_vaccine(ds: pd.Series) -> pd.Series:
    return enrich_data(ds, "vaccine", "Oxford/AstraZeneca, Sinopharm/Beijing, Sinovac")


def enrich_source(ds: pd.Series, source: str) -> pd.Series:
    return enrich_data(ds, "source_url", source)


def pipeline(ds: pd.Series, source: str) -> pd.Series:
    return (
        ds
        .pipe(enrich_location)
        .pipe(enrich_vaccine)
        .pipe(enrich_source, source)
    )


def main(paths):
    source = "https://vacunate.gob.do/"
    data = read(source).pipe(pipeline, source)
    increment(
        paths=paths,
        location=data["location"],
        total_vaccinations=data["total_vaccinations"],
        people_vaccinated=data["people_vaccinated"],
        people_fully_vaccinated=data["people_fully_vaccinated"],
        date=data["date"],
        source_url=data["source_url"],
        vaccine=data["vaccine"]
    )


if __name__ == "__main__":
    main()
