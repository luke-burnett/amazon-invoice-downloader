# Amazon Invoice Downloader (UK)
Forked to work with Amazon UK and deal with some more complex use cases when finding and saving invoices. Majority of code remains as written by David C Wang (thank you!). Also kept as a plain script rather than using Hatch - personal preference.

[![PyPI - Version](https://img.shields.io/pypi/v/amazon-invoice-downloader.svg)](https://pypi.org/project/amazon-invoice-downloader)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/amazon-invoice-downloader.svg)](https://pypi.org/project/amazon-invoice-downloader)

-----

**Table of Contents**

- [Installation](#installation)
- [License](#license)

## What it does


This program `amazon-invoice-downloader.py` is a utility script that uses the [Playwright](https://playwright.dev/) library to spin up a Chromium instance and automate the process of downloading invoices for Amazon purchases within a specified date range. The script logs into Amazon using the provided email and password, navigates to the "Returns & Orders" section, and retrieves invoices for the specified year or date range.

The user can provide their Amazon login credentials either through command line arguments (--email=<email> --password=<password>) or as environment variables ($AMAZON_EMAIL and $AMAZON_PASSWORD).

The script accepts the date range either as a specific year (--year=<YYYY>) or as a date range (--date-range=<YYYYMMDD-YYYYMMDD>). If no date range is provided, the script defaults to the current year.

Once the invoices are retrieved, they are saved as PDF files in a local "downloads" directory. The filename of each PDF is formatted as `YYYYMMDD_<total>_amazon_<orderid>.pdf`, where YYYYMMDD is the date of the order, total is the total amount of the order (with dollar signs and commas removed), and orderid is the unique Amazon order ID.

The program has a built-in "human latency" function, sleep(), to mimic human behavior by introducing random pauses between certain actions. This can help prevent the script from being detected and blocked as a bot by Amazon.

The script will skip downloading a file if it already exists in the `./downloads` directory.

## Installation

```console
pip install amazon-invoice-downloader
playwright install
```

## Usage

When running this program, Amazon may detect you are automation and introduce CAPTCHA's or make you login again.  Just do so, and once successfully logged in, the script will continue.

```console

Usage:
  aid.py \
    [--email=<email> --password=<password>] \
    [--year=<YYYY> | --date-range=<YYYYMMDD-YYYYMMDD>]
  aid.py (-h | --help)

Login Options:
  --email=<email>          Amazon login email  [default: $AMAZON_EMAIL].
  --password=<password>    Amazon login password  [default: $AMAZON_PASSWORD].

Date Range Options:
  --date-range=<YYYYMMDD-YYYYMMDD>  Start and end date range
  --year=<YYYY>            Year, formatted as YYYY  [default: <CUR_YEAR>].

Options:
  -h --help                Show this screen.

Examples:
  python aid.py --year=2022  # This uses env vars $AMAZON_EMAIL and $AMAZON_PASSWORD
  python aid.py --date-range=20220101-20221231
  python aid.py --email=user@example.com --password=secret  # Defaults to current year
  python aid.py --email=user@example.com --password=secret --year=2022
  python aid.py --email=user@example.com --password=secret --date-range=20220101-20221231
```


## License

`amazon-invoice-downloader` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
