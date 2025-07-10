from dataops import portal
import polars as pl
from datetime import datetime as dt


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
        "df": orig_endpoints,
        "id_start": max_row_id + 1,
    }


def extend_acs(snapshot: dict, years: list[int]):
    api_census_base = "https://api.census.gov/data/"
    base_len = 28  # len(api_census_base)

    data = snapshot["df"]

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
        .with_row_index("row_id", offset=snapshot["id_start"])
        .with_columns(
            pl.concat_str([pl.col("begin"), pl.col("new_year"), pl.col("end")]).alias(
                "endpoint"
            ),
            pl.lit(now).alias("date_added"),
            pl.lit("1970-01-01 00:00:00").alias("date_last_pulled"),
        )
        .drop(["begin", "year", "new_year", "end"])
        .select(["row_id", "endpoint", "active", "date_added", "date_last_pulled"])
        .collect()
    )

    stacked = pl.concat([data, new])

    return stacked


def time_table(years: list[int] = None) -> list[int]:
    if years is None:
        end = dt.today().year - 1
        start = end - 4

        return list(range(start, end))

    return years


def main():
    years = time_table()
    snapshot = snapshot_acs_source()

    huh = extend_acs(snapshot, years)
    print(huh)


if __name__ == "__main__":
    main()
