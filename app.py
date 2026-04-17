import streamlit as st
import pandas as pd

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="2B vs Tally Reconciliation Tool", layout="wide")

# ---------- BACKGROUND (ONLY ADDITION) ----------
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(to right, #f7f8fc, #dbeafe);
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("2B vs Tally Reconciliation Tool")

# ---------- FILE UPLOAD ----------
file1 = st.file_uploader("Upload 2B File", type=["xlsx"])
file2 = st.file_uploader("Upload Tally File", type=["xlsx"])

if file1 and file2:
    df1_org = pd.read_excel(file1)
    df2_org = pd.read_excel(file2)

    st.write("2B Columns:", df1_org.columns.tolist())
    st.write("Tally Columns:", df2_org.columns.tolist())

    cols1 = st.multiselect("Select columns from 2B", df1_org.columns)
    cols2 = st.multiselect("Select columns from Tally", df2_org.columns)

    if st.button("Compare"):

        # ---------- VALIDATION ----------
        if len(cols1) != len(cols2) or len(cols1) < 2:
            st.error("Select same number of columns and keep Amount as last column")
            st.stop()

        # ---------- COPY ----------
        df1 = df1_org.copy()
        df2 = df2_org.copy()

        # ---------- CLEAN ----------
        for c1, c2 in zip(cols1, cols2):
            df1[c1] = df1[c1].astype(str).str.strip().str.lower()
            df2[c2] = df2[c2].astype(str).str.strip().str.lower()

        # ---------- AMOUNT ----------
        amt1 = cols1[-1]
        amt2 = cols2[-1]

        df1[amt1] = pd.to_numeric(df1[amt1], errors='coerce')
        df2[amt2] = pd.to_numeric(df2[amt2], errors='coerce')

        # ---------- KEY ----------
        key_cols1 = cols1[:-1]
        key_cols2 = cols2[:-1]

        if len(key_cols1) == 0 or len(key_cols2) == 0:
            st.error("Select at least 1 key column and 1 amount column")
            st.stop()

        # SAFE KEY FUNCTION
        def make_key(row):
            return '|'.join([str(i).strip().lower() for i in row if pd.notna(i)])

        df1["key"] = df1[key_cols1].apply(make_key, axis=1)
        df2["key"] = df2[key_cols2].apply(make_key, axis=1)

        # ---------- MATCHING ----------
        matched_1 = set()
        matched_2 = set()

        for i, r1 in df1.iterrows():
            if i in matched_1:
                continue

            for j, r2 in df2.iterrows():
                if j in matched_2:
                    continue

                if r1["key"] != r2["key"]:
                    continue

                if pd.notna(r1[amt1]) and pd.notna(r2[amt2]):
                    if abs(r1[amt1] - r2[amt2]) <= 1:
                        matched_1.add(i)
                        matched_2.add(j)
                        break

        # ---------- OUTPUT ----------
        matched = df1_org.loc[list(matched_1)]      # ONLY 2B
        only_2b = df1_org.drop(list(matched_1))     # Unmatched 2B
        only_tally = df2_org.drop(list(matched_2))  # Unmatched Tally

        # ---------- DISPLAY ----------
        st.subheader("Matched (2B Format)")
        st.write(matched)

        st.subheader("Only in 2B")
        st.write(only_2b)

        st.subheader("Only in Tally")
        st.write(only_tally)

        # ---------- SUMMARY ----------
        st.subheader("Summary")
        st.write("Matched:", len(matched))
        st.write("Only in 2B:", len(only_2b))
        st.write("Only in Tally:", len(only_tally))