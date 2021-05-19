from datetime import datetime
from itertools import chain

import pandas as pd

from vax.cmd.utils import get_logger

logger = get_logger()

VACCINES_ACCEPTED = [
    "Abdala",
    "CanSino",
    "Covaxin",
    "EpiVacCorona",
    "Johnson&Johnson",
    "QazVac",
    "Moderna",
    "Oxford/AstraZeneca",
    "Pfizer/BioNTech",
    "RBD-Dimer",
    "Sinopharm/Beijing",
    "Sinopharm/HayatVax",
    "Sinopharm/Wuhan",
    "Sinovac",
    "Sputnik V",
]

VACCINES_ONE_DOSE = [
    "Johnson&Johnson",
    "CanSino",
]

def country_df_sanity_checks(
        df: pd.DataFrame, allow_extra_cols: bool = True, monotonic_check_skip: list = [],
        anomalies: bool = True, anomaly_check_skip: list = []) -> pd.DataFrame:
    checker = CountryChecker(
        df, monotonic_check_skip=monotonic_check_skip, anomalies=anomalies, anomaly_check_skip=anomaly_check_skip
    )
    checker.run()


class CountryChecker:
    def __init__(self, df: pd.DataFrame, allow_extra_cols: bool = True, monotonic_check_skip: list = [],
                 anomalies: bool = True, anomaly_check_skip: list = []):
        self.location = self._get_location(df)
        self.df = df
        self.allow_extra_cols = allow_extra_cols
        self.skip_monocheck_ids = self._skip_check_ids(monotonic_check_skip)
        self.anomalies = anomalies
        self.skip_anomalcheck_ids = self._skip_check_ids(anomaly_check_skip)

    def _get_location(self, df):
        x = df.loc[:, "location"].unique()
        if len(x) != 1:
            raise ValueError(f"More than one location found: {df.loc[:, 'location'].unique()}")
        return x[0]

    def _skip_check_ids(self, check_skip):
        def _f(x):
            dt = x["date"].strftime("%Y%m%d")
            if isinstance(x["metrics"], list):
                return [dt + m for m in x["metrics"]]
            return [x["date"].strftime("%Y%m%d") + x["metrics"]]
    
        res = [_f(x) for x in check_skip]
        return list(chain.from_iterable(res))

    @property
    def metrics_present(self):
        cols = ["total_vaccinations"]
        if "people_vaccinated" in self.df.columns:
            cols.append("people_vaccinated")
        if "people_fully_vaccinated" in self.df.columns:
            cols.append("people_fully_vaccinated")
        return cols

    def check_column_names(self):
        cols = ["total_vaccinations", "vaccine", "date", "location", "source_url"]
        cols_extra = cols + ["people_vaccinated", "people_fully_vaccinated"]
        cols_missing = [col for col in cols if col not in self.df.columns]
        if cols_missing:
            raise ValueError(f"df missing column(s): {cols_missing}.")
        # Ensure validity of column names in df
        if not self.allow_extra_cols:
            cols_wrong = [col for col in self.df.columns if col not in cols_extra]
            if cols_wrong:
                raise ValueError(f"df contains invalid column(s): {cols_wrong}.")

    def check_source_url(self):
        if self.df.source_url.isnull().any():
            raise ValueError(f"{self.location} -- Invalid source_url! NaN values found.")

    def check_vaccine(self):
        if self.df.vaccine.isnull().any():
            raise ValueError(f"{self.location} -- Invalid vaccine! NaN values found.")
        vaccines_used = set([xx for x in self.df.vaccine.tolist() for xx in x.split(', ')])
        if not all([vac in VACCINES_ACCEPTED for vac in vaccines_used]):
            vaccines_wrong = [vac for vac in vaccines_used if vac not in VACCINES_ACCEPTED]
            raise ValueError(f"{self.location} -- Invalid vaccine detected! Check {vaccines_wrong}.")

    def check_date(self):
        if self.df.date.isnull().any():
            raise ValueError(f"{self.location} -- Invalid dates! NaN values found.")
        if (self.df.date.min() < datetime(2020, 12, 1)) or (self.df.date.max() > datetime.now().date()):
            raise ValueError(f"{self.location} -- Invalid dates! Check {self.df.date.min()} and {self.df.date.max()}")
        if self.df.date.nunique() != len(self.df):
            raise ValueError(
                f"{self.location} -- Mismatch between number of rows {len(self.df)} and number of different dates "
                f"{self.df.date.nunique()}. Check {self.df.date.unique()}.")

    def check_location(self):
        if self.df.location.isnull().any():
            raise ValueError(
                f"{self.location} -- Invalid location! NaN values found. Check {self.df.location}."
            )
        if self.df.location.nunique() != 1:
            raise ValueError(
                f"{self.location} -- Invalid location! More than one location found. Check {self.df.location}."
            )

    def check_metrics(self):
        df = self.df.sort_values(by="date")# [self.metrics_present]
        # Monotonically
        self._check_metrics_monotonic(df)
        # Inequalities
        self._check_metrics_inequalities(df)
        # Anomalies
        if self.anomalies:
            self._check_metrics_anomalies(df)

    def _check_metrics_monotonic(self, df: pd.DataFrame):
        # Use info from monotonic_check_skip to raise exception or not
        for col in self.metrics_present:
            _x = df.dropna(subset=[col])
            if not _x[col].is_monotonic:
                idx_wrong = _x[col].diff() < 0
                wrong_rows = _x.loc[idx_wrong]
                wrong_ids = wrong_rows.date.dt.strftime("%Y%m%d") + col
                if not wrong_ids.isin(self.skip_monocheck_ids).all():
                    raise ValueError(
                        f"{self.location} -- Column {col} must be monotonically increasing! Check:\n{wrong_rows}"
                    )

    def _check_metrics_inequalities(self, df: pd.DataFrame):
        if ("total_vaccinations" in df.columns) and ("people_vaccinated" in df.columns):
            df = df[["people_vaccinated", "total_vaccinations"]].dropna()
            if (df["total_vaccinations"] < df["people_vaccinated"]).any():
                raise ValueError(f"{self.location} -- total_vaccinations can't be < people_vaccinated!")
        if ("people_vaccinated" in df.columns) and ("people_fully_vaccinated" in df.columns):
            df = df[["people_vaccinated", "people_fully_vaccinated"]].dropna()
            if (df["people_vaccinated"] < df["people_fully_vaccinated"]).any():
                raise ValueError(f"{self.location} -- people_vaccinated can't be < people_fully_vaccinated!")
        if ("total_vaccinations" in df.columns) and ("people_fully_vaccinated" in df.columns):
            df = df[["people_fully_vaccinated", "total_vaccinations"]].dropna()
            if (df["total_vaccinations"] < df["people_fully_vaccinated"]).any():
                raise ValueError(f"{self.location} -- people_fully_vaccinated can't be < people_vaccinated!")

    def _check_metrics_anomalies(self, df):
        for metric in self.metrics_present:
            self._check_anomalies(df, metric)

    def _check_anomalies(self, df, metric, th=6):
        # Get metric values above 10,000
        df_ = df.set_index("date")
        df_metric = df_.loc[(df_[metric] > 10000), metric]
        # Compute rolling average, 7 days. NaNs are filled with non-smoothed values
        window_size = "7d"
        m = df_metric.rolling(window_size, min_periods=2).mean().shift(1)
        m.loc[m.isnull()] = df_metric[m.isnull()]
        # Compute ratio between rolling average and value. Build Anomalies dataframe
        t = df_metric / (m+1e-9)
        t = pd.DataFrame({
            f"{metric}_{window_size}": m[t > th],
            f"{metric}_ratio": t[t > th],
        })
        anomalies = df_.loc[t.index, [metric]].merge(t, on="date").reset_index()
        if not anomalies.empty:
            wrong_ids = anomalies.date.dt.strftime("%Y%m%d") + metric
            if not wrong_ids.isin(self.skip_anomalcheck_ids).all():
                logger.warn(f"{self.location} -- Potential anomalies found ⚠️:\n{anomalies}")

    def run(self):
        # Ensure required columns are present
        self.check_column_names()
        # Source url consistency
        self.check_source_url()
        # Vaccine consistency
        self.check_vaccine()
        # Date consistency
        self.check_date()
        # Location consistency
        self.check_location()
        # Metrics checks
        self.check_metrics()
