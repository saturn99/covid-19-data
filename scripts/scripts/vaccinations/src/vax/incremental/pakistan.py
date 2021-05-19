import locale
import re

from bs4 import BeautifulSoup
import pandas as pd

from vax.utils.incremental import enrich_data, increment, clean_date, clean_count
from vax.utils.utils import get_soup


def read(source: str) -> pd.Series:
    soup = get_soup(source)

    counters = soup.find_all(class_="counter")
    people_partially_vaccinated = clean_count(counters[0].text)
    people_fully_vaccinated = clean_count(counters[1].text)
    total_vaccinations = clean_count(counters[2].text)
    people_vaccinated = people_partially_vaccinated + people_fully_vaccinated

    date = soup.find("span", id="last-update").text
    date = re.search(r"\d+.*202\d", date).group(0)
    date = clean_date(date, "%d %B, %Y")

    data = {
        "total_vaccinations": total_vaccinations,
        "people_vaccinated": people_vaccinated,
        "people_fully_vaccinated": people_fully_vaccinated,
        "date": date,
        "source_url": source,
    }
    return pd.Series(data=data)


def enrich_location(ds: pd.Series) -> pd.Series:
    return enrich_data(ds, "location", "Pakistan")


def enrich_vaccine(ds: pd.Series) -> pd.Series:
    return enrich_data(ds, "vaccine", "CanSino, Sinovac, Sinopharm/Beijing, Sputnik V")


def pipeline(ds: pd.Series) -> pd.Series:
    return (
        ds
        .pipe(enrich_location)
        .pipe(enrich_vaccine)
    )


def main(paths):
    locale.setlocale(locale.LC_TIME, "en_GB")
    source = "https://ncoc.gov.pk/covid-vaccination-en.php"
    data = read(source).pipe(pipeline)
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
