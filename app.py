import streamlit as st
import pandas as pd
import base64

# ---------- BACKGROUND ----------
def set_bg(image_file):
    try:
        with open(image_file, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        st.markdown(f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{encoded}");
            background-size: cover;
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

    st.write("File 1 Columns:", df1_original.columns.tolist())
    st.write("File 2 Columns:", df2_original.columns.tolist())

    cols1 = st.multiselect("Select columns from File 1", df1_original.columns)
    cols2 = st.multiselect("Select columns from File 2", df2_original.columns)

    if st.button("Compare"):

        if len(cols1) != len(cols2):
            st.error("Select same number of columns")
        else:
            # ---------- CLEAN COPIES (DO NOT TOUCH ORIGINAL) ----------
            df1 = df1_original.copy()
            df2 = df2_original.copy()

            for c1, c2 in zip(cols1, cols2):
                df1[c1] = df1[c1].astype(str).str.strip().str.lower()
                df2[c2] = df2[c2].astype(str).str.strip().str.lower()

            # ---------- AMOUNT ----------
            amt1 = cols1[-1]
            amt2 = cols2[-1]

            df1[amt1] = pd.to_numeric(df1[amt1], errors='coerce')
            df2[amt2] = pd.to_numeric(df2[amt2], errors='coerce')

            matched_idx_1 = []
            matched_idx_2 = []

            # ---------- MATCHING (SIMPLE & RELIABLE) ----------
            for i, r1 in df1.iterrows():
                for j, r2 in df2.iterrows():

                    # Match all columns except amount
                    other_match = True
                    for c1, c2 in zip(cols1[:-1], cols2[:-1]):
                        if str(r1[c1]) != str(r2[c2]):
                            other_match = False
                            break

                    if not other_match:
                        continue

                    # Amount tolerance check
                    if pd.notna(r1[amt1]) and pd.notna(r2[amt2]):
                        if abs(r1[amt1] - r2[amt2]) <= 1:
                            matched_idx_1.append(i)
                            matched_idx_2.append(j)
                            break

            # ---------- FINAL OUTPUT (ORIGINAL DATA) ----------
            matched = df1_original.loc[matched_idx_1]
            only_in_1 = df1_original.drop(matched_idx_1)
            only_in_2 = df2_original.drop(matched_idx_2)

            # ---------- DISPLAY ----------
            st.subheader("Matched Records")
            st.write(matched)

            st.subheader("Only in File 1")
            st.write(only_in_1)

            st.subheader("Only in File 2")
            st.write(only_in_2)

            # ---------- SUMMARY ----------
            st.subheader("Summary")
            st.write("Matched:", len(matched))
            st.write("Only in File 1:", len(only_in_1))
            st.write("Only in File 2:", len(only_in_2))

            # ---------- DOWNLOAD ----------
            def convert_df(df):
                return df.to_csv(index=False).encode('utf-8')

            st.download_button("Download Matched", convert_df(matched), "matched.csv")
            st.download_button("Download Only in File 1", convert_df(only_in_1), "only_in_1.csv")
            st.download_button("Download Only in File 2", convert_df(only_in_2), "only_in_2.csv")