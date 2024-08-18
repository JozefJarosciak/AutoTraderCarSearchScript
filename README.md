
# AutoTrader Car Search Script

This Python script automates the process of searching for cars on AutoTrader.ca. It allows users to input search criteria, such as postal code, search radius, mileage, year range, and price, and returns a list of cars that match the criteria. The results are displayed in a formatted table, sorted by the best price-to-mileage ratio.

## Features

- **Multi-make and model search:** Search for multiple car makes and models in a single run.
- **Filtered results:** Filter results based on mileage, year range, and price.
- **Cached results:** Cache search results to reduce unnecessary requests and speed up subsequent searches.
- **Multi-threaded page fetching:** Fetch car pages concurrently for faster performance.
- **Formatted output:** Display results in a clear, readable table format.

## Usage

1. **Install dependencies:**

   Make sure you have Python installed. Then, install the required dependencies by running:

   ```bash
   pip install requests beautifulsoup4 prettytable termcolor
   ```

2. **Run the script:**

   Execute the script in a terminal or command prompt:

   ```bash
   python autotrader_car_search.py
   ```

3. **Input search criteria:**

   The script will prompt you to enter the following:

   - **Postal code:** The postal code to center the search.
   - **Search radius:** The radius in kilometres around the postal code to search.
   - **Maximum mileage:** The maximum mileage of the cars in kilometres.
   - **Year range:** The range of years (e.g., '2015-2020') to search within.
   - **Maximum price:** The maximum price in CAD for the cars.
   - **Makes and models:** A comma-separated list of makes and models to search for (e.g., 'Mazda CX-5, Toyota RAV4, Honda CR-V').

4. **View results:**

   The script will search AutoTrader.ca based on the criteria and display the results in a table, sorted by the best price-to-mileage ratio.

## Example Output

After running the script, you might see an output like this:
![image](https://github.com/user-attachments/assets/763ec132-2bae-443a-9b4f-231f666ebdfb)

## Disclaimer

This script uses web scraping techniques to retrieve data from AutoTrader.ca. It is intended solely for personal, non-commercial use. **Do not use this script in any production environment** or in any manner that violates AutoTrader.ca's terms of service or applicable laws. The author is not responsible for any misuse of this script or any consequences arising from its use.


## License

This project is open-source and available under the MIT License.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue to discuss any changes.
