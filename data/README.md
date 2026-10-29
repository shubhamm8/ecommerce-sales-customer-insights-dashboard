# Data Directory

This directory contains datasets used for testing and demonstration of the AI-Powered E-Commerce Sales and Customer Insights Dashboard.

## Available Files

- `sample_ecommerce.csv`: A synthetic, realistic e-commerce transactional dataset modeled after the public UCI Online Retail benchmark dataset.
  - Rows: 1,500+ records
  - Time range: Multi-month / multi-year historical span
  - Columns:
    - `InvoiceNo`: Unique invoice number (prefix `C` indicates a cancelled/refund transaction)
    - `StockCode`: Unique product SKU
    - `Description`: Product name/description
    - `Quantity`: Ordered unit count (negative for cancellations)
    - `InvoiceDate`: Timestamp of purchase (`YYYY-MM-DD HH:MM:SS`)
    - `UnitPrice`: Unit price in GBP/USD
    - `CustomerID`: Unique customer identifier (nullable for guest checkouts)
    - `Country`: Geographical destination of transaction

## External Datasets

You can download the original UCI Online Retail dataset or similar Kaggle datasets:
- **UCI Machine Learning Repository: Online Retail**:
  [https://archive.ics.uci.edu/dataset/352/online+retail](https://archive.ics.uci.edu/dataset/352/online+retail)
- To use an external file, upload the `.csv` or `.xlsx` file directly inside the Streamlit web dashboard.
- The system automatically maps common column names and validates schema requirements.
