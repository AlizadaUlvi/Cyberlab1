# Cyberlab1
### Explanation of the Amazon Price Tracking Project

This project is designed to monitor product prices on the Amazon platform using **Python and Selenium**. The main objective is to automatically visit Amazon product pages, extract price information, record price changes over time, and provide evidence of execution through saved screenshots and logs.

The program starts by reading a list of Amazon product links from a CSV file. Each product entry includes the product name, its Amazon URL, and an optional target price. This allows the script to track multiple products in a single run and evaluate whether a price has fallen below a desired threshold.

Selenium WebDriver is used to automate the Chrome browser. The browser can run in headless mode (without a visible window) or normal mode, depending on the configuration. A custom user-agent is applied to reduce the chance of Amazon blocking the request as an automated bot. Once a product page is opened, the script waits briefly to ensure that all page elements are fully loaded.

For each product page, the script performs three key actions. First, it captures a screenshot of the page and saves it locally. These screenshots serve as visual proof that the page was accessed and are intended to be included in the project report. Second, it extracts the product title and price by checking several common HTML elements used by Amazon to display pricing information. Because Amazon’s layout may vary by region and product type, multiple selectors are tried to improve reliability. Third, the extracted price text is cleaned and converted into a numerical value so it can be stored and compared.

All collected data is appended to a CSV file that acts as a price history log. Each record includes the date and time of the check, product name, URL, extracted title, detected price, raw price text, target price, and a status message. The status indicates whether the price was successfully found, whether it could not be detected, or whether the target price condition has been met.

The project is version-controlled using Git and published to GitHub. This demonstrates proper software development practices, including reproducibility, transparency, and code sharing. By pushing the full project (source code, requirements file, and README) to GitHub, the work becomes easy to review, run, and extend by others.

Overall, this project demonstrates practical web automation, data extraction, file-based logging, and basic monitoring logic, making it suitable as an academic or introductory automation assignment.
