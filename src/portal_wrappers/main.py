from sodapy import Socrata
from dotenv import load_dotenv
import os
import logging

# import sys
import polars as pl


logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s] - %(levelname)s - %(message)s"
)

# environmental variables/secrets
logging.info("Attempting to load environmental variables.")
if load_dotenv():
    CENSUS_API_KEY = os.getenv("CENSUS_API_KEY")
    TABLE_SOURCE = os.getenv("TABLE_SOURCE")
    TABLE_TARGET = os.getenv("TABLE_TARGET")
    USER = os.getenv("USER")
    PASSWORD = os.getenv("PASSWORD")
    TOKEN = os.getenv("TOKEN")
    DOMAIN = os.getenv("DOMAIN")
    logging.info("Environmental variables successfully loaded.")
else:
    logging.critical("Environmental variables cannot be loaded.")

# helper functions


def fetch_portal_data(
    resource: str = TABLE_SOURCE,
    domain: str = DOMAIN,
    token: str = TOKEN,
    user: str = USER,
    password: str = PASSWORD,
    lazy: bool = True,
) -> pl.LazyFrame | pl.DataFrame:
    """
    Retrieve portal data as polars dataframe.
    Environmental variables are used as defaults unless otherwise specified.
    """

    with Socrata(domain, token, user, password) as client:
        data = client.get_all(resource)
        data = pl.LazyFrame(data)

    if not lazy:
        return data.collect()

    return data
