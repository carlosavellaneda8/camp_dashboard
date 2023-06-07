"""Streamlit app"""
import numpy as np
import pandas as pd
import streamlit as st
from camp_dashboard.etl import AirtableData

API_KEY = st.secrets["api_key"]
APP_KEY = st.secrets["app_key"]
TABLE = st.secrets["table"]
URL = f"https://api.airtable.com/v0/{APP_KEY}/{TABLE}"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}


# General functions:
@st.cache(allow_output_mutation=True, ttl=60 * 15)
def get_data():
    """Retrieve Airtable's data"""
    etl = AirtableData(url=URL, headers=HEADERS)
    return etl.run()


def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True


def filter_data(input_dataset: pd.DataFrame, column: str, value: str) -> pd.DataFrame:
    """Function to filter a dataframe"""
    output = input_dataset.copy()
    if value == "Todos":
        return output
    filter_ids = output.loc[output[column] == value, "número_de_documento"].drop_duplicates()
    return output[output.número_de_documento.isin(filter_ids)]


def person_summary(input_dataset: pd.DataFrame) -> pd.DataFrame:
    """Function to create a summary by person"""
    data = input_dataset.copy()
    payment_summary = data.groupby("número_de_documento").total_abono.sum().reset_index()
    person_data = data[[
        "número_de_documento", "nombres", "apellidos", "celular",
        "email", "ministerio_obra", "detalle_obra", "quién_invitó"
    ]].copy()
    person_data.drop_duplicates(subset="número_de_documento", inplace=True)
    output = person_data.merge(payment_summary).sort_values(by="total_abono", ascending=False)
    output["número_de_documento"] = output.número_de_documento.astype(str)
    output["número_de_documento"] = output.número_de_documento.str.replace(r"\.0+$", "", regex=True)
    output.columns = output.columns.str.replace("_", " ").str.upper()
    return output.fillna("")


def week_summary(input_dataset: pd.DataFrame) -> pd.DataFrame:
    """Function to create a summary by week"""
    output = input_dataset.copy()
    return output.groupby("week")["total_abono"].sum()


# Dasboard setup
st.set_page_config(
    page_title="Retiro de Jóvenes TBU",
    page_icon="✅",
    layout="wide",
)

if check_password():
    # Retrieving the data
    dataset = get_data()
    dataset["apoyos"] = dataset.observaciones.str.lower().str.contains("apoyo")

    # Dashboard content
    st.title("Retiro Nacional de Jóvenes ILBD 2023 - Reporte de pagos")

    ministry_list = ["Todos"] + dataset.ministerio_obra.drop_duplicates().sort_values().tolist()
    ministry_list.append("Documento")
    mission_list = ["Todos"] + dataset.detalle_obra.drop_duplicates().sort_values().tolist()
    mission_list = [obj for obj in mission_list if obj not in ["", np.nan]]

    with st.sidebar:
        main_filter = st.selectbox("Filtrar por:", ministry_list)
        if main_filter == "Obra/iglesia hija":
            secondary_filter = st.selectbox("Obra o iglesia hija:", mission_list)
        elif main_filter == "Documento":
            secondary_filter = st.number_input("Número de documento:", format="%d", value=0)
        else:
            secondary_filter = None

    filtered_dataset = filter_data(input_dataset=dataset, column="ministerio_obra", value=main_filter)

    if secondary_filter:
        if main_filter == "Obra/iglesia hija":
            filtered_dataset = filter_data(
                input_dataset=filtered_dataset, column="detalle_obra", value=secondary_filter
            )
        else:
            filtered_dataset = filter_data(
                input_dataset=dataset, column="número_de_documento", value=secondary_filter
            )


    exclude_rows = filtered_dataset.apoyos == True
    number_inscriptions = filtered_dataset.loc[~exclude_rows, "número_de_documento"].drop_duplicates().size
    number_offerings = filtered_dataset.loc[exclude_rows, "número_de_documento"].drop_duplicates().size
    total_value = filtered_dataset["total_abono"].sum()
    total_payments = filtered_dataset.loc[~exclude_rows, "total_abono"].sum()
    total_offerings = filtered_dataset.loc[exclude_rows, "total_abono"].sum()
    st.markdown(f"""
    ### Total de personas inscritas

    El total de inscritos es {number_inscriptions}

    El total de registros de apoyos es {number_offerings}

    ### Valor total recaudado

    El valor total recaudado es de ${total_value:,.0f}

    El valor total pagos de jóvenes es de ${total_payments:,.0f}

    El valor total de apoyos registrados es de ${total_offerings:,.0f}
    """)

    week_data = week_summary(input_dataset=filtered_dataset)
    person_dataset = person_summary(input_dataset=filtered_dataset[~exclude_rows])

    st.bar_chart(week_data)
    st.dataframe(person_dataset)
