import streamlit as st
import pandas as pd
import base64

# ---------- BACKGROUND IMAGE ----------
def set_bg(image_file):
    with open(image_file, "rb") as f:
        data = f.read()
    encoded = base64.b64encode(data).decode()

    page_bg = f"""
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{encoded}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
    }}
    </style>
    """
    st.markdown(page_bg, unsafe_allow_html=True)

# Call background
set_bg("background.png")

# ---------- TITLE ----------
st.title("Excel Reconciliation Tool")

# ---------- FILE UPLOAD ----------
file1 = st.file_uploader("Upload First Excel File", type=["xlsx"])
file2 = st.file_uploader("Upload Second Excel File", type=["xlsx"])

if file1 and file2:
    df1 = pd.read_excel(file1)
    df2 = pd.read_excel(file2)

    st.write("File 1 Columns:", df1.columns.tolist())
    st.write("File 2 Columns:", df2.columns.tolist())

    cols1 = st.multiselect("Select columns from File 1", df1.columns)
    cols2 = st.multiselect("Select columns from File 2", df2.columns)

    if st.button("Compare"):

        if len(cols1) != len(cols2):
            st.error("Select same number of columns")
        else:
            # CLEAN DATA
            for c1, c2 in zip(cols1, cols2):
                df1[c1] = df1[c1].astype(str).str.strip().str.lower()
                df2[c2] = df2[c2].astype(str).str.strip().str.lower()

                df1[c1] = df1[c1].str.replace(r'\.0$', '', regex=True)
                df2[c2] = df2[c2].str.replace(r'\.0$', '', regex=True)

                # Try numeric conversion + rounding
                try:
                    df1[c1] = pd.to_numeric(df1[c1]).round(0)
                    df2[c2] = pd.to_numeric(df2[c2]).round(0)
                except:
                    pass

            # CREATE KEY
            df1["key"] = df1[cols1].astype(str).agg('|'.join, axis=1)
            df2["key"] = df2[cols2].astype(str).agg('|'.join, axis=1)

            # MATCHING
            only_in_1 = df1[~df1["key"].isin(df2["key"])]
            only_in_2 = df2[~df2["key"].isin(df1["key"])]
            matched = df1[df1["key"].isin(df2["key"])]

            # RESULTS
            st.subheader("Only in File 1")
            st.write(only_in_1)

            st.subheader("Only in File 2")
            st.write(only_in_2)

            st.subheader("Matched Records")
            st.write(matched)

            # SUMMARY
            st.subheader("Summary")
            st.write("Only in File 1:", len(only_in_1))
            st.write("Only in File 2:", len(only_in_2))
            st.write("Matched:", len(matched))

            # DOWNLOAD
            def convert_df(df):
                return df.to_csv(index=False).encode('utf-8')

            st.download_button("Download Only in File 1", convert_df(only_in_1), "only_in_1.csv")
            st.download_button("Download Only in File 2", convert_df(only_in_2), "only_in_2.csv")
            st.download_button("Download Matched", convert_df(matched), "matched.csv")