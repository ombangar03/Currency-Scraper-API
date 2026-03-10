# Currency Scraper API

## Overview

Currency Scraper API is a Python-based project that collects historical currency exchange rate data for multiple currency pairs and stores it in a structured format.
The project is designed to automate the extraction and processing of forex data for analysis and financial applications.

This project demonstrates skills in **Python development, API integration, data extraction, and data processing**.

---

## Features

* Scrapes historical currency exchange data
* Supports multiple currency pairs
* Structured JSON output
* Data cleaning and processing
* Error handling and logging
* Modular Python code structure

---

## Currency Pairs Supported

Example currency pairs supported in this project:

* USD / INR
* EUR / INR
* GBP / INR
* JPY / INR
* AUD / INR
* CAD / INR
* CHF / INR
* SGD / INR

---

## Tech Stack

* Python
* Requests
* Pandas
* JSON
* API Integration

---

## Project Structure

```
Currency-Scraper-API
│
├── main.py
├── currency_scraper.py
├── requirements.txt
└── README.md
```

---

## Installation

Clone the repository:

```
git clone https://github.com/ombangar03/Currency-Scraper-API.git
```

Navigate to the project folder:

```
cd Currency-Scraper-API
```

Install dependencies:

```
pip install -r requirements.txt
```

---

## Usage

Run the scraper:

```
python main.py
```

The script will fetch historical currency data and return it in structured JSON format.

---

## Example Output

```
{
  "pair_key": "USDINR",
  "status": "success",
  "records_saved": 52,
  "date_from": "2020-01-06",
  "date_to": "2020-12-28"
}
```

---

## Learning Outcomes

This project demonstrates:

* Working with financial datasets
* API data extraction
* Data transformation using Python
* Writing modular and reusable code
* Handling errors and structured responses

---

## Author

Om Bangar
GitHub: https://github.com/ombangar03
