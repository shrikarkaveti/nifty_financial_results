from enum import Enum
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, date

class Month(Enum):
    """Enum representing month names and their corresponding numbers."""
    Jan = 1
    Feb = 2
    Mar = 3
    Apr = 4
    May = 5
    Jun = 6
    Jul = 7
    Aug = 8
    Sep = 9
    Oct = 10
    Nov = 11
    Dec = 12

class InvalidFinancialDataError(Exception):
    """Raised when financial data is invalid (e.g., negative sales, malformed quarter)."""
    pass

class QuarterResult:
    def __init__(self, ticker):
        url = f"https://www.screener.in/company/{ticker}/consolidated/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        self.soup = BeautifulSoup(response.content, 'html.parser')
        quarters_section = self.soup.find(id="quarters")
        if not quarters_section:
            raise InvalidFinancialDataError(f"No quarters section found for {ticker}")
        self.table_header = str(quarters_section.thead)
        self.table_body = quarters_section.tbody.find_all('tr')

        # Quarter Result Header Pattern
        self.quarter_header_pattern = r'''<thead>
<tr>
<th class=\"text\"></th>
<th class=\"(.*)\">
            (.*?) (.*?)
            
          </th>
<th class=\"(.*)\">
            (.*?) (.*?)
            
          </th>
<th class=\"(.*)\">
            (.*?) (.*?)
            
          </th>
<th class=\"(.*)\">
            (.*?) (.*?)
            
          </th>
<th class=\"(.*)\">
            (.*?) (.*?)
            
          </th>
<th class=\"(.*)\">
            (.*?) (.*?)
            
          </th>
<th class=\"(.*)\">
            (.*?) (.*?)
            
          </th>
<th class=\"(.*)\">
            (.*?) (.*?)
            
          </th>
<th class=\"(.*)\">
            (.*?) (.*?)
            
          </th>
<th class=\"\">
            (.*?) (.*?)
            
          </th>
<th class=\"(.*)\">
            (.*?) (.*?)
            
          </th>
<th class=\"(.*)\">
            (.*?) (.*?)
            
          </th>
<th class=\"(.*)\">
            (.*?) (.*?)
            
          </th>
</tr>
</thead>'''

        # Button Pattern Followed by Sales, Expenses and PAT
        self.button_pattern = r'''<tr class=\"(.*)\">
<td class=\"text\">
<button class=\"button-plain\" onclick=\"(.*)\">
                  (.*) <span class=\"blue-icon\">(.*)</span>
</button>
</td>
<td class=\"(.*)\">(.*?)</td>
<td class=\"(.*)\">(.*?)</td>
<td class=\"(.*)\">(.*?)</td>
<td class=\"(.*)\">(.*?)</td>
<td class=\"(.*)\">(.*?)</td>
<td class=\"(.*)\">(.*?)</td>
<td class=\"(.*)\">(.*?)</td>
<td class=\"(.*)\">(.*?)</td>
<td class=\"(.*)\">(.*?)</td>
<td class=\"(.*)\">(.*?)</td>
<td class=\"(.*)\">(.*?)</td>
<td class=\"(.*)\">(.*?)</td>
<td class=\"(.*)\">(.*?)</td>
</tr>'''

        # Non Button Pattern Followed by PBT and EPS
        self.non_button_pattern = r'''<tr class=\"(.*)\">
<td class=\"text\">
              
                (.*)
              
            </td>
<td class=\"(.*)\">(.*?)</td>
<td class=\"\">(.*?)</td>
<td class=\"\">(.*?)</td>
<td class=\"\">(.*?)</td>
<td class=\"(.*)\">(.*?)</td>
<td class=\"\">(.*?)</td>
<td class=\"\">(.*?)</td>
<td class=\"\">(.*?)</td>
<td class=\"(.*)\">(.*?)</td>
<td class=\"\">(.*?)</td>
<td class=\"\">(.*?)</td>
<td class=\"\">(.*?)</td>
<td class=\"(.*)\">(.*?)</td>
</tr>'''

    def get_header(self):
        match_table_header = re.match(self.quarter_header_pattern, self.table_header)
        quarter_header_month = match_table_header.group(2, 5, 8, 11, 14, 17, 20, 23, 26, 28, 31, 34, 37)
        quarter_header_month_number = []
        for month_str in quarter_header_month:
            try:
                month_number = Month[month_str].value
                quarter_header_month_number.append(month_number)
            except KeyError:
                quarter_header_month_number.append(None)  # Or handle invalid months differently
        quarter_header_year = match_table_header.group(3, 6, 9, 12, 15, 18, 21, 24, 27, 29, 32, 35, 38)

        return [list(quarter_header_month_number), list(quarter_header_year)]
    
    # [0] (Quarter Result Index) Sales - 0 (Soup Index)
    # [1] Expenses - 1
    # [2] PBT - 7
    # [3] PAT - 9
    # [4] EPS - 10
    
    def get_sales(self):
        """
        Extracts sales data from the table body.

        Returns:
            list: A list of integers representing sales data.

        Raises:
            TypeError: If `quarter table_body` is not a list or its first element is not a string.
            AttributeError: If `quarter button_pattern` is not a valid regex pattern or is None.
            IndexError: If `quarter table_body` is empty or the regex match fails to extract the required groups.
            ValueError: If the extracted sales data cannot be converted to integers.
        """
        try:
            if not isinstance(self.table_body, list):
                raise TypeError("quarter table_body must be a list.")
            sales = str(self.table_body[0])  # Access the first element
        except IndexError:
            raise IndexError("quarter table_body is empty.")
        except TypeError:
            raise TypeError("The first element of quarter table_body must be a string.")

        try:
            match_sales = re.match(self.button_pattern, sales)
        except AttributeError:
            raise AttributeError("quarter button_pattern must be a valid regex pattern and cannot be None.")

        if not match_sales:
            raise ValueError(f"Regex pattern {self.button_pattern} did not match the sales string: {sales}")

        try:
            sales_data = [int(i.replace(',', '')) for i in match_sales.group(6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30)]
        except ValueError as e:
            raise ValueError(f"Could not convert extracted sales data to integers: {e}")
        except IndexError:
            raise IndexError("Regex pattern did not extract the expected number of sales data points.")

        return sales_data
    
    def get_expenses(self):
        """
        Extracts expenses data from the table body.

        Returns:
            list: A list of integers representing expenses data.

        Raises:
            TypeError: If `quarters.table_body` is not a list or its second element is not a string.
            AttributeError: If `quarters.button_pattern` is not a valid regex pattern or is None.
            IndexError: If `quarters.table_body` has fewer than two elements or the regex match fails.
            ValueError: If the extracted expenses data cannot be converted to integers.
        """
        try:
            if not isinstance(self.table_body, list):
                raise TypeError("quarters.table_body must be a list.")
            expenses = str(self.table_body[1])  # Access the second element
        except IndexError:
            raise IndexError("quarters.table_body does not have enough elements.")
        except TypeError:
            raise TypeError("The elements of quarters.table_body must be strings.")

        try:
            match_expenses = re.match(self.button_pattern, expenses)
        except AttributeError:
            raise AttributeError("quarters.button_pattern must be a valid regex pattern and cannot be None.")

        if not match_expenses:
            raise ValueError(f"Regex pattern {self.button_pattern} did not match the expenses string: {expenses}")

        try:
            expenses_data = [int(i.replace(',', '')) for i in match_expenses.group(6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30)]
        except ValueError as e:
            raise ValueError(f"Could not convert extracted expenses data to integers: {e}")
        except IndexError:
            raise IndexError("Regex pattern did not extract the expected number of expenses data points.")

        return expenses_data
        
    def get_pbt(self):
        """
        Extracts profit before tax (PBT) data from the table body.

        Returns:
            list: A list of integers representing PBT data.

        Raises:
            TypeError: If `quarters.table_body` is not a list or its eighth element is not a string.
            AttributeError: If `quarters.non_button_pattern` is not a valid regex pattern or is None.
            IndexError: If `quarters.table_body` has fewer than eight elements or the regex match fails.
            ValueError: If the extracted PBT data cannot be converted to integers.
        """
        try:
            if not isinstance(self.table_body, list):
                raise TypeError("quarters.table_body must be a list.")
            profit_before_tax = str(self.table_body[7])  # Access the eighth element
        except IndexError:
            raise IndexError("quarters.table_body does not have enough elements.")
        except TypeError:
            raise TypeError("The elements of quarters.table_body must be strings.")

        try:
            match_pbt = re.match(self.non_button_pattern, profit_before_tax)
        except AttributeError:
            raise AttributeError("quarters.non_button_pattern must be a valid regex pattern and cannot be None.")

        if not match_pbt:
            raise ValueError(f"Regex pattern {self.non_button_pattern} did not match the PBT string: {profit_before_tax}")

        try:
            pbt_data = [int(i.replace(',', '')) for i in match_pbt.group(4, 5, 6, 7, 9, 10, 11, 12, 14, 15, 16, 17, 19)]
        except ValueError as e:
            raise ValueError(f"Could not convert extracted PBT data to integers: {e}")
        except IndexError:
            raise IndexError("Regex pattern did not extract the expected number of PBT data points.")

        return pbt_data
    
    def get_pat(self):
        """
        Extracts profit after tax (PAT) data from the table body.

        Returns:
            list: A list of integers representing PAT data.

        Raises:
            TypeError: If `quarters.table_body` is not a list or its tenth element is not a string.
            AttributeError: If `quarters.button_pattern` is not a valid regex pattern or is None.
            IndexError: If `quarters.table_body` has fewer than ten elements or the regex match fails.
            ValueError: If the extracted PAT data cannot be converted to integers.
        """
        try:
            if not isinstance(self.table_body, list):
                raise TypeError("quarters.table_body must be a list.")
            profit_after_tax = str(self.table_body[9])  # Access the tenth element
        except IndexError:
            raise IndexError("quarters.table_body does not have enough elements.")
        except TypeError:
            raise TypeError("The elements of quarters.table_body must be strings.")

        try:
            match_pat = re.match(self.button_pattern, profit_after_tax)
        except AttributeError:
            raise AttributeError("quarters.button_pattern must be a valid regex pattern and cannot be None.")

        if not match_pat:
            raise ValueError(f"Regex pattern {self.button_pattern} did not match the PAT string: {profit_after_tax}")

        try:
            pat_data = [int(i.replace(',', '').replace('%', '')) for i in match_pat.group(6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30)]
        except ValueError as e:
            raise ValueError(f"Could not convert extracted PAT data to integers: {e}")
        except IndexError:
            raise IndexError("Regex pattern did not extract the expected number of PAT data points.")

        return pat_data


    def get_eps(self):
        """
        Extracts earnings per share (EPS) data from the table body.

        Returns:
            list: A list of floats representing EPS data.

        Raises:
            TypeError: If `quarters.table_body` is not a list or its eleventh element is not a string.
            AttributeError: If `quarters.non_button_pattern` is not a valid regex pattern or is None.
            IndexError: If `quarters.table_body` has fewer than eleven elements or the regex match fails.
            ValueError: If the extracted EPS data cannot be converted to floats.
        """
        try:
            if not isinstance(self.table_body, list):
                raise TypeError("quarters.table_body must be a list.")
            eps = str(self.table_body[10])  # Access the eleventh element
        except IndexError:
            raise IndexError("quarters.table_body does not have enough elements.")
        except TypeError:
            raise TypeError("The elements of quarters.table_body must be strings.")

        try:
            match_eps = re.match(self.non_button_pattern, eps)
        except AttributeError:
            raise AttributeError("quarters.non_button_pattern must be a valid regex pattern and cannot be None.")

        if not match_eps:
            raise ValueError(f"Regex pattern {self.non_button_pattern} did not match the EPS string: {eps}")

        try:
            eps_data = [float(i.replace(',', '')) for i in match_eps.group(4, 5, 6, 7, 9, 10, 11, 12, 14, 15, 16, 17, 19)]
        except ValueError as e:
            raise ValueError(f"Could not convert extracted EPS data to floats: {e}")
        except IndexError:
            raise IndexError("Regex pattern did not extract the expected number of EPS data points.")

        return eps_data

    # Method to get all the data
    def get_quarter_data(self):
        quarters = []
        quarters.extend(self.get_header())
        quarters.append(self.get_sales())
        quarters.append(self.get_expenses())
        quarters.append(self.get_pbt())
        quarters.append(self.get_pat())
        quarters.append(self.get_eps())
        return quarters
    
    # Method to get only data for csv creator
    def get_quarter_result(self):
        quarters = []
        quarters.append(self.get_sales())
        quarters.append(self.get_expenses())
        quarters.append(self.get_pbt())
        quarters.append(self.get_pat())
        quarters.append(self.get_eps())
        return quarters

class AnnualResult:
    def __init__(self, ticker):
        url = f"https://www.screener.in/company/{ticker}/consolidated/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        self.soup = BeautifulSoup(response.content, 'html.parser')

        # Getting Table Header and Table Body
        self.table_header = str(self.soup.find(id = "profit-loss").thead)
        self.table_body = self.soup.find(id = "profit-loss").tbody.find_all('tr')

        # Annual Result Header Pattern
        self.annual_header_pattern = r'''<thead>
<tr>
<th class=\"text\"></th>
<th class=\"(.*)\">
            (.*?) (.*?)
            
          </th>
<th class=\"(.*)\">
            (.*?) (.*?)
            
          </th>
<th class=\"(.*)\">
            (.*?) (.*?)
            
          </th>
<th class=\"(.*)\">
            (.*?) (.*?)
            
          </th>
<th class=\"(.*)\">
            (.*?) (.*?)
            
          </th>
<th class=\"(.*)\">
            (.*?) (.*?)
            
          </th>
<th class=\"(.*)\">
            (.*?) (.*?)
            
          </th>
<th class=\"(.*)\">
            (.*?) (.*?)
            
          </th>
<th class=\"(.*)\">
            (.*?) (.*?)
            
          </th>
<th class=\"(.*)\">
            (.*?) (.*?)
            
          </th>
<th class=\"(.*)\">
            (.*?) (.*?)
            
          </th>
<th class=\"(.*)\">
            (.*?) (.*?)
            
          </th>
<th class=\"(.*)\">
            (.*?)
            
          </th>
</tr>
</thead>'''

        # Button Pattern Followed by Sales, Expenses and PAT
        self.button_pattern = r'''<tr class=\"(.*)\">
<td class=\"text\">
<button class=\"button-plain\" onclick=\"(.*)\">
                  (.*) <span class=\"blue-icon\">(.*)</span>
</button>
</td>
<td class=\"(.*)\">(.*?)</td>
<td class=\"(.*)\">(.*?)</td>
<td class=\"(.*)\">(.*?)</td>
<td class=\"(.*)\">(.*?)</td>
<td class=\"(.*)\">(.*?)</td>
<td class=\"(.*)\">(.*?)</td>
<td class=\"(.*)\">(.*?)</td>
<td class=\"(.*)\">(.*?)</td>
<td class=\"(.*)\">(.*?)</td>
<td class=\"(.*)\">(.*?)</td>
<td class=\"(.*)\">(.*?)</td>
<td class=\"(.*)\">(.*?)</td>
<td class=\"(.*)\">(.*?)</td>
</tr>'''

        # Non Button Pattern Followed by PBT and EPS
        self.non_button_pattern = r'''<tr class=\"(.*)\">
<td class=\"text\">
              
                (.*)
              
            </td>
<td class=\"(.*)\">(.*?)</td>
<td class=\"\">(.*?)</td>
<td class=\"\">(.*?)</td>
<td class=\"\">(.*?)</td>
<td class=\"(.*)\">(.*?)</td>
<td class=\"\">(.*?)</td>
<td class=\"\">(.*?)</td>
<td class=\"\">(.*?)</td>
<td class=\"(.*)\">(.*?)</td>
<td class=\"\">(.*?)</td>
<td class=\"\">(.*?)</td>
<td class=\"\">(.*?)</td>
<td class=\"(.*)\">(.*?)</td>
</tr>'''

    def get_header(self):
        """
        Extracts month and year headers from the table header string.

        Args:
            self: The object containing the table_header and annual_header_pattern attributes.

        Returns:
            A list containing two lists: the first list contains the months, and the
            second list contains the years.

        Raises:
            TypeError: If table_header or annual_header_pattern is not a string.
            ValueError: If the table_header does not match the annual_header_pattern.
            AttributeError: If the object does not have the required attributes.
        """
        if not isinstance(self.table_header, str):
            raise TypeError("annual table_header must be a string")
        if not hasattr(self, 'annual_header_pattern'):
            raise AttributeError("Object must have 'annual_header_pattern' attribute")
        if not isinstance(self.annual_header_pattern, str):
            raise TypeError("annual_header_pattern must be a string.")

        match_table_header = re.match(self.annual_header_pattern, self.table_header)
        if not match_table_header:
            raise ValueError("annual table_header does not match the expected pattern")

        annual_header_month = match_table_header.group(2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35)
        annual_header_month_number = []
        for month_str in annual_header_month:
            try:
                month_number = Month[month_str].value
                annual_header_month_number.append(month_number)
            except KeyError:
                annual_header_month_number.append(None)  # Or handle invalid months differently
        annual_header_year = match_table_header.group(3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36)

        return [list(annual_header_month_number), list(annual_header_year)]



    def get_sales(self):
        """
        Extracts and cleans sales data from the table body.

        Args:
            self: The object containing the table_body and button_pattern attributes.

        Returns:
            A list of integers representing the sales data.

        Raises:
            TypeError: If table_body is not a list or button_pattern is not a string.
            ValueError: If the sales data does not match the expected pattern.
            AttributeError: If the object does not have the required attributes.
        """
        if not hasattr(self, 'table_body'):
            raise AttributeError("Object must have 'table_body' attribute")
        if not isinstance(self.table_body, list):
            raise TypeError("annual table_body must be a list")
        if not hasattr(self, 'button_pattern'):
            raise AttributeError("Object must have 'button_pattern' attribute")
        if not isinstance(self.button_pattern, str):
            raise TypeError("annual button_pattern must be a string.")

        if not self.table_body:  # Check if table_body is empty
            raise ValueError("annual table_body is empty")

        sales = str(self.table_body[0])
        match_sales = re.match(self.button_pattern, sales)
        if not match_sales:
            raise ValueError("Annual Sales data does not match the expected pattern")

        sales_data = [int(i.replace(',', '')) for i in match_sales.group(6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28)]
        return sales_data


    def get_expenses(self):
        """
        Extracts and cleans expenses data from the table body.

        Args:
            self: The object containing the table_body and button_pattern attributes.

        Returns:
            A list of integers representing the expenses data.

        Raises:
            TypeError: If table_body is not a list or button_pattern is not a string.
            ValueError: If the expenses data does not match the expected pattern.
            AttributeError: If the object does not have the required attributes.
        """
        if not hasattr(self, 'table_body'):
            raise AttributeError("Object must have 'table_body' attribute")
        if not isinstance(self.table_body, list):
            raise TypeError("table_body must be a list")
        if not hasattr(self, 'button_pattern'):
            raise AttributeError("Object must have 'button_pattern' attribute")
        if not isinstance(self.button_pattern, str):
            raise TypeError("button_pattern must be a string.")

        if not self.table_body:  # Check if table_body is empty
            raise ValueError("table_body is empty")

        expenses = str(self.table_body[1])
        match_expenses = re.match(self.button_pattern, expenses)
        if not match_expenses:
            raise ValueError("Expenses data does not match the expected pattern")

        expenses_data = [int(i.replace(',', '')) for i in match_expenses.group(6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28)]
        return expenses_data



    def get_pbt(self):
        """
        Extracts and cleans profit before tax (PBT) data from the table body.

        Args:
            self: The object containing the table_body and non_button_pattern attributes.

        Returns:
            A list of integers representing the PBT data.

        Raises:
            TypeError: If table_body is not a list or non_button_pattern is not a string.
            ValueError: If the PBT data does not match the expected pattern.
            AttributeError: If the object does not have the required attributes.
        """
        if not hasattr(self, 'table_body'):
            raise AttributeError("Object must have 'table_body' attribute")
        if not isinstance(self.table_body, list):
            raise TypeError("table_body must be a list")
        if not hasattr(self, 'non_button_pattern'):
            raise AttributeError("Object must have 'non_button_pattern' attribute")
        if not isinstance(self.non_button_pattern, str):
            raise TypeError("non_button_pattern must be a string.")

        if not self.table_body:  # Check if table_body is empty
            raise ValueError("table_body is empty")

        profit_before_tax = str(self.table_body[7])
        match_pbt = re.match(self.non_button_pattern, profit_before_tax)
        if not match_pbt:
            raise ValueError("PBT data does not match the expected pattern")

        pbt_data = [int(i.replace(',', '')) for i in match_pbt.group(4, 5, 6, 7, 9, 10, 11, 12, 14, 15, 16, 17)]
        return pbt_data


    def get_pat(self):
        """
        Extracts and cleans profit after tax (PAT) data from the table body.

        Args:
            self: The object containing the table_body and button_pattern attributes.

        Returns:
            A list of integers representing the PAT data.

        Raises:
            TypeError: If table_body is not a list or button_pattern is not a string.
            ValueError: If the PAT data does not match the expected pattern.
            AttributeError: If the object does not have the required attributes.
        """
        if not hasattr(self, 'table_body'):
            raise AttributeError("Object must have 'table_body' attribute")
        if not isinstance(self.table_body, list):
            raise TypeError("table_body must be a list")
        if not hasattr(self, 'button_pattern'):
            raise AttributeError("Object must have 'button_pattern' attribute")
        if not isinstance(self.button_pattern, str):
            raise TypeError("button_pattern must be a string.")

        if not self.table_body:  # Check if table_body is empty
            raise ValueError("table_body is empty")

        profit_after_tax = str(self.table_body[9])
        match_pat = re.match(self.button_pattern, profit_after_tax)
        if not match_pat:
            raise ValueError("PAT data does not match the expected pattern")

        pat_data = [int(i.replace(',', '').replace('%', '')) for i in match_pat.group(6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28)]
        return pat_data


    def get_eps(self):
        """
        Extracts and cleans earnings per share (EPS) data from the table body.

        Args:
            self: The object containing the table_body and non_button_pattern attributes.

        Returns:
            A list of floats representing the EPS data.

        Raises:
            TypeError: If table_body is not a list or non_button_pattern is not a string.
            ValueError: If the EPS data does not match the expected pattern.
            AttributeError: If the object does not have the required attributes.
        """
        if not hasattr(self, 'table_body'):
            raise AttributeError("Object must have 'table_body' attribute")
        if not isinstance(self.table_body, list):
            raise TypeError("table_body must be a list")
        if not hasattr(self, 'non_button_pattern'):
            raise AttributeError("Object must have 'non_button_pattern' attribute")
        if not isinstance(self.non_button_pattern, str):
            raise TypeError("non_button_pattern must be a string.")

        if not self.table_body:  # Check if table_body is empty
            raise ValueError("table_body is empty")

        eps = str(self.table_body[10])
        match_eps = re.match(self.non_button_pattern, eps)
        if not match_eps:
            raise ValueError("EPS data does not match the expected pattern")

        eps_data = [float(i.replace(',', '')) for i in match_eps.group(4, 5, 6, 7, 9, 10, 11, 12, 14, 15, 16, 17)]
        return eps_data
    
    # Method to get all the data
    def get_annual_data(self):
        annual_data = []
        annual_data.extend(self.get_header())
        annual_data.append(self.get_sales())
        annual_data.append(self.get_expenses())
        annual_data.append(self.get_pbt())
        annual_data.append(self.get_pat())
        annual_data.append(self.get_eps())
        return annual_data
    
    # Method to get only data for csv creator
    def get_annual_result(self):
        annual_data = []
        annual_data.append(self.get_sales())
        annual_data.append(self.get_expenses())
        annual_data.append(self.get_pbt())
        annual_data.append(self.get_pat())
        annual_data.append(self.get_eps())
        return annual_data
    
# CSV Writter Function
def security_csv_writter(result, security_name, type):
    '''
    Write CSV file for a specific security in the security_[quarter, annual].csv
    
    results_size: 7
    type: 0 => quarter | 1 => annual
    '''

    if (type > 1 or type < 0):
        raise Exception('Type Value is expected to be 0 or 1')

    if (type == 0):
        file = open('security_quarter.csv', 'w')
    elif (type == 1):
        file = open('securtiy_annual.csv', 'w')
    

    for i in range(2, 7):
        for j in range(len(result[0])):
            match i:
                case 2:
                    file.write("{0}, {1}, {2}, {3}, {4}\n".format(
                        result[0][j],
                        result[1][j],
                        security_name,
                        "Sales",
                        result[2][j])
                    )
                
                case 3:
                    file.write("{0}, {1}, {2}, {3}, {4}\n".format(
                        result[0][j],
                        result[1][j],
                        security_name,
                        "Expenses",
                        result[3][j])
                    )

                case 4:
                    file.write("{0}, {1}, {2}, {3}, {4}\n".format(
                        result[0][j],
                        result[1][j],
                        security_name,
                        "PBT",
                        result[4][j])
                    )

                case 5:
                    file.write("{0}, {1}, {2}, {3}, {4}\n".format(
                        result[0][j],
                        result[1][j],
                        security_name,
                        "PAT",
                        result[5][j])
                    )

                case 6:
                    file.write("{0}, {1}, {2}, {3}, {4}\n".format(
                        result[0][j],
                        result[1][j],
                        security_name,
                        "EPS",
                        result[6][j])
                    )

    file.close()
    print('Successfully written data to file ')

    if (type == 0):
        print('Successfully written data to file security_quarter.csv')
    elif (type == 1):
        print('Successfully written data to file securtiy_annual.csv')

def scrape_financials(ticker):
    """Scrape quarterly and annual data for a ticker."""
    try:
        # Scrape quarterly data
        quarter_scraper = QuarterResult(ticker)
        quarter_scraper.ticker = ticker
        quarterly_data = quarter_scraper.get_quarter_data()

        # Scrape annual data
        annual_scraper = AnnualResult(ticker)
        annual_scraper.ticker = ticker
        annual_data = annual_scraper.get_annual_data()

        return {'quarterly': quarterly_data, 'annual': annual_data}
    except (requests.RequestException, InvalidFinancialDataError) as e:
        print(f"Error scraping {ticker}: {e}")
        return {'quarterly': [], 'annual': []}
    
# Driver Program
# if __name__ == "__main__":
#     quarter = QuarterResult('SUNPHARMA')

#     security_csv_writter(quarter.get_quarter_result(),'SUNPHARMA', 0)

# data = scrape_financials('SUNPHARMA')

# print(data['annual'])