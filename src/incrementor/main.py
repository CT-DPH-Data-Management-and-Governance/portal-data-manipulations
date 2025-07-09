from dataops import portal
from dataops.models import CensusAPIEndpoint
import polars as pl
from datetime import datetime as dt
# import urllib

# take a look at incrementing the url years

# take a look at the data catalog
# api data catalog:  https://api.census.gov/data/

# for each endpoint in endpoints use CensusAPIEndpoint.from_url()
# construct a new instance but with a new year


def snapshot_acs_source():
    raw = portal.fetch_data()

    orig_endpoints = (
        raw.with_columns(
            pl.col("endpoint").struct.unnest().alias("endpoint"),
            pl.col("row_id").cast(pl.UInt32),
        )
        .sort(pl.col("row_id"))
        .collect()
    )

    max_row_id = orig_endpoints.select("row_id").max().item()

    return {
        "orig": orig_endpoints,
        "max_id": max_row_id,
        "new_index_start": max_row_id + 1,
    }


snapshot = snapshot_acs_source()

df = snapshot["orig"]


def extend_acs(data: pl.DataFrame | pl.LazyFrame, years: list):
    api_census_base = "https://api.census.gov/data/"
    base_len = 28  # len(api_census_base)

    base = data.lazy().with_columns(
        pl.lit(api_census_base).alias("begin"),
        pl.col("endpoint").str.slice(base_len, 4).alias("year"),
        pl.col("endpoint")
        .str.slice(
            base_len + 4,
        )
        .alias("end"),
    )

    years_df = pl.DataFrame({"new_year": years}).lazy()

    expanded = base.filter(pl.col("active").eq("1")).join(years_df, how="cross")

    now = dt.now().strftime("%Y-%m-%d %H:%M:%S")

    new = (
        expanded.filter(pl.col("year").cast(pl.Int64).ne(pl.col("new_year")))
        .drop("row_id")
        .with_row_index("row_id", offset=snapshot["new_index_start"])
        .with_columns(
            pl.concat_str([pl.col("begin"), pl.col("new_year"), pl.col("end")]).alias(
                "endpoint"
            ),
            pl.col("new_year").alias("year"),
            pl.lit(now).alias("date_added"),
            pl.lit("").alias("date_last_pulled"),
        )
        .drop(["begin", "new_year", "end"])
        .select(
            ["row_id", "endpoint", "active", "year", "date_added", "date_last_pulled"]
        )
        .collect()
    )

    # TODO add year to data
    stacked = pl.concat([data, new])

    return stacked
