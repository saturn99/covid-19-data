import os
import requests

import pandas as pd


def read(source: str) -> pd.DataFrame:
    data = requests.get(source).json()
    return pd.DataFrame.from_records(data["data"])


def pipeline(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df.total_vaccinations > 0]
    df = (
        df[["date", "total_vaccinations", "total_vaccinated"]]
        .rename(columns={"total_vaccinated": "people_fully_vaccinated"})
        .sort_values("date")
    )
    df = df.assign(
        people_vaccinated=df.total_vaccinations - df.people_fully_vaccinated,
        location="Canada",
        source_url="https://covid19tracker.ca/vaccinationtracker.html",
        vaccine="Moderna, Oxford/AstraZeneca, Pfizer/BioNTech",
    )
    return df


def main(paths):
    source = "https://api.covid19tracker.ca/reports"
    destination = paths.tmp_vax_out("Canada")

    read(source).pipe(pipeline).to_csv(destination, index=False)


if __name__ == "__main__":
    main()
