
## Script Responsibilities

### download_data.py

Downloads country metadata and ten economic/education indicators, parses records, and saves three JSON files. Existing output files are skipped.

Custom functions:

| Function | Responsibility |
|---|---|
| `_get_with_retry()` | Send requests with retries for timeouts and selected HTTP errors. |
| `fetch_wb_data()` | Retrieve paginated indicator records. |
| `fetch_wb_countries()` | Retrieve country metadata. |
| `is_valid_country()` | Check for a three-character alphabetic code; this is not a definitive country/aggregate filter. |
| `parse_wb_records()` | Reshape API records and convert year/value fields. |
| `save_json()` | Write records to JSON. |
| `main()` | Coordinate downloads and output-file checks. |

Other functions and methods used:

```python
print(), range(), len(), isinstance(), int(), float(), open()
load_dotenv(), requests.get(), time.sleep(), json.dump()
os.makedirs(), os.path.abspath(), os.path.join(), os.path.exists()
resp.raise_for_status(), resp.json()
.get(), .isalpha(), .append(), .extend(), .items()
```

### notebook.py

Performs database initialisation, ingestion, cleaning, transformation, exploratory analysis, visualisation, and Ridge Regression modelling.

The following are imported modules/packages, not function names:

- Standard library: `pathlib`, `os`, `sys`, `json`, `time`, `warnings`
- Data access: `requests`, `python-dotenv`, `PyMongo`, `psycopg2`, `SQLAlchemy`
- Data processing: `NumPy`, `pandas`
- Visualisation: `Matplotlib`, `Seaborn`, `Plotly`
- Machine learning: `scikit-learn`

No model-performance claims are made here; consult the notebook's evaluation outputs.

### dashboard.py

Connects to PostgreSQL and displays an interactive dashboard with filters for year range, region, and income group.

Custom functions:

| Function | Responsibility |
|---|---|
| `get_engine()` | Create and cache the PostgreSQL SQLAlchemy engine. |
| `load_merged()` | Load `merged_development_data`; cache results for 300 seconds. |
| `load_countries()` | Load `countries`; cache results for 300 seconds. |

Dashboard tabs:

1. Global Overview — world map and income-group summary.
2. Economic Trends — regional trends, rankings, distributions, and selected G7/BRICS comparisons.
3. Education Analysis — literacy, enrollment, and education expenditure.
4. Correlations — population-sized scatterplot, correlation heatmap, and unemployment comparison.
5. Country Deep Dive — country comparisons and latest-indicator summary.

The Ridge Regression model is part of the analysis workflow, not the supplied dashboard code.

Selected functions, methods, and decorators:

```python
os.getenv(), warnings.filterwarnings(), load_dotenv()
create_engine(), text(), connect()
int(), sorted(), max(), min(), len(), dict()
str.replace(), str.title()
pd.read_sql(), pd.Categorical()
dropna(), unique(), tolist(), isin(), copy(), sort_values()
groupby(), last(), nunique(), mean(), reindex(), round()
query(), nlargest(), corr(), set_index(), rename()
update_layout(), update_traces()
st.cache_resource, st.cache_data()
st.set_page_config(), st.title(), st.caption(), st.error(), st.stop()
st.sidebar.header(), st.sidebar.slider(), st.sidebar.multiselect()
st.divider(), st.columns(), st.warning(), metric(), st.tabs()
st.subheader(), st.selectbox(), st.plotly_chart(), st.dataframe()
st.slider(), st.select_slider(), st.multiselect(), st.info()
px.choropleth(), px.line(), px.bar(), px.box()
px.area(), px.scatter(), px.imshow()
```

Here, `metric()` is called on Streamlit column objects. The lists include methods and decorators as well as functions.

## Data Source

World Bank Indicators API: https://api.worldbank.org/v2
