import re
import requests
from bs4 import BeautifulSoup

MONTH_MAP = {'Mar': 3, 'Jun': 6, 'Sep': 9, 'Dec': 12}
sym = 'BAJAJ-AUTO'

def get_quarterly_headers(thead):
    # returns list of tuples with month and year (Ex. [('Sep', '2022'), ('Dec', '2022'), ('Mar', '2023')])
    return re.findall(r"(...).(\d+)", thead)

def get_quarter_rows(trow):
    # returns list of numbers in float format (Ex. [10203.0, 9319.0, 8929.0, 10312.0])
    table_data = "\n".join(map(str, trow.find_all('td')[1:]))
    num_data = list(map(float, [i.replace(',', '') for i in re.findall(r">(.*)<", table_data)]))
    return num_data

# Fetch Webpage Source Code
page_source_code = requests.get(f"https://www.screener.in/company/{sym}/consolidated/")

if (page_source_code.status_code == 200):
    print(f"{sym} - HTTPS Response: Success")
else:
    print(f"{sym} - HTTPS Response: Failed")

# Parsing using BeautifulSoup
soup = BeautifulSoup(page_source_code.content, 'html.parser')

# Getting Quarterly Financials
quarters_element = soup.find_all(id='quarters')[0]

# thead is used to make the key and quarter-year details
quarters_thead = quarters_element.find_all('thead')[0]
quarters_tbody = quarters_element.find_all('tbody')[0]

# Getting Rows from table body
# trow {0: 'Sales', 1: 'Expenses', 7: 'PBT', 9: 'PAT', 10: 'EPS'}
quarter_rows = quarters_tbody.find_all('tr')

# print(get_quarter_rows(quarter_rows[10]))
print(quarter_rows[10])
