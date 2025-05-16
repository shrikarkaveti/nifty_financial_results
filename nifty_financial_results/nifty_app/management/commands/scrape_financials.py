import csv
from pathlib import Path
from django.core.management.base import BaseCommand
from nifty_app.models import Company, QuarterlyResult, AnnualResult
from nifty_app.scraper import scrape_financials, InvalidFinancialDataError
import logging
from datetime import date, datetime
import time

# Configure logging
log_dir = Path(__file__).resolve().parents[4] / 'logs'
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    filename=log_dir / 'scraper.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S %Z'
)

class Command(BaseCommand):
    help = 'Scrape financial data from screener.in'

    def add_arguments(self, parser):
        parser.add_argument('--silent', action='store_true', help='Suppress console output')

    def handle(self, *args, **options):
        start_time = time.time()
        silent = options['silent']
        logger = logging.getLogger(__name__)
        logger.info("Starting scraper run")

        csv_path = Path(__file__).resolve().parents[4] / 'tickers.csv'
        try:
            with open(csv_path, 'r') as file:
                reader = csv.DictReader(file)
                if 'ticker' not in reader.fieldnames:
                    msg = "CSV must have 'ticker' column"
                    logger.error(msg)
                    if not silent:
                        self.stdout.write(self.style.ERROR(msg))
                    return
                tickers = [row['ticker'].strip().upper() for row in reader]
        except FileNotFoundError:
            msg = f"CSV file not found at {csv_path}"
            logger.error(msg)
            if not silent:
                self.stdout.write(self.style.ERROR(msg))
            return
        except csv.Error:
            msg = "Invalid CSV format"
            logger.error(msg)
            if not silent:
                self.stdout.write(self.style.ERROR(msg))
            return

        if not tickers:
            msg = "No tickers found in CSV"
            logger.warning(msg)
            if not silent:
                self.stdout.write(self.style.WARNING(msg))
            return

        msg = f"Loaded {len(tickers)} tickers from CSV"
        logger.info(msg)
        if not silent:
            self.stdout.write(msg)

        for ticker in tickers:
            msg = f"Scraping {ticker}..."
            logger.info(msg)
            if not silent:
                self.stdout.write(msg)

            try:
                data = scrape_financials(ticker)
                if not data or not data.get('quarterly') or not data.get('annual'):
                    msg = f"No data for {ticker}"
                    logger.warning(msg)
                    if not silent:
                        self.stdout.write(msg)
                    continue
            except InvalidFinancialDataError as e:
                msg = f"Invalid data for {ticker}: {e}"
                logger.error(msg)
                if not silent:
                    self.stdout.write(self.style.ERROR(msg))
                continue
            except Exception as e:
                msg = f"Error scraping {ticker}: {e}"
                logger.error(msg)
                if not silent:
                    self.stdout.write(self.style.ERROR(msg))
                continue

            company, created = Company.objects.get_or_create(ticker=ticker)
            if created:
                msg = f"Created company: {ticker}"
                logger.info(msg)
                if not silent:
                    self.stdout.write(msg)

            # Validate quarterly data lengths
            quarterly_lengths = [len(data['quarterly'][i]) for i in range(7)]
            if len(set(quarterly_lengths)) != 1:
                msg = f"Inconsistent quarterly data lengths for {ticker}: {quarterly_lengths}"
                logger.error(msg)
                if not silent:
                    self.stdout.write(self.style.ERROR(msg))
                continue

            quarterly_count = 0
            for index in range(len(data['quarterly'][0])):
                try:
                    month = data['quarterly'][0][index]
                    if not 1 <= month <= 12:
                        msg = f"Invalid month '{month}' for {ticker} quarterly data.  Month should be between 1 and 12."
                        logger.error(msg)
                        if not silent:
                            self.stdout.write(self.style.ERROR(msg))
                        continue
                    if not isinstance(month, int) or month < 1 or month > 12:
                        msg = f"Invalid month {month} for {ticker} quarterly data"
                        logger.error(msg)
                        if not silent:
                            self.stdout.write(self.style.ERROR(msg))
                        continue

                    year = data['quarterly'][1][index]
                    sales = data['quarterly'][2][index]
                    expenses = data['quarterly'][3][index]
                    pbt = data['quarterly'][4][index]
                    pat = data['quarterly'][5][index]
                    eps = data['quarterly'][6][index]

                    if None in (sales, expenses, pbt, pat):
                        msg = f"Skipping incomplete quarterly data for {ticker} {month}-{year}"
                        logger.warning(msg)
                        if not silent:
                            self.stdout.write(msg)
                        continue

                    obj, created = QuarterlyResult.objects.get_or_create(
                        company=company,
                        month=month,
                        year=year,
                        defaults={
                            'sales': sales,
                            'expenses': expenses,
                            'pbt': pbt,
                            'pat': pat,
                            'eps': eps,
                            'date_reported': date.today()
                        }
                    )
                    if not created:
                        fields = ['sales', 'expenses', 'pbt', 'pat', 'eps']
                        changed = False
                        changed_fields = []
                        for field in fields:
                            scraped_value = locals()[field]
                            existing_value = getattr(obj, field)
                            if scraped_value != existing_value:
                                setattr(obj, field, scraped_value)
                                changed = True
                                changed_fields.append(field)
                        if changed:
                            obj.date_reported = date.today()
                            obj.save()
                            msg = f"Updated {ticker} {month}-{year}: {changed_fields} changed"
                            logger.info(msg)
                            if not silent:
                                self.stdout.write(msg)
                        else:
                            msg = f"Skipped {ticker} {month}-{year}: data unchanged"
                            logger.info(msg)
                            if not silent:
                                self.stdout.write(msg)
                    else:
                        quarterly_count += 1
                except Exception as e:
                    msg = f"Error saving quarterly {ticker} {month}-{year}: {e}"
                    logger.error(msg)
                    if not silent:
                        self.stdout.write(msg)

            # Validate annual data lengths
            annual_lengths = [len(data['annual'][i]) for i in range(7)]
            if len(set(annual_lengths)) != 1:
                msg = f"Inconsistent annual data lengths for {ticker}: {annual_lengths}"
                logger.error(msg)
                if not silent:
                    self.stdout.write(self.style.ERROR(msg))
                continue

            annual_count = 0
            for index in range(len(data['annual'][1])):
                try:
                    year = data['annual'][1][index]
                    sales = data['annual'][2][index]
                    expenses = data['annual'][3][index]
                    pbt = data['annual'][4][index]
                    pat = data['annual'][5][index]
                    eps = data['annual'][6][index]

                    if None in (sales, expenses, pbt, pat):
                        msg = f"Skipping incomplete annual data for {ticker} {year}"
                        logger.warning(msg)
                        if not silent:
                            self.stdout.write(msg)
                        continue

                    obj, created = AnnualResult.objects.get_or_create(
                        company=company,
                        year=year,
                        defaults={
                            'sales': sales,
                            'expenses': expenses,
                            'pbt': pbt,
                            'pat': pat,
                            'eps': eps,
                            'date_reported': date.today()
                        }
                    )
                    if not created:
                        fields = ['sales', 'expenses', 'pbt', 'pat', 'eps']
                        changed = False
                        changed_fields = []
                        for field in fields:
                            scraped_value = locals()[field]
                            existing_value = getattr(obj, field)
                            if scraped_value != existing_value:
                                setattr(obj, field, scraped_value)
                                changed = True
                                changed_fields.append(field)
                        if changed:
                            obj.date_reported = date.today()
                            obj.save()
                            msg = f"Updated {ticker} {year}: {changed_fields} changed"
                            logger.info(msg)
                            if not silent:
                                self.stdout.write(msg)
                        else:
                            msg = f"Skipped {ticker} {year}: data unchanged"
                            logger.info(msg)
                            if not silent:
                                self.stdout.write(msg)
                    else:
                        annual_count += 1
                except Exception as e:
                    msg = f"Error saving annual {ticker} {year}: {e}"
                    logger.error(msg)
                    if not silent:
                        self.stdout.write(msg)

            msg = f"Saved {quarterly_count} quarterly and {annual_count} annual records for {ticker}"
            logger.info(msg)
            if not silent:
                self.stdout.write(msg)
            msg = f"Finished scraping {ticker}"
            logger.info(msg)
            if not silent:
                self.stdout.write(msg)

        msg = f"Scraper run completed in {time.time() - start_time:.2f} seconds"
        logger.info(msg)
        if not silent:
            self.stdout.write(msg)