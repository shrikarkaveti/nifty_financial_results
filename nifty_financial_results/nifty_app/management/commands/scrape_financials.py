import csv
from pathlib import Path
from django.core.management.base import BaseCommand
from nifty_app.models import Company, QuarterlyResult, AnnualResult
from nifty_app.scraper import scrape_financials
from datetime import date

class Command(BaseCommand):
    help = 'Scrape financial data from screener.in'

    def handle(self, *args, **options):
        # Path to CSV file in project root
        csv_path = Path(__file__).resolve().parents[3] / 'tickers.csv'
        try:
            with open(csv_path, 'r') as file:
                reader = csv.DictReader(file)
                if 'ticker' not in reader.fieldnames:
                    self.stdout.write(self.style.ERROR("CSV must have 'ticker' column"))
                    return
                tickers = [row['ticker'].strip().upper() for row in reader]
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"CSV file not found at {csv_path}"))
            return
        except csv.Error:
            self.stdout.write(self.style.ERROR("Invalid CSV format"))
            return
        
        for ticker in tickers:
            self.stdout.write(f"Scraping {ticker}...")
            data = scrape_financials(ticker)
            if not data:
                self.stdout.write(f"No data for {ticker}")
                continue

            # Create or get Company
            company, created = Company.objects.get_or_create(ticker=ticker)
            if created:
                self.stdout.write(f"Created company: {ticker}")

            # Save QuarterlyResult records
            for index in range(len(data['quarterly'][0])):
                try:
                    QuarterlyResult.objects.get_or_create(
                        company=company,
                        month=data['quarterly'][0][index],
                        year=data['quarterly'][1][index],
                        sales=data['quarterly'][2][index],
                        expenses=data['quarterly'][3][index],
                        pbt=data['quarterly'][4][index],
                        pat=data['quarterly'][5][index],
                        eps=data['quarterly'][6][index],
                        date_reported=date.today()
                    )
                except Exception as e:
                    self.stdout.write(f"Error saving Quaterly Results - {ticker} {data['quarterly'][0][index]}-{data['quarterly'][1][index]}: {e}")

            # Save AnnualResult records
            for index in range(len(data['annual'][0])):
                try:
                    AnnualResult.objects.get_or_create(
                        company=company,
                        # month=data['annual'][0][index],
                        year=data['annual'][1][index],
                        sales=data['annual'][2][index],
                        expenses=data['annual'][3][index],
                        pbt=data['annual'][4][index],
                        pat=data['annual'][5][index],
                        eps=data['annual'][6][index],
                        date_reported=date.today()
                    )
                except Exception as e:
                    self.stdout.write(f"Error saving Annual Results - {ticker} {data['annual'][0][index]}-{data['annual'][1][index]}: {e}")
            self.stdout.write(f"Finished scraping {ticker}")
