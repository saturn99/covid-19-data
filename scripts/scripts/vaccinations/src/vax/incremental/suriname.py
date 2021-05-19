import os
import datetime

import requests
from bs4 import BeautifulSoup
import pandas as pd
import pytz

from vax.utils.incremental import enrich_data, increment


def read(source: str) -> pd.Series:
    soup = BeautifulSoup(requests.get(source).content, "html.parser")
    return parse_data(soup)


def parse_data(soup: BeautifulSoup) -> pd.Series:

    numbers = soup.find_all(class_="elementor-counter-number")

    return pd.Series(data={
        "total_vaccinations": int(numbers[0]["data-to-value"]),
        "people_vaccinated": int(numbers[1]["data-to-value"]),
        "people_fully_vaccinated": int(numbers[2]["data-to-value"]),
        "date": set_date()
    })


def set_date() -> str:
    return str(datetime.datetime.now(pytz.timezone("America/Paramaribo")).date() - datetime.timedelta(days=1))


def enrich_location(ds: pd.Series) -> pd.Series:
    return enrich_data(ds, "location", "Suriname")


def enrich_vaccine(ds: pd.Series) -> pd.Series:
    return enrich_data(ds, "vaccine", "Oxford/AstraZeneca")


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
    source = "https://laatjevaccineren.sr/"
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
