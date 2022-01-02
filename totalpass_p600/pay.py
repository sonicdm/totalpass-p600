from datetime import datetime

from bs4 import BeautifulSoup
from pydantic.dataclasses import dataclass

"""

COMPANY INFORMATION 
 
Company Name
Capella Market
 
Company Payroll ID
2489
 
PAYROLL PREFERENCES 
 
Pay Period Type
Bi-Weekly
 
  
 
Last Pay Start
12/05/21
 
This Pay Start
12/19/21
 
Next Pay Start
01/02/22
 
  
 
Day Start
12:00a

 
Week Start
Sun
 
  
 
OVERTIME PREFERENCES 
 
Day OT1 After
99.00
Hours
Day OT2 After
99.00
Hours
Week OT1 After
40.00
Hours
Week OT2 After
99.00
Hours
Consecutive Day OT
No
 
OT1 Multiplier
1.50
 
OT2 Multiplie
"""


@dataclass
class PayConfig:
    # Company Information
    company_name: str
    company_payroll_id: str
    # Payroll Preferences
    pay_period_type: str
    last_pay_start: str
    this_pay_start: str
    next_pay_start: str
    day_start: datetime  # time of day the payroll day starts
    week_start: str  # day of week the payroll week starts
    # Overtime Preferences
    day_ot1_after: str  # daily hours after which ot1 is applied
    week_ot1_after: str  # weekly hours after which ot1 is applied
    consecutive_day_ot: str  # whether ot1 is applied consecutively
    ot1_multiplier: str  # ot1 multiplier
    ot2_multiplier: str  # ot2 multiplier
    day_ot2_after: str  # daily hours after which ot2 is applied
    week_ot2_after: str  # weekly hours after which ot2 is applied


def parse_pay_page(pay_page_html):
    pay_soup = BeautifulSoup(pay_page_html, 'lxml')
    # Company Information

    company_name = pay_soup.find('span', {'id': 'ctl00_ContentPlaceHolder1_lblCompanyName'}).text
    # Payroll Preferences

    # Overtime Preferences

    pay_config = PayConfig()
