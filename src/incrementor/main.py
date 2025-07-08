from dataops import portal
from dataops.models import CensusAPIEndpoint
import polars as pl

# take a look at incrementing the url years

# take a look at the data catalog
# api data catalog:  https://api.census.gov/data/


endpoints = (
    portal.fetch_data()
    .collect()
    .with_columns(pl.col("endpoint").struct.unnest().alias("endpoint"))
)

# for each endpoint in endpoints use CensusAPIEndpoint.from_url()
# construct a new instance but with a new year

print(endpoints)
