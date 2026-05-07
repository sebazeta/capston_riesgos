import streamlit as st
import pandas as pd
from awesome_table import AwesomeTable
from awesome_table.column import Column, ColumnDType

st.title("Test Table")
df = pd.DataFrame({
    "ID": [1, 2],
    "Name": ["A", "B"],
    "Action": ["btn1", "btn2"]
})

st.write("Session State before:", st.session_state)

columns = [
    Column("ID", label="ID"),
    Column("Name", label="Name"),
    Column("Action", label="Action", dtype=ColumnDType.ICONBUTTON, icon="fa-solid fa-play")
]

res = AwesomeTable(df, columns=columns, key="my_table")
st.write("Res type:", type(res))
st.write("Session State after:", st.session_state)
