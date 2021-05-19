import os
import shutil
import datetime
import re

import pandas as pd
import requests


GH_LINK = "https://github.com/owid/covid-19-data/raw/master/public/data/vaccinations/country_data"

def clean_count(count):
    count = re.sub(r"[^0-9]", "", count)
    count = int(count)
    return count


def clean_date(date, fmt):
    return (
        datetime.datetime
        .strptime(date, fmt)
        .strftime("%Y-%m-%d")
    )


def enrich_data(ds: pd.Series, row, value) -> pd.Series:
    return ds.append(pd.Series({row: value}))


def increment(
        paths,
        location,
        total_vaccinations,
        date,
        vaccine,
        source_url,
        people_vaccinated=None,
        people_fully_vaccinated=None):
    assert type(location) == str
    assert isinstance(total_vaccinations, (int, float))
    assert type(people_vaccinated) == int or pd.isnull(people_vaccinated)
    assert type(people_fully_vaccinated) == int or pd.isnull(people_fully_vaccinated)
    assert type(date) == str
    assert re.match(r"\d{4}-\d{2}-\d{2}", date)
    assert date <= str(datetime.date.today() + datetime.timedelta(days=1))
    assert type(vaccine) == str
    assert type(source_url) == str

    filepath_automated = paths.tmp_vax_out(location)
    filepath_public = f"{GH_LINK}/{location}.csv"
    # Move from public to output folder
    if not os.path.isfile(filepath_automated) and requests.get(filepath_public).ok:
        pd.read_csv(filepath_public).to_csv(filepath_automated, index=False)
    # Update file in automatio/output
    if os.path.isfile(filepath_automated):
        df = _increment(
            filepath=filepath_automated,
            location=location,
            total_vaccinations=total_vaccinations,
            date=date,
            vaccine=vaccine,
            source_url=source_url,
            people_vaccinated=people_vaccinated,
            people_fully_vaccinated=people_fully_vaccinated
        )
    # Not available, create new file
    else:
        df = _build_df(
            location=location,
            total_vaccinations=total_vaccinations,
            date=date,
            vaccine=vaccine,
            source_url=source_url,
            people_vaccinated=people_vaccinated,
            people_fully_vaccinated=people_fully_vaccinated
        )
    # To Integer type
    col_ints = ["total_vaccinations", "people_vaccinated", "people_fully_vaccinated"]
    for col in col_ints:
        if col in df.columns:
            df[col] = df[col].astype("Int64").fillna(pd.NA)

    df.to_csv(paths.tmp_vax_out(location), index=False)
    # print(f"NEW: {total_vaccinations} doses on {date}")


def _increment(filepath, location, total_vaccinations, date, vaccine, source_url, people_vaccinated=None,
               people_fully_vaccinated=None):
    prev = pd.read_csv(filepath)
    if total_vaccinations <= prev["total_vaccinations"].max() or date < prev["date"].max():
        df = prev.copy()
    elif date == prev["date"].max():
        df = prev.copy()
        df.loc[df["date"] == date, "total_vaccinations"] = total_vaccinations
        df.loc[df["date"] == date, "people_vaccinated"] = people_vaccinated
        df.loc[df["date"] == date, "people_fully_vaccinated"] = people_fully_vaccinated
        df.loc[df["date"] == date, "source_url"] = source_url
    else:
        new = _build_df(
            location, total_vaccinations, date, vaccine, source_url, people_vaccinated, people_fully_vaccinated
        )
        df = pd.concat([prev, new])
    return df.sort_values("date")


def _build_df(location, total_vaccinations, date, vaccine, source_url, people_vaccinated=None,
              people_fully_vaccinated=None):
    new = pd.DataFrame({
        "location": location,
        "date": date,
        "vaccine": vaccine,
        "total_vaccinations": [total_vaccinations],
        "source_url": source_url,
    })
    if people_vaccinated is not None:
        new["people_vaccinated"] = people_vaccinated
    if people_fully_vaccinated is not None:
        new["people_fully_vaccinated"] = people_fully_vaccinated
    return new
