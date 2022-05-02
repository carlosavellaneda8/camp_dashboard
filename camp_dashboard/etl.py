"""ETL process"""
from datetime import date
import requests
import pandas as pd
import streamlit as st

today_date = date.today().strftime("%Y-%m-%d")


class AirtableData:

    """Class that wraps the ETL process from Airtable"""

    def __init__(self, url: str, headers: str) -> None:
        self.url = url
        self.headers = headers
        self.data = pd.DataFrame()

    def run(self) -> pd.DataFrame:
        """Execute ETL process"""
        self.download_data()
        self.data_preprocess()
        return self.data

    def download_data(self) -> None:
        """Download data from Airtable"""
        params = ()
        records = []
        run = True
        while run:
            r = requests.get(self.url, params=params, headers=self.headers)
            data = pd.json_normalize(r.json()["records"])
            records.append(data)
            if "offset" in r.json():
                run = True
                params = (("offset", r.json()["offset"]), )
            else:
                run = False
        output_data = pd.concat(records)
        self.data = output_data

    def data_preprocess(self) -> None:
        """Preprocess the downloaded data"""
        self.data.columns = self.data.columns.str.replace("fields.", "", regex=False)
        self.data.columns = self.data.columns.str.replace(" +|/", "_", regex=True).str.lower()
        self.data["detalle_obra"] = self.data.detalle_obra.str.strip()
        payment_date = pd.to_datetime(self.data.fecha_de_abono, format="%Y-%m-%d")
        self.data["fecha_de_abono"] = payment_date
        self.data["week"] = payment_date - pd.to_timedelta(payment_date.dt.dayofweek, unit="d")
        self.data["week"] = self.data.week.dt.strftime("%Y-%m-%d")
