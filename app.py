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
st.title("Excel Reconciliation Tool (2B vs Tally)")

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

        if len(cols1) != len(cols2):
            st.error("Select same number of columns")
        else:
            df1 = df1_org.copy()
            df2 = df2_org.copy()

            # CLEAN
            for c1, c2 in zip(cols1, cols2):
                df1[c1] = df1[c1].astype(str).str.strip().str.lower()
                df2[c2] = df2[c2].astype(str).str.strip().str.lower()

            amt1 = cols1[-1]
            amt2 = cols2[-1]

            df1[amt1] = pd.to_numeric(df1[amt1], errors='coerce')
            df2[amt2] = pd.to_numeric(df2[amt2], errors='coerce')

            key_cols1 = cols1[:-1]
            key_cols2 = cols2[:-1]

            df1["key"] = df1[key_cols1].astype(str).agg('|'.join, axis=1)
            df2["key"] = df2[key_cols2].astype(str).agg('|'.join, axis=1)

            # ---------- DUPLICATE PARTIAL MATCH ----------
            partial_keys = set()

            key_count_1 = df1["key"].value_counts()
            key_count_2 = df2["key"].value_counts()

            for key in key_count_1.index:
                if key in key_count_2.index:
                    if key_count_1[key] > 1 and key_count_2[key] > 1:
                        partial_keys.add(key)

            partial_df1 = df1_org[df1["key"].isin(partial_keys)]
            partial_df2 = df2_org[df2["key"].isin(partial_keys)]

            # REMOVE partial from main data
            df1 = df1[~df1["key"].isin(partial_keys)]
            df2 = df2[~df2["key"].isin(partial_keys)]

            df1_org_filtered = df1_org.loc[df1.index]
            df2_org_filtered = df2_org.loc[df2.index]

            matched_1 = set()
            matched_2 = set()

            # ---------- FULL MATCH ----------
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

            matched = df1_org.loc[list(matched_1)]
            only1 = df1_org_filtered.drop(list(matched_1))
            only2 = df2_org_filtered.drop(list(matched_2))

            # ---------- DISPLAY ----------
            st.subheader("Fully Matched (2B Format)")
            st.write(matched)

            st.subheader("Partially Matched (Duplicate Keys)")

            st.write("From 2B (Sheet 1)")
            st.write(partial_df1)

            st.write("From Tally (Sheet 2)")
            st.write(partial_df2)

            st.subheader("Only in 2B")
            st.write(only1)

            st.subheader("Only in Tally")
            st.write(only2)

            # ---------- SUMMARY ----------
            st.subheader("Summary")
            st.write("Full Match:", len(matched))
            st.write("Partial Match:", len(partial_df1))
            st.write("Only in 2B:", len(only1))
            st.write("Only in Tally:", len(only2))