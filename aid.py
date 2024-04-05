"""
Amazon Invoice Downloader

Usage:
  amazon-invoice-downloader.py \
    [--email=<email> --password=<password>] \
    [--year=<YYYY> | --date-range=<YYYYMMDD-YYYYMMDD>]
  amazon-invoice-downloader.py (-h | --help)

Login Options:
  --email=<email>          Amazon login email  [default: $AMAZON_EMAIL].
  --password=<password>    Amazon login password  [default: $AMAZON_PASSWORD].

Date Range Options:
  --date-range=<YYYYMMDD-YYYYMMDD>  Start and end date range
  --year=<YYYY>            Year, formatted as YYYY  [default: <CUR_YEAR>].

Options:
  -h --help                Show this screen.

Examples:
  amazon-invoice-downloader.py --year=2022  # This uses env vars $AMAZON_EMAIL and $AMAZON_PASSWORD
  amazon-invoice-downloader.py --date-range=20220101-20221231
  amazon-invoice-downloader.py --email=user@example.com --password=secret  # Defaults to current year
  amazon-invoice-downloader.py --email=user@example.com --password=secret --year=2022
  amazon-invoice-downloader.py --email=user@example.com --password=secret --date-range=20220101-20221231
"""

from amazon_invoice_downloader.__about__ import __version__

from playwright.sync_api import sync_playwright, TimeoutError
from datetime import datetime
import random
import time
import os
import sys
from docopt import docopt


def sleep():
    # Add human latency
    # Generate a random sleep time between 3 and 5 seconds
    sleep_time = random.uniform(2, 5)
    # Sleep for the generated time
    time.sleep(sleep_time)


def run(playwright, args):
    email = args.get('--email')
    if email == '$AMAZON_EMAIL':
        email = os.environ.get('AMAZON_EMAIL')

    password = args.get('--password')
    if password == '$AMAZON_PASSWORD':
        password = os.environ.get('AMAZON_PASSWORD')

    # Parse date ranges int start_date and end_date
    if args['--date-range']:
        start_date, end_date = args['--date-range'].split('-')
    elif args['--year'] != "<CUR_YEAR>":
        start_date, end_date = args['--year'] + "0101", args['--year'] + "1231"
    else:
        year = str(datetime.now().year)
        start_date, end_date = year + "0101", year + "1231"
    start_date = datetime.strptime(start_date, "%Y%m%d")
    end_date = datetime.strptime(end_date, "%Y%m%d")

    # Debug
    # print(email, password, start_date, end_date)

    # Ensure the location exists for where we will save our downloads
    target_dir = os.getcwd() + "/" + "downloads"
    os.makedirs(target_dir, exist_ok=True)

    # Create Playwright context with Chromium
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()

    page = context.new_page()
    page.goto("https://www.amazon.co.uk/")

    # Sometimes, we are interrupted by a bot check, so let the user solve it
    page.wait_for_selector('span >> text=Hello, sign in', timeout=0).click()

    if email:
        page.get_by_label("Email").click()
        page.get_by_label("Email").fill(email)
        page.get_by_role("button", name="Continue").click()

    if password:
        page.get_by_label("Password").click()
        page.get_by_label("Password").fill(password)
        page.get_by_label("Keep me signed in").check()
        page.click("#signInSubmit")

    
    page.wait_for_selector('a >> text=Returns & Orders', timeout=0).click()
    sleep()

    # Get a list of years from the select options
    select = page.query_selector('select#time-filter')
    years = select.inner_text().split("\n")  # skip the first two text options

    # Filter years to include only numerical years (YYYY)
    years = [year for year in years if year.isnumeric()]

    # Filter years to the include only the years between start_date and end_date inclusively
    years = [year for year in years if start_date.year <= int(year) <= end_date.year]
    years.sort(reverse=True)

    # Year Loop (Run backwards through the time range from years to pages to orders)
    for year in years:
        # Select the year in the order filter
        page.select_option('form[action="/your-orders/orders"] select#time-filter', value=f"year-{year}")
        sleep()

        # Page Loop
        first_page = True
        done = False
        while not done:
            # Go to the next page pagination, and continue downloading
            #   if there is not a next page then break
            try:
                if first_page:
                    first_page = False
                else:
                    #page.get_by_role("link", name="Next â†’").click()
                    next_page = page.query_selector('xpath=//a[contains(text(), "Next") and ancestor::*[contains(@class, "a-last")]]')
                    if next_page:
                        next_page.click()
                    else:
                        break
                        
                sleep()  # sleep after every page load
            except TimeoutError:
                # There are no more pages
                break

            # Order Loop
            order_cards = page.query_selector_all(".order.js-order-card")
            for order_card in order_cards:
                # Parse the order card to create the date and file_name
                spans = order_card.query_selector_all("span")
                date = datetime.strptime(spans[1].inner_text(), "%d %B %Y")
                total = spans[3].inner_text().replace("Â£", "").replace(",", "")
                orderid = spans[9].inner_text().replace("/", "")
                date_str = date.strftime("%Y%m%d")
                file_name = f"{target_dir}/{date_str}_{total}_amazon_{orderid}"

                if date > end_date:
                    continue
                elif date < start_date:
                    done = True
                    break

                if os.path.isfile(file_name):
                    print(f"File [{file_name}] already exists")
                else:
                    invoice_popover = order_card.query_selector('xpath=//a[contains(text(), "Invoice")]')
                    if invoice_popover:
                        invoice_popover.click()
                        sleep()

                        invoice_selector = 'xpath=//div[contains(@class, "a-popover-content") and not(contains(@style, "display: none"))]//a[contains(text(), "Invoice") and not(ancestor::*[contains(@style, "display: none")])]'
                        invoices = page.query_selector_all(invoice_selector)
                
                        # Download all invoices
                        i = 0
                        for invoice in invoices:
                            print(f"Invoice found for {date} with value Â£{total}")
                            href = invoice.get_attribute("href")
                            if ".pdf" in href:
                                i = i + 1
                                invoice_number = f'{i:03}'
                                link = "https://www.amazon.co.uk" + href
                                
                                # Start waiting for the download
                                with page.expect_download() as download_info:
                                    # Perform the action that initiates download
                                    invoice.click(modifiers=["Alt"])
                                    sleep()
                                download = download_info.value
                                
                                # Wait for the download process to complete and save the downloaded file somewhere
                                download.save_as(file_name + "-" + invoice_number + ".pdf")

    # Close the browser
    context.close()
    browser.close()


args = docopt(__doc__)
with sync_playwright() as playwright:
    run(playwright, args)
