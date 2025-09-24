# Generate Owner Data Tool

A tool that automates the process of enriching your input files with detailed **owner information** from a local `bottoms_up` database.  This tool is designed to help users quickly match records by **ID, phone number, or serial number**, and automatically populate additional fields such as owner name, address, city, state, category, and other metadata.   It handles multiple input files at once and ensures data consistency by expanding matches using contact group IDs. The processed results are saved in the same format as the input, making it easy to continue working with your enriched data without manual effort.  

With a simple graphical interface, you can select your files and database, track progress in real-time, and generate accurate enriched outputs efficiently.

---

![Version](https://img.shields.io/badge/version-1.0.1-ffab4c?style=for-the-badge&logo=python&logoColor=white)
![Python](https://img.shields.io/badge/python-3.9%2B-273946?style=for-the-badge&logo=python&logoColor=ffab4c)
![Status](https://img.shields.io/badge/status-active-273946?style=for-the-badge&logo=github&logoColor=ffab4c)

---

## 📌 Features

- GUI for easy file selection and execution
- Processes `.xlsx` and `.csv` files
- Supports multiple input file formats (`id`, `phone_number`, `BTP SN`)
- Normalizes phone numbers (removes non-digits, trims leading `1`)
- Enriches rows with owner details from the `bottoms_up` database
- Outputs results in the same format as input (`.xlsx` or `.csv`)
- Progress bar and wait-popup during processing
- Automatic folder setup for:
  - `files_to_process/`
  - `results/`
  - `bu_database/`

---

## 📂 Project Structure

<pre>
project/
│
├── .github/                 # GitHub workflows and automation
│   └── workflows/           # Environment variables and CI/CD logic
│       └── build.yml        # Build workflow
├── main.py                  # Core processing logic
├── gui.py                   # GUI application
├── version.txt              # Stores current app version (e.g., v1.0.0)
├── files_to_process/        # Place input files here (.xlsx or .csv)
├── results/                 # Generated enriched output files
├── bu_database/             # Place your .db database file here (exactly one required)
└── requirements.txt         # Python dependencies
</pre>

---

## 🚀 Installation and Setup

1. **Clone the Repository**
```bash
git clone https://github.com/yourusername/generate-owner-data-tool.git
cd generate-owner-data-tool
```
2. **Install Dependencies**

```bash
pip install -r requirements.txt
```
Note: Tkinter comes with Python by default, but customtkinter is an external library.
3. **To build the .exe (Windows only):**

```bash
pyinstaller --onefile --windowed --name generate_owner_data gui.py --clean --add-data "main.py;." --hidden-import pandas --hidden-import tqdm
```
The .exe will be created in the dist/ folder.

---

## 🖥️ User Guide

1. **First-Time Setup**

   When you open the tool for the first time, it will automatically create three (3) folders:
   - `files_to_process` – place files to be cleaned here
   - `bu_database` – place the latest version of the bottoms-up database (.db) here
   - `results` – cleaned files will be saved here

     > 💡 **Tip:** Place the `.exe` file in the location where you want these folders to be stored **before** running it the first time.

2. **Opening the Tool**

   Double-click the program file (or `.exe`) to start it.

3. **Checking Your Files**

   When the tool opens, it will display a list of:
   - **Database file(s)** in the `bu_database` folder  
     - Supported file type: `.db` (SQLite database)  
     - There must be **exactly one** `.db` file for the tool, otherwise it will encounter an error during processing.
     - The database must contain the following columns:
       - id
       - contact_group_id
       - phone1
       - phone2
       - phone3
       - phone4
       - phone5
       - Serial Number
       - date_created
       - Owner
       - Input: Address
       - Input: City
       - Input: State
       - County
       - State
       - Contact Type
       - \# of Interests
       - is_latest_offer
       - Category
       - Total Value - Low ($)
       - md_address
       - md_city
       - md_state
    - **Input files** currently in the `files_to_process` folder
      - Supported file types: Excel (`.xlsx`) and CSV (`.csv`) only
      - Each file must contain **exactly one of the following columns**, which will be used as the lookup value for processing:
          - id
          - BTP SN
          - phone_number
      - Only **one lookup column per file** will be used to match against the database.
      - The tool can process multiple input files, but each file must follow this rule.
- If the list is wrong or empty:
  - Click **Open bu_database folder** or **Open files_to_process folder** to check and update the file/s.
  - Then click **Refresh** in the tool to reload the lists.

> 📝 **Note:**
> - Only files inside the input folder will be processed. 
> - Make sure both database and input files are up-to-date.


4. **Running the Cleaning**

   - Ensure the list shows the correct files and the database contains only **one** `.db` file.  

     The **GENERATE RESULTS** button will be **enabled** only when:  
     - At least **one valid input file** (.xlsx or .csv) exists in the `files_to_process` folder.  
     - At least **one valid database file** (.db) exists in the `bu_database` folder.  
     - The tool is **not currently processing** another file.  

     The button will be **disabled** if:  
     - No database file exists.  
     - No valid input files exist.  
     - Both database and input files are missing.  
     - Processing is currently running.  

   - Click **GENERATE RESULTS**.  
   - A **Processing** window will appear — do **not** close it.  
   - Wait until you see the message: **Processing finished successfully!**

5. **Getting the Results**
   
   - When processing is done, you will be asked if you want to open the output folder.  
   - Click **Yes** to view your cleaned files.  
   - The cleaned files will always be saved in the `results` folder with the prefix `output_`.  

> ⚠️ **Important Notes**
> * Do **not** close the “Processing” popup before it finishes — this might interrupt the process. 
> * Do **not** run the tool twice at the same time.
> * Any file that is not an Excel (.xlsx) or CSV (.csv) file will be ignored.
> * Ensure there is **exactly one .db file** in the `bu_database` folder, or the process will fail.

