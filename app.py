import streamlit as st
import pandas as pd
import base64

# ---------- BACKGROUND ----------
def set_bg(image_file):
    try:
        with open(image_file, "rb") as f:
            data = f.read()
        encoded = base64.b64encode(data).decode()

        st.markdown(f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{encoded}");
            background-size: cover;
            background-position: center;
        }}
        </style>
        """, unsafe_allow_html=True)
    except:
        pass

set_bg("background.png")

# ---------- TITLE ----------
st.title("Excel Reconciliation Tool")

# ---------- FILE UPLOAD ----------
file1 = st.file_uploader("Upload First Excel File", type=["xlsx"])
file2 = st.file_uploader("Upload Second Excel File", type=["xlsx"])

if file1 and file2:
    df1_original = pd.read_excel(file1)
    df2_original = pd.read_excel(file2)

    df1 = df1_original.copy()
    df2 = df2_original.copy()

    st.write("File 1 Columns:", df1.columns.tolist())
    st.write("File 2 Columns:", df2.columns.tolist())

    cols1 = st.multiselect("Select columns from File 1", df1.columns)
    cols2 = st.multiselect("Select columns from File 2", df2.columns)

    if st.button("Compare"):

        if len(cols1) != len(cols2):
            st.error("Select same number of columns")
        else:
            # ---------- CLEAN (CASE INSENSITIVE) ----------
            for c1, c2 in zip(cols1, cols2):
                df1[c1] = df1[c1].astype(str).str.strip().str.lower()
                df2[c2] = df2[c2].astype(str).str.strip().str.lower()

            # ---------- AMOUNT ----------
            amount_col1 = cols1[-1]
            amount_col2 = cols2[-1]

            df1[amount_col1] = pd.to_numeric(df1[amount_col1], errors='coerce')
            df2[amount_col2] = pd.to_numeric(df2[amount_col2], errors='coerce')

            # ---------- SPLIT KEYS ----------
            key_cols1 = cols1[:-1]
            key_cols2 = cols2[:-1]

            # Create key without amount
            df1["key"] = df1[key_cols1].astype(str).agg('|'.join, axis=1)
            df2["key"] = df2[key_cols2].astype(str).agg('|'.join, axis=1)

            matched_idx_1 = []
            matched_idx_2 = []

            # ---------- MATCHING ----------
            for i, row1 in df1.iterrows():
                possible_matches = df2[df2["key"] == row1["key"]]

                for j, row2 in possible_matches.iterrows():
                    if pd.notna(row1[amount_col1]) and pd.notna(row2[amount_col2]):
                        if abs(row1[amount_col1] - row2[amount_col2]) <= 1:
                            matched_idx_1.append(i)
                            matched_idx_2.append(j)
                            break

            # ---------- RESULTS ----------
            matched = df1_original.loc[matched_idx_1]
            only_in_1 = df1_original.drop(matched_idx_1)
            only_in_2 = df2_original.drop(matched_idx_2)

            # ---------- OUTPUT ----------
            st.subheader("Only in File 1")
            st.write(only_in_1)

            st.subheader("Only in File 2")
            st.write(only_in_2)

            st.subheader("Matched Records")
            st.write(matched)

            # ---------- SUMMARY ----------
            st.subheader("Summary")
            st.write("Only in File 1:", len(only_in_1))
            st.write("Only in File 2:", len(only_in_2))
            st.write("Matched:", len(matched))

            # ---------- DOWNLOAD ----------
            def convert_df(df):
                return df.to_csv(index=False).encode('utf-8')

            st.download_button("Download Only in File 1", convert_df(only_in_1), "only_in_1.csv")
            st.download_button("Download Only in File 2", convert_df(only_in_2), "only_in_2.csv")
            st.download_button("Download Matched", convert_df(matched), "matched.csv")