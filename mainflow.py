from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException , ElementClickInterceptedException
import time
import re
import datetime
from xlsxwriter import Workbook
from xlsxwriter.utility import xl_rowcol_to_cell
import os
import win32com.client as win32


# TODO: Add explicit wait for selenium
# TODO: Add chrome options
# TODO: Add mature / non-mature flats

class SBFScraper:

    def __init__(self, filename, headless: bool = False):
        self._filename = os.path.abspath(filename)
        self._headless = headless
        self._service = ChromeService(ChromeDriverManager().install())
        self._driver = webdriver.Chrome(service=self._service)
        self._driver.get("https://homes.hdb.gov.sg/home/finding-a-flat")
        self._initial_units = self.get_SBF_units_n_click()

    def get_SBF_units_n_click(self):
        test = self._driver.find_elements(By.XPATH,
                                          "/html/body/app-root/div[2]/app-find-my-flat/section/div/"
                                          "app-search-results/div/div/div[4]/app-flat-cards-categories")
        for element in test:
            split = element.text.split(sep='\n')
            if split[0] == 'SBF':
                element.click()
                break
        return int(''.join([x for x in split[1] if x.isdigit()]))

    def get_town_details(self):
        town_details = self._driver.find_element(By.XPATH,
                                                 "/html/body/app-root/div[2]/app-sbf-details"
                                                 "/section/div/div[3]/div[1]/div/div/div/div[2]/div").text.split(
            sep='\n')
        town_dict = dict(zip(town_details[::2], town_details[1::2]))
        town_dict['Remaining Lease'] = self.parse_lease(town_dict['Remaining Lease'])
        town_dict['Est months'] = ''
        if 'available' not in town_dict['Est. Completion Date'].lower():
            town_dict['Est. Completion Date'] = self.parse_dates(town_dict['Est. Completion Date'])
            town_dict['Keys Available'] = False
        else:
            town_dict['Est. Completion Date'] = ''
            town_dict['Keys Available'] = True

        return town_dict

    def scroll_blocks(self, flat_type_dict):
        block_no_selector = Select(
            self._driver.find_element(By.XPATH, "//*[@id='layout-block']/div[2]/div/div/div[3]/select"))
        value = 0
        flat_block_LD = []
        while True:
            try:
                block_no_selector.select_by_value(str(value))
                block_no_string = self._driver.find_element(By.XPATH,
                                                            f"//*[@id='layout-block']/div[2]/"
                                                            f"div/div/div[3]/select/option[{value + 3}]").text
                block_dict = {'Block': block_no_string}
                ethnics_dict = self.get_ethnics()
                list_of_flats = [flat_type_dict | block_dict | x | ethnics_dict for x in self.get_units()]
                flat_block_LD.extend(list_of_flats)
                value += 1
            except NoSuchElementException:
                break
        return flat_block_LD

    # loop to check room type
    def scroll_flat_type(self, town_dict):
        flat_type_selector = Select(
            self._driver.find_element(By.XPATH, "//*[@id='layout-block']/div[2]/div/div/div[1]/select"))
        value = 0
        final_flat_block_LD = []
        while True:
            try:
                flat_type_selector.select_by_value(str(value))
                flat_type_string = self._driver.find_element(By.XPATH,
                                                             f"//*[@id='layout-block']/"
                                                             f"div[2]/div/div/div[1]/select/option[{value + 2}]").text
                flat_type_dict = town_dict | {"flat_type": flat_type_string}
                final_flat_block_LD.extend(self.scroll_blocks(flat_type_dict))
                value += 1
            except NoSuchElementException:
                break
        return final_flat_block_LD

    def get_ethnics(self):
        ethnic = self._driver.find_element(By.XPATH, "//*[@id='available-sidebar']/div[1]/div[2]").text
        ethnic = re.split(r'\n|:', ethnic)
        ethnic = dict(zip(ethnic[::2], ethnic[1::2]))
        return ethnic

    def get_units(self):
        all_blocks = self._driver.find_element(By.XPATH, "//*[@id='available-grid']").text
        flat_list = re.split('#', all_blocks)
        flat_list = self.remove_null(flat_list)
        list_of_flats = []
        for floor_level in flat_list:
            floor_level = floor_level.split(sep='\n')
            floor_level = self.remove_null(floor_level)
            list_of_flats.extend(self.get_flats(floor_level))
        return list_of_flats

    @staticmethod
    def get_flats(floor_level_list):
        index = 1
        flats = []
        while index < len(floor_level_list):
            test_dict = {'level': int(floor_level_list[0]),
                         'unit': floor_level_list[index],
                         'sqm': int(floor_level_list[index + 1].split(sep=' ')[0]),
                         'price': int(floor_level_list[index + 2].replace('$', '').replace(',', ''))}
            flats.append(test_dict)
            index += 3
        return flats

    @staticmethod
    def remove_null(any_list_with_null: list) -> list:
        return list(filter(None, any_list_with_null))

    @staticmethod
    def parse_dates(date):
        if "Q" in date:
            _date = re.split(r'Q/| to ', date)[-2:]
            date = datetime.datetime(int(_date[1]), int(_date[0]) * 3, 1)

        else:
            _date = re.split(r' to |/', date)[-2:]
            date = datetime.datetime(int(_date[1]), int(_date[0]), 1)
        return date

    @staticmethod
    def parse_lease(lease: str) -> int:
        """
        Parse lease to get remaining lease in months
        If lease is range A - B, then returns B
        Else returns only one value
        :param lease: string of lease
        :return: remaining lease in years as integer
        """
        return int(re.findall('\d+',lease)[-1])

    def run(self):
        """
        Run function
        """
        # 1. Get list of all towns
        # Select 50 towns per page for faster checking
        sel = Select(self._driver.find_element(By.XPATH,
                                               "/html/body/app-root/div[2]/app-find-my-flat/section/div/"
                                               "app-search-results/div/div/div[3]/div/div[1]/div[1]"
                                               "/div[2]/select"))
        sel.select_by_value('50')
        print("Getting list of towns...")
        list_of_links = []
        while True:
            for div in self._driver.find_elements(By.CLASS_NAME, "flat-link"):
                list_of_links.append(div.get_attribute('href'))
            try:
                self._driver.find_element(By.CSS_SELECTOR, "[aria-label=Next]").click()
            # if not clickable then break, meaning end of pages
            except ElementClickInterceptedException:
                break
            time.sleep(1)

        # Internal functions have their own loops
        # for loop by town, then by flat type, then by block, then by unit
        print("Running through every town...")
        final_list = []
        tic = time.perf_counter()
        for link in list_of_links:
            self._driver.get(link)
            time.sleep(1)
            flat_details = self.scroll_flat_type(self.get_town_details())
            dict_by_town = [x | {'Link': link} for x in flat_details]
            final_list.extend(dict_by_town)
        print(f"{len(final_list)} flats found. Took {time.perf_counter() - tic:.2f} seconds")
        if len(final_list) == self._initial_units:
            print(f"Correct number of units found")
        self._driver.quit()
        # 3. Parse data into xlsx
        print("Parsing data into xlsx...")
        wb = Workbook(self._filename)
        ws = wb.add_worksheet("Raw Data")
        ordered_list = list(final_list[0].keys())

        first_row = 0
        for header in ordered_list:
            col = ordered_list.index(header)  # We are keeping order.
            ws.write(first_row, col, header)  # We have written first row which is the header of worksheet also.

        date_format = wb.add_format({'num_format': 'mm/dd/yyyy'})

        row = 1
        for details in final_list:
            for _key, _value in details.items():
                col = ordered_list.index(_key)
                if _key.lower() == 'est. completion date':
                    ws.write(row, col, _value, date_format)
                elif _key.lower() == 'est months':
                    cell = xl_rowcol_to_cell(row, col - 1)
                    ws.write_formula(row=row, col=col, formula=f'=IFERROR(DATEDIF(TODAY(),{cell},"M"),0)')
                else:
                    ws.write(row, col, _value)
            row += 1  # enter the next row
        wb.close()

        # Autofit columns
        print("Autofitting columns...")
        excel = win32.gencache.EnsureDispatch('Excel.Application')
        wb = excel.Workbooks.Open(self._filename)
        ws = wb.Worksheets("Raw Data")
        ws.Columns.AutoFit()
        wb.Save()
        excel.Application.Quit()


SBFScraper(filename='NOV22_SBF.xlsx').run()
