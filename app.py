import streamlit as st
import pandas as pd

st.title("2B vs Tally Reconciliation Tool")

# Upload files
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
            st.error("Select same number of columns and keep Amount last")
            st.stop()

        # Copy data
        df1 = df1_org.copy()
        df2 = df2_org.copy()

        # Clean (case insensitive match)
        for c1, c2 in zip(cols1, cols2):
            df1[c1] = df1[c1].astype(str).str.strip().str.lower()
            df2[c2] = df2[c2].astype(str).str.strip().str.lower()

        # Amount column (last selected)
        amt1 = cols1[-1]
        amt2 = cols2[-1]

        df1[amt1] = pd.to_numeric(df1[amt1], errors='coerce')
        df2[amt2] = pd.to_numeric(df2[amt2], errors='coerce')

        # Create key (excluding amount)
        key_cols1 = cols1[:-1]
        key_cols2 = cols2[:-1]

        df1["key"] = df1[key_cols1].apply(lambda x: '|'.join(x.astype(str)), axis=1)
        df2["key"] = df2[key_cols2].apply(lambda x: '|'.join(x.astype(str)), axis=1)

        matched_1 = set()
        matched_2 = set()

        # Matching logic
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

        # Final outputs
        matched = df1_org.loc[list(matched_1)]          # ONLY 2B
        only_2b = df1_org.drop(list(matched_1))         # Unmatched 2B
        only_tally = df2_org.drop(list(matched_2))      # Unmatched Tally

        # Display
        st.subheader("Matched (2B Format)")
        st.write(matched)

        st.subheader("Only in 2B")
        st.write(only_2b)

        st.subheader("Only in Tally")
        st.write(only_tally)

        # Summary
        st.subheader("Summary")
        st.write("Matched:", len(matched))
        st.write("Only in 2B:", len(only_2b))
        st.write("Only in Tally:", len(only_tally))