from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import re
from bs4 import BeautifulSoup
import requests
import csv
import shutil
    

major = "Computer Science"

print("Choose degree:")
print("1 = Bachelor")
print("2 = Master")
print("3 = PhD")
print("'' = All degrees")
degree_input = 2
All = ""
format_major = lambda x: x.replace(" ", "%20")


def get_number_of_programs(page):
    html = page.content()
    soup = BeautifulSoup(html, "html.parser")

    title_element = soup.find("h2", class_="c-result-header__title js-result-header-title")
    if title_element:
        programs = title_element.get_text(strip=True)
        number_of_programs = re.search(r"\d[\d,]*", programs)
        if number_of_programs:
            return number_of_programs.group(0).replace(",", "")
    return None  


base_url = f"https://www2.daad.de/deutschland/studienangebote/international-programmes/en/result/?q={format_major(major)}&fos=&cert=&admReq=&langExamPC=&scholarshipLC=&langExamLC=&scholarshipSC=&langExamSC=&degree%5B%5D={degree_input}&langDeAvailable=&langEnAvailable=&lang%5B%5D=&modStd%5B%5D=&cit%5B%5D=&tyi%5B%5D=&ins%5B%5D=&fee=&bgn%5B%5D=&dat%5B%5D=&prep_subj%5B%5D=&prep_degree%5B%5D=&sort=4&dur=&subjects%5B%5D=&limit=10&offset=&display=list"
programs_list = []
program_details = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    try:
        page.goto(base_url)
        page.wait_for_selector("button:has-text('Accept')")
        page.click("button:has-text('Accept')")
        page.wait_for_selector("h2.c-result-header__title")

        number_of_programs = get_number_of_programs(page)
        
        if number_of_programs:
            print(f"Number of programs found: {number_of_programs}")
            json_data_url = f"https://www2.daad.de/deutschland/studienangebote/international-programmes/api/solr/en/search.json?cert=&admReq=&langExamPC=&scholarshipLC=&langExamLC=&scholarshipSC=&langExamSC=&fos=&langDeAvailable=&langEnAvailable=&fee=&sort=4&dur=&q={format_major(major)}&limit={number_of_programs}&offset=&display=list&isElearning=&isSep="
            
            response = requests.get(json_data_url)
            if response.status_code == 200:
                data = response.json()
                programs_list = [(course['id'], course['academy']) for course in data['courses']]
            else:
                print(f"Failed to retrieve JSON data. Status code: {response.status_code}")
        else:
            print("Could not retrieve the number of programs.")
        
        for id, uni in programs_list:
            print(id, uni)
            try:
                degree_url = f"https://www2.daad.de/deutschland/studienangebote/international-programmes/en/detail/{id}/"
                print(degree_url)
                page.goto(degree_url, timeout=5000)
                page.wait_for_load_state("networkidle", timeout=15000)

                degree_name = page.locator('span.d-sm-none').text_content().strip()

                page.click("#costs-tab", timeout=5000)
                funding_label = page.locator("dt:has-text('Funding opportunities within the university')").nth(0)
                funding_value = funding_label.locator("xpath=following-sibling::dd[1]").inner_text().strip()

                program_details.append({
                    "Program ID": id,
                    "University": uni,
                    "degree": degree_name,
                    "Funding Opportunities": funding_value,
                    "link": degree_url
                })            
            except PlaywrightTimeoutError:
                print(f"Timeout while processing program {id} - {uni}, skipping...")
                continue
            except Exception as e:
                print(f"Unexpected error with program {id} - {uni}: {e}")
                continue
    finally:
        browser.close()


if program_details:
    keys = program_details[0].keys()
    
    filename = f"daad_programs_{major.replace(' ', '_')}.csv"
        
    with open(filename, "w", newline="", encoding="utf-8") as f:
        dict_writer = csv.DictWriter(f, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(program_details)
        
    shutil.copy(filename, "output.csv")
