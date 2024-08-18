import json
import logging
import os
import re
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup
from prettytable import PrettyTable
from termcolor import colored

logging.basicConfig(level=logging.INFO)

URL_BASE = "https://www.autotrader.ca"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"
}

CACHE_DAYS = 7
CACHE_FOLDER = "autotrader-cars"
os.makedirs(CACHE_FOLDER, exist_ok=True)

# Delay between different car model searches (in seconds)
SEARCH_DELAY = 2  # 5-second delay

# Define colors for different makes
MAKE_COLORS = {
    "Mazda": "cyan",
    "Toyota": "green",
    "Honda": "yellow"
}


def search_autotrader(make: str, model: str, postal_code: str, radius_km: int = 100, display_results: int = 100) -> Optional[BeautifulSoup]:
    try:
        url = (
                URL_BASE
                + "/cars/?"
                + "&".join(
            [f"loc={postal_code}", f"make={make}", f"mdl={model}", f"prx={radius_km}", f"rcp={display_results}"]
        ).replace(" ", "%20")
        )
        #logging.info(f"Requesting URL: {url}")
        response = requests.get(url, timeout=15, headers=HEADERS)
        response.raise_for_status()
        return BeautifulSoup(response.content, "html.parser")
    except requests.RequestException as e:
        logging.error(f"Error fetching search results for {make} {model}: {e}")
        return None


def get_car_page_urls(search_page: BeautifulSoup) -> List[str]:
    tags = search_page.find_all("a", attrs={"class": ["detail-price-area", "inner-link"]})
    car_page_urls = [URL_BASE + tag.get("href") for tag in tags if tag.get("href")]
    return list(set(car_page_urls))


def is_url_cached(url: str) -> bool:
    cache_file = os.path.join(CACHE_FOLDER, re.sub(r'[^\w]', '_', url) + ".json")
    if os.path.exists(cache_file):
        last_modified_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
        if datetime.now() - last_modified_time < timedelta(days=CACHE_DAYS):
            return True
    return False


def save_url_cache(url: str, car_data: Dict):
    cache_file = os.path.join(CACHE_FOLDER, re.sub(r'[^\w]', '_', url) + ".json")
    with open(cache_file, 'w') as f:
        json.dump(car_data, f)


def load_url_cache(url: str) -> Optional[Dict]:
    cache_file = os.path.join(CACHE_FOLDER, re.sub(r'[^\w]', '_', url) + ".json")
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            return json.load(f)
    return None


def fetch_car_page(url: str) -> Optional[Union[BeautifulSoup, Dict]]:
    if is_url_cached(url):
        return load_url_cache(url)

    try:
        response = requests.get(url, timeout=15, headers=HEADERS)
        response.raise_for_status()
        return BeautifulSoup(response.content, "html.parser")
    except requests.RequestException as e:
        logging.error(f"Error fetching car page {url}: {e}")
        return None


def get_car_pages(car_page_urls: List[str]) -> List[Union[BeautifulSoup, Dict]]:
    car_pages = []
    with ThreadPoolExecutor() as executor:
        future_to_url = {executor.submit(fetch_car_page, url): url for url in car_page_urls}
        for future in as_completed(future_to_url):
            car_page = future.result()
            if car_page:
                car_pages.append(car_page)
    return car_pages


def extract_car_data(car_page: Union[BeautifulSoup, Dict]) -> Dict:
    if isinstance(car_page, Dict):
        return car_page

    scripts = car_page.find_all("script", {"type": "application/ld+json"})
    if len(scripts) < 2:
        return {}

    json_data = json.loads(scripts[1].text)
    car_data = {
        "url": json_data.get("url"),
        "name": json_data.get("name"),
        "make": json_data["brand"]["name"],
        "model": json_data.get("model"),
        "year": json_data.get("vehicleModelDate"),
        "color": json_data.get("color"),
        "mileage": json_data.get("mileageFromOdometer", {}).get("value"),
        "price": json_data.get("offers", {}).get("price"),
        "location": json_data.get("offers", {}).get("eligibleRegion"),
        "vehicle_configuration": json_data.get("vehicleConfiguration"),
    }

    return {k: v for k, v in car_data.items() if v is not None}


def filter_and_rank_cars(car_data_list: List[Dict], max_mileage_km: int, year_range: str, max_price: int) -> List[Dict]:
    year_start, year_end = (None, None)
    if year_range:
        year_start, year_end = map(int, year_range.split('-'))

    filtered_cars = []

    for car_data in car_data_list:
        mileage = car_data.get("mileage")
        year = car_data.get("year")
        price = car_data.get("price")

        if mileage is not None:
            mileage = int(mileage)
        if year is not None:
            year = int(year)
        if price is not None:
            price = float(price)

        if (max_mileage_km == 0 or (mileage is not None and mileage <= max_mileage_km)) and \
                (year_start is None or (year is not None and year_start <= year <= year_end)) and \
                (max_price == 0 or (price is not None and price <= max_price)):
            filtered_cars.append(car_data)

    return sorted(filtered_cars, key=lambda car: (float(car.get("price", 0) or 0), float(car.get("mileage", 0) or 0)))


def display_cars_table(cars: List[Dict], title: str):
    print()
    print(f"{title} (sorted by best price/mileage ratio):")
    print()

    if not cars:
        print("No results found.")
        return

    table = PrettyTable()
    table.field_names = ["#", "Make", "Model", "Year", "Mileage (km)", "Price", "Location", "Color", "Configuration", "URL"]

    for idx, car in enumerate(cars, start=1):
        make = car.get("make")
        mileage = car.get("mileage")
        price = car.get("price")
        color = MAKE_COLORS.get(make, "white")  # Default to white if make not in MAKE_COLORS

        if mileage is not None:
            mileage = f"{int(mileage):,}"  # Format mileage with a thousand separator
        else:
            mileage = "N/A"
        if price is not None:
            price = f"{int(price):,}"  # Format price with a thousand separator

        table.add_row([
            idx,
            colored(make, color),
            car.get("model"),
            car.get("year"),
            mileage,
            price,
            car.get("location"),
            car.get("color"),
            car.get("vehicle_configuration"),
            car.get("url"),
        ])

    print(table)


def main():
    postal_code = input("Enter your postal code: ")
    radius_km = int(input("Enter the search radius in kilometers: "))
    max_mileage_km = int(input("Enter the maximum mileage in kilometers: "))
    year_range = input("Enter the year range (e.g., '2015-2020'): ")
    max_price = int(input("Enter the maximum price in CAD: "))
    search_prompt = input("Enter the makes and models you want to search for (comma-separated, e.g., 'Mazda CX-5, Toyota RAV4, Honda CR-V'): ")

    car_search_terms = [term.strip() for term in search_prompt.split(',')]
    car_data_list = []

    for term in car_search_terms:
        # Split based on the first space only, keeping the rest as the model
        make_model = term.split(maxsplit=1)
        if len(make_model) == 2:
            make, model = make_model
        else:
            make = make_model[0]
            model = ''

        logging.info(f"Searching for {make} {model} within {radius_km} km of {postal_code}")
        search_page = search_autotrader(make, model, postal_code, radius_km)

        if search_page:
            car_page_urls = get_car_page_urls(search_page)

            car_pages = get_car_pages(car_page_urls)
            if not car_pages:
                logging.warning(f"No pages found for {make} {model}. Skipping to next term.")
                continue

            for car_page in car_pages:
                car_data = extract_car_data(car_page)
                if 'url' in car_data:
                    save_url_cache(car_data['url'], car_data)
                    car_data_list.append(car_data)

        # Introduce a delay before the next search
        time.sleep(SEARCH_DELAY)

    if not car_data_list:
        logging.error("No car data was collected. Exiting.")
        exit(0)

    # Filter and rank the cars
    filtered_and_ranked_cars = filter_and_rank_cars(car_data_list, max_mileage_km, year_range, max_price)

    # Display the combined results
    display_cars_table(filtered_and_ranked_cars, "Total Combined Filtered Results")



if __name__ == "__main__":
    main()
