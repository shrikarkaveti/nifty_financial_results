import requests
from bs4 import BeautifulSoup
import re

class QuarterResult:
    def __init__(self, security_name):
        # Getting HTML Parser Data
        url = f"https://www.screener.in/company/{security_name}/consolidated/"
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        self.soup = BeautifulSoup(response.content, 'html.parser')

        # Getting Table Header and Table Body
        self.table_header = str(self.soup.find(id = "quarters").thead)
        self.table_body = self.soup.find(id = "quarters").tbody.find_all('tr')

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
        quarter_header_year = match_table_header.group(3, 6, 9, 12, 15, 18, 21, 24, 27, 29, 32, 35, 38)

        return [list(quarter_header_month), list(quarter_header_year)]
    
    # [0] (Quarter Result Index) Sales - 0 (Soup Index)
    # [1] Expenses - 1
    # [2] PBT - 7
    # [3] PAT - 9
    # [4] EPS - 10
    
    def get_sales(self):
       sales = str(self.table_body[0])
       match_sales = re.match(self.button_pattern, sales)
       sales_data = [int(i.replace(',', '')) for i in match_sales.group(6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30)]
       return sales_data
    
    def get_expenses(self):
       expenses = str(self.table_body[1])
       match_expenses = re.match(self.button_pattern, expenses)
       expenses_data = [int(i.replace(',', '')) for i in match_expenses.group(6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30)]
       return expenses_data
    
    def get_pbt(self):
        profit_before_tax = str(self.table_body[7])
        match_pbt = re.match(self.non_button_pattern, profit_before_tax)
        pbt_data = [int(i.replace(',', '')) for i in match_pbt.group(4, 5, 6, 7, 9, 10, 11, 12, 14, 15, 16, 17, 19)]
        return pbt_data
    
    def get_pat(self):
        profit_after_tax = str(self.table_body[9])
        match_pat = re.match(self.button_pattern, profit_after_tax)
        pat_data = [int(i.replace(',', '').replace('%', '')) for i in match_pat.group(6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30)]
        return pat_data

    def get_eps(self):
        eps = str(self.table_body[10])
        match_eps = re.match(self.non_button_pattern, eps)
        eps_data = [float(i.replace(',', '')) for i in match_eps.group(4, 5, 6, 7, 9, 10, 11, 12, 14, 15, 16, 17, 19)]
        return eps_data

    # Method to get all the data
    def get_quarter_result(self):
        quarters = []
        quarters.extend(self.get_header())
        quarters.append(self.get_sales())
        quarters.append(self.get_expenses())
        quarters.append(self.get_pbt())
        quarters.append(self.get_pat())
        quarters.append(self.get_eps())
        return quarters
    
    # Method to get only data for csv creator
    def get_quarter_data(self):
        quarters = []
        quarters.append(self.get_sales())
        quarters.append(self.get_expenses())
        quarters.append(self.get_pbt())
        quarters.append(self.get_pat())
        quarters.append(self.get_eps())
        return quarters
    
    # Method to write data to 


class AnnualResult:
    def __init__(self, security_name):
        # Getting HTML Parser Data
        url = f"https://www.screener.in/company/{security_name}/consolidated/"
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
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
        match_table_header = re.match(self.annual_header_pattern, self.table_header)
        annual_header_month = match_table_header.group(2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35, 38)
        annual_header_year = match_table_header.group(3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36, 38)

        return [list(annual_header_month), list(annual_header_year)]
    
    # [0] (annual Result Index) Sales - 0 (Soup Index)
    # [1] Expenses - 1
    # [2] PBT - 7
    # [3] PAT - 9
    # [4] EPS - 10
    
    def get_sales(self):
       sales = str(self.table_body[0])
       match_sales = re.match(self.button_pattern, sales)
       sales_data = [int(i.replace(',', '')) for i in match_sales.group(6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30)]
       return sales_data
    
    def get_expenses(self):
       expenses = str(self.table_body[1])
       match_expenses = re.match(self.button_pattern, expenses)
       expenses_data = [int(i.replace(',', '')) for i in match_expenses.group(6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30)]
       return expenses_data
    
    def get_pbt(self):
        profit_before_tax = str(self.table_body[7])
        match_pbt = re.match(self.non_button_pattern, profit_before_tax)
        pbt_data = [int(i.replace(',', '')) for i in match_pbt.group(4, 5, 6, 7, 9, 10, 11, 12, 14, 15, 16, 17, 19)]
        return pbt_data
    
    def get_pat(self):
        profit_after_tax = str(self.table_body[9])
        match_pat = re.match(self.button_pattern, profit_after_tax)
        pat_data = [int(i.replace(',', '').replace('%', '')) for i in match_pat.group(6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30)]
        return pat_data

    def get_eps(self):
        eps = str(self.table_body[10])
        match_eps = re.match(self.non_button_pattern, eps)
        eps_data = [float(i.replace(',', '')) for i in match_eps.group(4, 5, 6, 7, 9, 10, 11, 12, 14, 15, 16, 17, 19)]
        return eps_data

    # Method to get all the data
    def get_annual_result(self):
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

# Complete CSv Writter Function



# Driver Program
if __name__ == "__main__":
    quarter = QuarterResult('SUNPHARMA')

    security_csv_writter(quarter.get_quarter_result(),'SUNPHARMA', 0)