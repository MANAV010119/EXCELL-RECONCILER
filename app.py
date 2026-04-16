import streamlit as st
import pandas as pd

st.title("Excel Reconciliation Tool")

file1 = st.file_uploader("Upload First Excel File", type=["xlsx"])
file2 = st.file_uploader("Upload Second Excel File", type=["xlsx"])

if file1 and file2:
    df1 = pd.read_excel(file1)
    df2 = pd.read_excel(file2)

    st.write("File 1 Columns:", df1.columns.tolist())
    st.write("File 2 Columns:", df2.columns.tolist())

    cols1 = st.multiselect("Select key columns from File 1", df1.columns)
    cols2 = st.multiselect("Select key columns from File 2", df2.columns)

    if st.button("Compare"):

        if len(cols1) != len(cols2):
            st.error("Select same number of columns in both files")
        else:
            # 🔥 Clean data
            for c1, c2 in zip(cols1, cols2):
                df1[c1] = df1[c1].astype(str).str.strip().str.lower()
                df2[c2] = df2[c2].astype(str).str.strip().str.lower()

                df1[c1] = df1[c1].str.replace(r'\.0$', '', regex=True)
                df2[c2] = df2[c2].str.replace(r'\.0$', '', regex=True)

            # 🔥 Create combined key
            df1["key"] = df1[cols1].agg('|'.join, axis=1)
            df2["key"] = df2[cols2].agg('|'.join, axis=1)

            # Debug view
            st.write("Sample Keys File1:", df1["key"].head())
            st.write("Sample Keys File2:", df2["key"].head())

            only_in_1 = df1[~df1["key"].isin(df2["key"])]
            only_in_2 = df2[~df2["key"].isin(df1["key"])]
            matched = df1[df1["key"].isin(df2["key"])]

            st.subheader("Only in File 1")
            st.write(only_in_1)

            st.subheader("Only in File 2")
            st.write(only_in_2)

            st.subheader("Matched")
            st.write(matched)

            st.subheader("Summary")
            st.write("Only in File 1:", len(only_in_1))
            st.write("Only in File 2:", len(only_in_2))
            st.write("Matched:", len(matched))
