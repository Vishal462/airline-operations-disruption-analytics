# Data

## Source

Flight-level data is sourced from the U.S. Department of Transportation Bureau of Transportation Statistics (BTS) Marketing Carrier On-Time Performance dataset.\
👉[BTS On‑Time Performance Fields](https://www.transtats.bts.gov/Fields.asp?gnoyr_VQ=FGK)

The project uses monthly data from:

**January 2024 – December 2025**

The BTS source contains flight-level information covering carriers, airports, scheduled and actual operations, cancellations, diversions, and delay causes. The bundled BTS documentation identifies this as the Marketing Carrier On-Time Performance dataset and describes the monthly file naming convention. 
For additional details, see the [Data README](data/README.html).

## Airport Metadata

Airport-level metadata is sourced from the FAA National Transportation Atlas Database (NTAD) Aviation Facilities dataset.\
👉[FAA NTAD Aviation Facilities](https://geodata.bts.gov/datasets/usdot::aviation-facilities/about)

Selected attributes include:

- Airport ID
- Airport name
- City
- State
- Latitude
- Longitude
- Elevation
- Airport status
- Ownership type
- Facility/use information
- ICAO code

## Data Availability

Raw BTS ZIP files and processed Parquet datasets are **not included in this repository** because of their size.

The Python ingestion scripts can be used to reproduce the data preparation workflow.

The SQL analysis outputs included in the repository are derived from the processed flight dataset.
