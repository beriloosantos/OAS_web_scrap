import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
import time
import pandas as pd
import numpy as np
import re
import sys, os


def get_avaiable_links(driver, years):

    base_url = "https://www.oas.org/EOMDatabase/"
    driver.get(base_url)
    time.sleep(3)

    links = []

    for year in years:
        
        # Verify if year is avaiable
        found_year = False

        try:
            # Click year's input
            year_input = driver.find_element(By.CSS_SELECTOR, "#ctl00_ContentPlaceHolder1_RadDataPager1_ctl00_TimelineYearCB_Input")
            year_input.click()
            time.sleep(1)

            # Type year
            year_input.send_keys(str(year))
            time.sleep(1)
            year_input.send_keys(Keys.RETURN)  # Press Enter

            # Wait for year to show and click
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.LINK_TEXT, str(year)))
            )
            year_link = driver.find_element(By.LINK_TEXT, str(year))
            year_link.click()
            found_year = True
            time.sleep(2)
    
        except Exception as e:
            print(f"Erro ao buscar o ano {year}: {e}")

        # Iterate through every country
        for i in range(34):  # 33 members
            html_element = WebDriverWait(driver, 1).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, f"#ctl00_ContentPlaceHolder1_RadListCountries_i{i}"))
                )
            moesid = html_element.get_attribute("moesid")
            if moesid:
                # Generate link through 'onclick'
                link = f"https://www.oas.org/EOMDatabase/moeInfo.aspx?Lang=En&Id={moesid}"
                links.append(link)

    return links

def get_general_informations_and_documents(driver, links):

    general_informations = []
    for link in links:

        driver.get(link)
        time.sleep(3)
        
        # Download PDF documents in page
        download_documents(link)

        # Is there second round?
        try:
            # Locate the specific <td> element to check its class
            round_element = driver.find_element(By.XPATH, "/html/body/div/div[3]/form/div[4]/div[2]/div[1]/div[1]/div/div/div[2]/div[3]/table/tbody/tr/td/div/table/tbody/tr/td[2]")

            # Check the class of the element
            element_class = round_element.get_attribute("class")
            if "rd-optionToShow" in element_class:
                rounds = ['First', 'Second']
            else:
                rounds = ['First']
            print(rounds)
        except Exception as e:
            print(f"Error while checking round information: {e}")

        for round in rounds:

            info_dict = {
            "URL": link,
            "Round": round,
            "Chief of Mission": "",
            "Deputy Chief": "",
            "Election Types": "",
            "Observed Topics": "",
            "Observers": "",
            "Donors": "",
            "Invitation": "",
            "Acceptance": "",
            "Installation": "",
            "Election Date": "",
            "Withdrawal": ""
            }

            # Extract round information
            try:
                if round == "Second":
                    try:
                        # Locate and click the "Second Round" button
                        second_round_button = driver.find_element(By.XPATH, "/html/body/div/div[3]/form/div[4]/div[2]/div[1]/div[1]/div/div/div[2]/div[3]/table/tbody/tr/td/div/table/tbody/tr/td[2]")
                        second_round_button.click()
                        time.sleep(3)  # Allow time for the page to load after clicking
                        print("Clicked on Second Round button.")
                    except Exception as e:
                        print(f"Error while clicking Second Round button: {e}")
                    
                    try:
                        element = WebDriverWait(driver, 1).until(
                            EC.presence_of_element_located(
                                (By.CSS_SELECTOR, "#ctl00_ContentPlaceHolder1_MoeGeneralInfo > table > tbody > tr:nth-child(1) > td > table > tbody > tr")
                            )
                        )
                        text = element.text
                    except NoSuchElementException:
                        text = "Element not found"

                else:  # Get data for First Round
                    try:
                        driver.get(link)
                        time.sleep(2)
   
                        element = WebDriverWait(driver, 1).until(
                            EC.presence_of_element_located(
                                (By.CSS_SELECTOR, "#ctl00_ContentPlaceHolder1_MoeGeneralInfo > table > tbody > tr:nth-child(1) > td > table > tbody > tr")
                            )
                        )
                        text = element.text
                    except NoSuchElementException:
                        text = "Element not found"

                for key in info_dict.keys():
                    match = re.search(f"{key}([^\n]*)", text)
                    if match:
                        info_dict[key] = match.group(1).strip()

            except Exception as e:
                print(f"Error when extracting info: {e}")

            general_informations.append(info_dict)
    
    df = pd.DataFrame(general_informations)
    df.to_csv('general_info.csv', index=False)


def download_documents(link):

    print(link)
    # Create directory, if doesn't exist
    download_dir = link[-3:]
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
    
    # Find PDFs within div through JS path
    pdf_links = driver.find_elements(By.CSS_SELECTOR, "#ctl00_ContentPlaceHolder1_DocumentsSection > div.liens a")
    print(pdf_links)
    # Download PDFs
    for pdf_link in pdf_links:
        pdf_url = pdf_link.get_attribute("href")
        
        if pdf_url:  # Verify if link is a PDF
            print(f"Found PDF: {pdf_url}")
            
            # Generate file name
            file_name = os.path.join(download_dir, pdf_url.split("=")[-1] + ".pdf")

            try:
                response = requests.get(pdf_url, allow_redirects=True)
                if response.status_code == 200:
                    with open(file_name, "wb") as f:
                        f.write(response.content)
                    print(f"PDF downloaded: {file_name}")
                else:
                    print(f"Failed to download: {pdf_url} with status {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"Error downloading {pdf_url}: {e}")

def get_recommendations(driver, link):

    driver.get(link)
    time.sleep(3)

    # Find and click the Recommendations button to load the page
    path_button = driver.find_element(By.CSS_SELECTOR, "#ctl00_ContentPlaceHolder1_RadTabStrip1 > div > ul > li.rtsLI.rtsLast > a")
    path_button.click()
    time.sleep(3)  # wait for the new page to load

    # Find all table rows in the recommendations table
    recommendations_list = []

    try:
        # Loop through each tbody in the table
        tbody_elements = driver.find_elements(By.CSS_SELECTOR, "#ctl00_ContentPlaceHolder1_MoeRecommens > table > tbody")
        
        for i, tbody in enumerate(tbody_elements):
            try:
                # Use XPath to locate the elements
                info_1 = driver.find_element(By.XPATH, f"/html/body/div/div[3]/form/div[4]/div[3]/div[2]/div/div/div/table/tbody[{i}]/tr[1]/td[3]").text
            except NoSuchElementException:
                info_1 = "N/A"  # If the element is not found, assign "N/A"

            try:
                info_2 = driver.execute_script("""
    return document.evaluate('/html/body/div/div[3]/form/div[4]/div[3]/div[2]/div/div/div/table/tbody[' + arguments[0] + ']/tr[2]/td/div/div/div/div/div[2]/span', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue ? document.evaluate('/html/body/div/div[3]/form/div[4]/div[3]/div[2]/div/div/div/table/tbody[' + arguments[0] + ']/tr[2]/td/div/div/div/div/div[2]/span', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.textContent : 'N/A';
""", i)
                info_2.strip()
                info_2 = ' '.join(info_2.split())
            except NoSuchElementException:
                info_2 = "N/A"  # If the element is not found, assign "N/A"

            recommendations_list.append([link[-3:], info_1, info_2])

    except NoSuchElementException:
        print("Recommendations table or element not found")
        
    recommendations_list = np.array(recommendations_list[1:]).flatten()
    reshaped_array = np.array(recommendations_list).reshape(-1, 3)
    header1 = ['id', 'categories', 'description']
    df1 = pd.DataFrame(reshaped_array, columns=header1)
    print(df1)
    
    return df1


if __name__ == "__main__":

    # Selenium configurations
    chrome_options = Options()
    #chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # years list
    years = range(1962, 2025)

    # get every avaiable link
    links = get_avaiable_links(driver, years)
    
    # test_links = ['https://www.oas.org/EOMDatabase/moeInfo.aspx?Lang=En&Id=427', 'https://www.oas.org/EOMDatabase/moeInfo.aspx?Lang=En&Id=447', 'https://www.oas.org/EOMDatabase/moeInfo.aspx?Lang=En&Id=429']

    print(len(links))
    print(links)
    
    # Get general informations for first and second (if exists) round and download documents in PDF
    get_general_informations_and_documents(driver, links)

    # Get recommendations
    recommendations = pd.DataFrame()
    for link in links:
        recommendations = pd.concat([recommendations, get_recommendations(driver, link)], ignore_index=True)
    header1 = ['id', 'categories', 'description']
    df1 = pd.DataFrame(recommendations, columns=header1)
    df1.to_csv('recommendations.csv', index=False)
