"""
Canadian Election Simulator - Polling Data Scraper
Copyright (c) 2025 [Your Name]

This module handles scraping polling data from the CBC Poll Tracker website.
"""

import time
import re
from typing import Optional, Dict, Tuple
import logging

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException, WebDriverException

logging.basicConfig(level=logging.INFO)


def process_province_container(container: WebElement) -> Optional[Tuple[str, Dict[str, float]]]:
    """
    Process a single province container to extract the province name and its polling data.

    Args:
        container (WebElement): The container element for a province.

    Returns:
        Optional[Tuple[str, Dict[str, float]]]: A tuple containing the province name and a dictionary
        of party polling data if successful, or None if an error occurs.
    """
    try:
        province_name = container.find_element(By.CSS_SELECTOR, ".MuiTypography-BreakDownsChartHeading").text
        chart = container.find_element(By.CSS_SELECTOR, ".recharts-surface")
        aria_label = chart.get_attribute("aria-label")
        matches = re.findall(r"([\w\s]+):\s(\d+\.\d+)%", aria_label)
        province_data = {p.strip(): float(percent) / 100 for p, percent in matches}
        parties = ["LIB", "CON", "NDP", "GRN", "BQ", "PPC", "OTH"]
        for party in parties:
            province_data.setdefault(party, 0.0)
        return province_name, province_data
    except NoSuchElementException as e:
        logging.error("Error processing province container: %s", e)
        return None


def scrape_polling_data() -> Optional[Dict[str, Dict[str, float]]]:
    """
    Scrapes current polling data from CBC Poll Tracker website.

    Returns:
        Optional[Dict[str, Dict[str, float]]]: A dictionary with provinces as keys and party polling
        percentages as values, or None if an error occurs.
    """
    driver = webdriver.Chrome()
    driver.get("https://newsinteractives.cbc.ca/elections/poll-tracker/canada/")
    time.sleep(5)

    polling_data: Dict[str, Dict[str, float]] = {}

    try:
        province_containers = driver.find_elements(By.CSS_SELECTOR, ".eachBreakdownChartInnerWrapper")
        for container in province_containers:
            result = process_province_container(container)
            if result is not None:
                province_name, province_data = result
                polling_data[province_name] = province_data
        return polling_data
    except WebDriverException as e:
        logging.error("Error scraping polling data: %s", e)
        return None
    finally:
        driver.quit()


if __name__ == "__main__":
    # Test the scraper
    poll_data = scrape_polling_data()
    if poll_data:
        logging.info("Polling data by province:")
        for province, data in poll_data.items():
            logging.info("%s: %s", province, data)
    else:
        logging.error("No polling data found.")

if __name__ == '__main__':
    import doctest
    import python_ta

    doctest.testmod()

    python_ta.check_all(config={
        'extra-imports': [],
        'allowed-io': [],
        'max-line-length': 120
    })
