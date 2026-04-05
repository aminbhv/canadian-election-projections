"""
Canadian Election Simulator - Polling Data Scraper

Copyright (c) 2025 Amin Behbudov, Fares Abdulmajeed Alabdulhadi, Tahmid Wasif Zaman, Dimural Murat.

This module handles scraping polling data from the CBC Poll Tracker website.
"""

import re
import time
import logging
from typing import Dict, Optional, Tuple

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException, WebDriverException

logging.basicConfig(level=logging.INFO)


def process_province_container(
    container: WebElement,
) -> Optional[Tuple[str, Dict[str, float]]]:
    """
    Process a single province container to extract polling data.

    Args:
        container (WebElement): The container element for a province.

    Returns:
        Optional[Tuple[str, Dict[str, float]]]: Province name and party polling
        percentages, or None if extraction fails.
    """
    try:
        province_name = container.find_element(
            By.CSS_SELECTOR, ".MuiTypography-BreakDownsChartHeading"
        ).text

        chart = container.find_element(By.CSS_SELECTOR, ".recharts-surface")
        aria_label = chart.get_attribute("aria-label")
        matches = re.findall(r"([\w\s]+):\s(\d+\.\d+)%", aria_label)
        province_data = {p.strip(): float(pct) / 100 for p, pct in matches}

        # Ensure all expected parties are present
        for party in ["LIB", "CON", "NDP", "GRN", "BQ", "PPC", "OTH"]:
            province_data.setdefault(party, 0.0)

        return province_name, province_data

    except NoSuchElementException as e:
        logging.error("Error processing province container: %s", e)
        return None


def scrape_polling_data() -> Optional[Dict[str, Dict[str, float]]]:
    """
    Scrape current polling data from the CBC Poll Tracker.

    Returns:
        Optional[Dict[str, Dict[str, float]]]: Province-keyed dictionary of
        party polling percentages, or None if scraping fails.
    """
    driver = webdriver.Chrome()
    driver.get("https://newsinteractives.cbc.ca/elections/poll-tracker/canada/")
    time.sleep(5)

    polling_data: Dict[str, Dict[str, float]] = {}

    try:
        containers = driver.find_elements(
            By.CSS_SELECTOR, ".eachBreakdownChartInnerWrapper"
        )
        for container in containers:
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
    poll_data = scrape_polling_data()
    if poll_data:
        logging.info("Polling data by province:")
        for province, data in poll_data.items():
            logging.info("%s: %s", province, data)
    else:
        logging.error("No polling data found.")
