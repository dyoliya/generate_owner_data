# -------------------------ABOUT --------------------------

# pyinstaller --onefile --noconsole --name generate_owner_data gui.py
# Tool: Generate Owner Data
# Developer: dyoliya
# Created: 2025-04-25

# © 2025 dyoliya. All rights reserved.

# ---------------------------------------------------------

import os
import pandas as pd
import re
import sqlite3
from tqdm import tqdm


phone_cols = ['phone1', 'phone2', 'phone3', 'phone4', 'phone5']

# ----------------------- FUNCTIONS -----------------------
# load bottoms-up database
def load_bottoms_up_db(bottoms_up_folder, logger=print):
    db_files = [f for f in os.listdir(bottoms_up_folder) if f.endswith(".db")]
    if not db_files:
        logger(f"No .db file found in {bottoms_up_folder}")
        raise RuntimeError(f"No .db file found in {bottoms_up_folder}")
    elif len(db_files) > 1:
        logger(f"Multiple .db files found in {bottoms_up_folder}, expected only one.")
        raise RuntimeError(f"Multiple .db files found in {bottoms_up_folder}, expected only one.")

    bottoms_up_db_path = os.path.join(bottoms_up_folder, db_files[0])

    # Load bottoms_up table from SQLite database and standardize id columns
    conn = sqlite3.connect(bottoms_up_db_path)
    bottoms_up = pd.read_sql_query(
        """
        SELECT 
            id,
            contact_group_id,
            CAST(phone1 AS TEXT) AS phone1,
            CAST(phone2 AS TEXT) AS phone2,
            CAST(phone3 AS TEXT) AS phone3,
            CAST(phone4 AS TEXT) AS phone4,
            CAST(phone5 AS TEXT) AS phone5,
            [Serial Number],
            date_created,
            Owner,
            [Input: Address],
            [Input: City],
            [Input: State],
            County,
            State,
            [Contact Type],
            [# of Interests],
            is_latest_offer,
            Category,
            [Total Value - Low ($)],
            md_address,
            md_city,
            md_state
        FROM bottoms_up
        """,
        conn
    )

    conn.close()

    # validate required columns
    required_cols_bottoms_up = [
        "id", "contact_group_id", "phone1", "phone2", "phone3", "phone4", "phone5", "Serial Number",
        "date_created", "Owner", "Input: Address", "Input: City", "Input: State",
        "County", "State", "Contact Type", "# of Interests", "is_latest_offer", "Category",
        "Total Value - Low ($)", "md_address", "md_city", "md_state"
        ]
    missing_cols = [c for c in required_cols_bottoms_up if c not in bottoms_up.columns]
    if missing_cols:
        logger(f"❌ Database error: Missing required columns {missing_cols}")
        raise RuntimeError(f"Database error: Missing required columns {missing_cols}")

    bottoms_up['id'] = bottoms_up['id'].astype(str).fillna('').str.upper().str.strip()
    for col in phone_cols:
        bottoms_up[col] = bottoms_up[col].apply(normalize_phone)

    return bottoms_up

def normalize_phone(phone):
    if not isinstance(phone, str):
        return ""
    # Keep only digits
    digits = re.sub(r"\D", "", phone)
    # Remove leading 1 if 11 digits and starts with 1
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    return digits
    
# Helper function to separate by rows
def separate_by_rows(df):
    if 'id' in df.columns:
        df = df.assign(**{'id': df['id'].astype(str).str.split('|')}).explode('id')
    elif 'BTP SN' in df.columns:
        df = df.assign(**{'BTP SN': df['BTP SN'].astype(str).str.split('|')}).explode('BTP SN')
    elif 'phone_number' in df.columns:
        df = df.assign(**{'phone_number': df['phone_number'].astype(str).str.split(',')}).explode('phone_number')
    return df

def get_matching_ids(bottoms_up_df, id=None, phone=None, sn=None):
    results = []
    if id:
        id = id.upper().strip()
        mask = (bottoms_up_df['id'] == id)
        results.extend(bottoms_up_df.loc[mask, 'id'].dropna().unique().tolist())

    if phone:
        phone = phone.upper().strip()
        mask = bottoms_up_df[phone_cols].eq(phone).any(axis=1)
        results.extend(bottoms_up_df.loc[mask, 'id'].dropna().unique().tolist())

    if sn:
        sn = sn.upper().strip()
        mask = (bottoms_up_df['Serial Number'] == sn)
        results.extend(bottoms_up_df.loc[mask, 'id'].dropna().unique().tolist())

    # remove duplicates
    return list(set(results))


# Helper function to get owner data
def enrich_row(row, matched_row=None):
    """Return a new row enriched with bottoms_up data if matched_row is given,
       otherwise fill enrichment columns with blanks."""
    new_row = row.copy()
    cols_to_copy = [
        "id", "date_created", "Owner", "Input: Address", "Input: City", "Input: State",
        "County", "State", "Contact Type", "# of Interests", "contact_group_id",
        "is_latest_offer", "Category", "Total Value - Low ($)",
        "md_address", "md_city", "md_state"
    ]
    for col in cols_to_copy:
        if matched_row is not None:
            new_row[col] = matched_row.get(col, "")
        else:
            new_row[col] = ""
    return new_row

# ------------------ MAIN SCRIPT ------------------
def main(input_folder="files_to_process", output_folder="results", bottoms_up_folder="bu_database", logger=print, progress_callback=None):
    for folder in [input_folder, output_folder, bottoms_up_folder]:
        os.makedirs(folder, exist_ok=True)

    bottoms_up = load_bottoms_up_db(bottoms_up_folder, logger=logger)
    if bottoms_up is None: 
        return

    # Process input files if any
    files = [f for f in os.listdir(input_folder) if f.endswith((".xlsx", ".csv"))]
    if not files:
        logger(f"No input files found in '{input_folder}'. Please add files to process.")
        return
    
    total_rows = 0
    file_row_counts = {}
    skipped_files = []

    for filename in files:
        file_path = os.path.join(input_folder, filename)
        if filename.endswith(".xlsx"):
            df = pd.read_excel(file_path, dtype=str)
        elif filename.endswith(".csv"):
            df = pd.read_csv(file_path, dtype=str)
        else:
            continue

        df = separate_by_rows(df)

        if 'phone_number' in df.columns:
            df['phone_number'] = df['phone_number'].fillna('').apply(normalize_phone)
        elif 'id' in df.columns:
            df = df[df['id'].notna() & (df['id'].str.strip().str.lower() != 'nan') & (df['id'].str.strip() != '')]
        elif 'BTP SN' in df.columns:
            df = df[df['BTP SN'].notna() & (df['BTP SN'].str.strip().str.lower() != 'nan') & (df['BTP SN'].str.strip() != '')]
            df['BTP SN'] = df['BTP SN'].str.replace(r'(?i)^TX-?', '', regex=True).str.strip()


        file_row_counts[filename] = len(df)
        total_rows += len(df)

    if total_rows == 0:
        logger("No rows to process.")
        return
    
    processed_rows = 0
    for filename in files:
        file_path = os.path.join(input_folder, filename)

        # Detect file type
        if filename.endswith(".xlsx"):
            df = pd.read_excel(file_path, dtype=str)
            output_ext = ".xlsx"
        elif filename.endswith(".csv"):
            df = pd.read_csv(file_path, dtype=str)
            output_ext = ".csv"
        else:
            continue

        df = separate_by_rows(df)

        if 'phone_number' in df.columns:
            df['phone_number'] = df['phone_number'].fillna('').apply(normalize_phone)
        elif 'id' in df.columns:
            df = df[df['id'].notna() & (df['id'].str.strip().str.lower() != 'nan') & (df['id'].str.strip() != '')]
        elif 'BTP SN' in df.columns:
            df = df[df['BTP SN'].notna() & (df['BTP SN'].str.strip().str.lower() != 'nan') & (df['BTP SN'].str.strip() != '')]
            df['BTP SN'] = df['BTP SN'].str.replace(r'(?i)^TX-?', '', regex=True).str.strip()

        required_cols_input = ["id", "phone_number", "BTP SN"]
        present_cols = [c for c in required_cols_input if c in df.columns]

        if not present_cols:
            msg = f"{filename}: missing required columns {required_cols_input}"
            if len(files) == 1:
                # Only one file to process → fatal
                logger(f"\nError: {msg}")
                raise RuntimeError(msg)
            else:
                # Multiple files → just skip
                skipped_files.append(filename)
                logger(f"\nSkipping {msg}")
                continue

        result_rows = []
        row_iterator = tqdm(df.iterrows(), total=len(df), desc=f"Processing {filename}")
        for _, row in row_iterator:
            if "id" in df.columns:
                id = row['id']
                row_iterator.set_description(f"id {id}")
                ids = set(get_matching_ids(bottoms_up, id=id))

            elif "phone_number" in df.columns:
                phone = row['phone_number']
                row_iterator.set_description(f"Phone {phone}")
                ids = set(get_matching_ids(bottoms_up, phone=phone))

            elif "BTP SN" in df.columns:
                sn = row['BTP SN']
                row_iterator.set_description(f"SN {sn}")
                ids = set(get_matching_ids(bottoms_up, sn=sn))      

            # Expand ids using contact_group_id
            additional_ids = set()
            for match_id in ids:
                group_id = bottoms_up.loc[bottoms_up['id'] == match_id, 'contact_group_id'].dropna()
                if not group_id.empty:
                    group = group_id.values[0]
                    group_matches = bottoms_up[bottoms_up['contact_group_id'] == group]['id'].dropna().tolist()
                    additional_ids.update(group_matches)
            all_ids = ids.union(additional_ids)

            if all_ids:
                    # Duplicate row for each matched ID
                for matched_id in all_ids:
                    matched_row = bottoms_up[bottoms_up['id'] == matched_id]
                    if not matched_row.empty:
                        matched = matched_row.iloc[0]
                        result_rows.append(enrich_row(row, matched))
            else:
                # Always include row, just blank enrichment columns
                result_rows.append(enrich_row(row, None))

            # Row-level progress update
            processed_rows += 1
            progress_fraction = processed_rows / total_rows
            progress_percentage = int(progress_fraction * 100)
            if progress_callback:
                progress_callback(progress_fraction, filename)

        # Save output in the same format as input
        if result_rows:
                output_df = pd.DataFrame(result_rows)
                
                if "date_created" in output_df.columns:
                    output_df["date_created"] = pd.to_datetime(
                        output_df["date_created"], errors="coerce"
                    ).dt.strftime("%Y-%m-%d").fillna("")

                output_path = os.path.join(output_folder, f"output_{os.path.splitext(filename)[0]}{output_ext}")
                if output_ext == ".xlsx":
                    output_df.to_excel(output_path, index=False)
                else:
                    output_df.to_csv(output_path, index=False)

    if skipped_files:
        summary_msg = "The following files were skipped due to missing required columns (`id`, `BTP SN`, or `phone_number`):\n" + "\n".join(skipped_files)
        logger("\n" + summary_msg)

        if len(files) > 1:
            try:
                from tkinter import messagebox
                messagebox.showwarning("Skipped Files", summary_msg)
            except:
                pass
            
if __name__ == "__main__":
    main()
