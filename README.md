# Global Socioeconomic Development Analytics

This is my project in NCI APDV module repeat attempt 
## Project Description

The project analyses global socioeconomic development using World Bank data covering GDP per capita, education enrollment, adult literacy, unemployment, life expectancy, FDI, and population. Data is ingested programmatically, stored in MongoDB Atlas and PostgreSQL, cleaned and transformed, then visualised through an interactive Streamlit dashboard with Plotly charts. A Ridge Regression model is included to predict GDP per capita.

---

## Folder Structure

```
Project/
    notebook.ipynb          Main analysis notebook (Sections 1 to 11)
    dashboard.py            Streamlit interactive dashboard
    download_data.py        Script to download raw data from World Bank API
    requirements.txt        Python dependencies
    .env                    Database credentials (not committed to version control)
    dataset/                Raw JSON data files
    plots/                  Exported Plotly HTML charts
```

---

## Setup Instructions

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment variables

Create a `.env` file in the project root with the following variables:

```
MONGO_URI=your_mongodb_connection_string
PG_HOST=your_postgres_host
PG_PORT=5432
PG_USER=your_postgres_user
PG_PASSWORD=your_postgres_password
PG_DB=your_database_name
```

### 3. Download raw data 
```bash
python download_data.py
```

### 4. Run the notebook

Open `notebook.ipynb` in Jupyter or VS Code and run all cells in order. The notebook will:

- Initialise MongoDB and PostgreSQL databases and tables
- Ingest raw data from JSON files and World Bank API into MongoDB
- Store raw records into PostgreSQL
- Retrieve data from MongoDB, clean and transform it
- Store processed data back into PostgreSQL
- Perform EDA, statistical analysis, and visualizations
- Train and evaluate a Ridge Regression model
- Run MongoDB aggregation queries for insights

### 5. Launch the dashboard

```bash
streamlit run dashboard.py
```

---

## Databases Used

MongoDB Atlas is used to store raw semi-structured JSON documents for country metadata, economic indicators, and education indicators.

PostgreSQL is used to store both raw records and the final cleaned and processed dataset for analysis.

---

## Key Libraries

pandas, numpy, matplotlib, seaborn, plotly, streamlit, pymongo, psycopg2, SQLAlchemy, scikit-learn, scipy

---

## Datasets

All datasets are sourced from the World Bank Open Data API (https://data.worldbank.org/). Kaggle datasets are not used. Each dataset contains records for over 200 countries across multiple decades.

Indicators covered:
- GDP per capita (NY.GDP.PCAP.CD)
- Adult literacy rate (SE.ADT.LITR.ZS)
- Primary school enrollment (SE.PRM.ENRR)
- Secondary school enrollment (SE.SEC.ENRR)
- Tertiary school enrollment (SE.TER.ENRR)
- Government education expenditure (SE.XPD.TOTL.GD.ZS)
- Unemployment rate (SL.UEM.TOTL.ZS)
- Life expectancy (SP.DYN.LE00.IN)
- FDI net inflows (BX.KLT.DINV.CD.WD)
- Total population (SP.POP.TOTL)

---

## Notes

- Run the notebook fully before launching the dashboard so all database tables are populated.
- The .env file must be configured correctly before running any scripts.
- All chart files are saved in the plots/ folder as HTML files.

## Organisation interest

Exploring this project for your organisation?

[View my LinkedIn](https://linkedin.com/in/arjun-mohan-b57305341)

It will enable me to follow up. Thank you.
