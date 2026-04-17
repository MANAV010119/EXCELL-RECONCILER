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

        if len(cols1) != len(cols2) or len(cols1) < 2:
            st.error("Select same number of columns and include amount as last column")
            st.stop()

        # ---------- CLEAN ----------
        df1 = df1_org.copy()
        df2 = df2_org.copy()

        for c1, c2 in zip(cols1, cols2):
            df1[c1] = df1[c1].astype(str).str.strip().str.lower()
            df2[c2] = df2[c2].astype(str).str.strip().str.lower()

        amt1 = cols1[-1]
        amt2 = cols2[-1]

        df1[amt1] = pd.to_numeric(df1[amt1], errors='coerce')
        df2[amt2] = pd.to_numeric(df2[amt2], errors='coerce')

        # ---------- KEY ----------
        key_cols1 = cols1[:-1]
        key_cols2 = cols2[:-1]

        df1["key"] = df1[key_cols1].apply(lambda x: '|'.join([str(i) for i in x if pd.notna(i)]), axis=1)
        df2["key"] = df2[key_cols2].apply(lambda x: '|'.join([str(i) for i in x if pd.notna(i)]), axis=1)

        # ---------- PARTIAL MATCH (DUPLICATES) ----------
        partial_keys = set()

        vc1 = df1["key"].value_counts()
        vc2 = df2["key"].value_counts()

        for k in vc1.index:
            if k in vc2.index and vc1[k] > 1 and vc2[k] > 1:
                partial_keys.add(k)

        partial_df = []

        for k in partial_keys:
            for _, row in df1_org[df1["key"] == k].iterrows():
                r = row.to_dict()
                r["Source"] = "2B"
                partial_df.append(r)

            for _, row in df2_org[df2["key"] == k].iterrows():
                r = row.to_dict()
                r["Source"] = "Tally"
                partial_df.append(r)

        partial_df = pd.DataFrame(partial_df)

        # Remove partial from main
        df1 = df1[~df1["key"].isin(partial_keys)]
        df2 = df2[~df2["key"].isin(partial_keys)]

        df1_org_f = df1_org.loc[df1.index]
        df2_org_f = df2_org.loc[df2.index]

        # ---------- FULL MATCH ----------
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

        # ---------- FINAL OUTPUT ----------
        matched = df1_org.loc[list(matched_1)]   # ONLY 2B
        only_2b = df1_org_f.drop(list(matched_1))
        only_tally = df2_org.drop(list(matched_2))  # remove matched tally

        # ---------- DISPLAY ----------
        st.subheader("Matched (2B Data Only)")
        st.write(matched)

        st.subheader("Partially Matched (With Source)")
        st.write(partial_df)

        st.subheader("Only in 2B")
        st.write(only_2b)

        st.subheader("Only in Tally")
        st.write(only_tally)

        # ---------- SUMMARY ----------
        st.subheader("Summary")
        st.write("Matched:", len(matched))
        st.write("Partial:", len(partial_df))
        st.write("Only 2B:", len(only_2b))
        st.write("Only Tally:", len(only_tally))