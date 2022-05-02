"""Streamlit app"""
import pandas as pd
import streamlit as st
from camp_dashboard.etl import AirtableData

API_KEY = st.secrets["api_key"]
APP_KEY = st.secrets["app_key"]
TABLE = st.secrets["table"]
URL = f"https://api.airtable.com/v0/{APP_KEY}/{TABLE}"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}


# General functions:
@st.cache
def get_data():
    """Retrieve Airtable's data"""
    etl = AirtableData(url=URL, headers=HEADERS)
    return etl.run()


def filter_data(input_dataset: pd.DataFrame, column: str, value: str) -> pd.DataFrame:
    """Function to filter a dataframe"""
    output = input_dataset.copy()
    if value == "Todos":
        return output
    return output[output[column] == value]


def person_summary(input_dataset: pd.DataFrame) -> pd.DataFrame:
    """Function to create a summary by person"""
    data = input_dataset.copy()
    payment_summary = data.groupby("número_de_documento").total_abono.sum().reset_index()
    person_data = data[[
        "número_de_documento", "nombres", "apellidos", "celular",
        "email", "ministerio_obra", "detalle_obra", "quién_invitó"
    ]].copy()
    person_data.drop_duplicates(subset="número_de_documento", inplace=True)
    output = person_data.merge(payment_summary)
    output.columns = output.columns.str.replace("_", " ").str.upper()
    return output


def week_summary(input_dataset: pd.DataFrame) -> pd.DataFrame:
    """Function to create a summary by week"""
    output = input_dataset.copy()
    return output.groupby("week")["total_abono"].sum()


# Dasboard setup
st.set_page_config(
    page_title="Retiro Nacional de Jóvenes",
    page_icon="✅",
    layout="wide",
)

# Retrieving the data
dataset = get_data()

# Dashboard content
st.title("Retiro Nacional de Jóvenes ILBD 2022 - Reporte de pagos")

ministry_list = ["Todos"] + dataset.ministerio_obra.drop_duplicates().tolist()
mission_list = ["Todos"] + dataset.detalle_obra.drop_duplicates().tolist()

main_filter = st.selectbox("Filtrar por ministerio/obra:", ministry_list)
if main_filter == "Obra/iglesia hija":
    secondary_filter = st.selectbox("Obra o iglesia hija:", mission_list)
else:
    secondary_filter = None

filtered_dataset = filter_data(input_dataset=dataset, column="ministerio_obra", value=main_filter)

if secondary_filter:
    filtered_dataset = filter_data(
        input_dataset=filtered_dataset, column="detalle_obra", value=secondary_filter
    )

st.markdown(f"""
### Total de personas inscritas

El total de personas inscritas es {filtered_dataset["número_de_documento"].drop_duplicates().size}

### Valor total recaudado

El valor total recaudado es de ${filtered_dataset.total_abono.sum():,.0f}
""")

week_data = week_summary(input_dataset=filtered_dataset)
person_dataset = person_summary(input_dataset=filtered_dataset)

st.bar_chart(week_data)
st.dataframe(person_dataset)
