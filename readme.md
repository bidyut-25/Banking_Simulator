Zenith Core Banking - A Python Streamlit Simulation
===================================================

Welcome to Zenith Core Banking, a comprehensive simulation of a mini core banking system built entirely in Python using the Streamlit framework and an SQL backend. This application provides a dual-interface system for both customers and bank staff, demonstrating key banking operations, ACID-compliant transactions, and automated financial reporting.

✨ Features
----------

This project is a single-file, fully functional application with a robust set of features:

### 👤 Customer Portal

-   Secure Login: Customers log in using their email and a securely hashed password.

-   Dashboard Overview: A clean dashboard displays total balance and a summary of all accounts.

-   ACID-Compliant Transactions:

-   Fund Transfers: Seamlessly transfer money to any other account holder in the system. Transactions are atomic; they either complete fully or not at all.

-   Deposits & Withdrawals: Simple interfaces for managing account funds.

-   Transaction History: A detailed, filterable log of all past transactions.

-   Loan System: Customers can apply for loans and monitor the status of their applications (Pending, Approved, Rejected).

### 🏦 Bank Staff Portal

-   Secure Staff Login: Bank employees log in with a unique username and password.

-   Administrative Dashboard: An at-a-glance view of key bank metrics like total customers, total deposits, and pending loan applications.

-   Loan Management: A dedicated section to review and either approve or reject pending customer loan applications. Approved loans automatically disburse funds to the customer's account.

-   Automated Financial Reporting:

-   Balance Sheet: Dynamically generated report showing the bank's assets, liabilities, and equity.

-   Income Statement: A simplified report on revenue (loan interest) vs. expenses.

-   Cash Flow Statement: Tracks the movement of cash from deposits, withdrawals, and loan disbursements.

-   Audit Trail: A comprehensive log that records every significant action taken within the system for security and traceability.

### 🛠️ Technical Highlights

-   Single-File Application: The entire project---frontend, backend, styling, and logic---is contained within a single Python script (core_banking_app.py) for simplicity and portability.

-   SQL Backend: Uses Python's built-in sqlite3 for a lightweight, serverless database.

-   ACID Compliance: Employs SQL BEGIN TRANSACTION, COMMIT, and ROLLBACK statements to ensure data integrity during complex operations like fund transfers.

-   Synthetic Data: On first run, the application automatically populates the database with realistic, fake customer and transaction data using the Faker library.

-   Secure by Design: Passwords are never stored in plain text. They are salted and hashed using hashlib before database insertion.

-   Modular Code: Despite being a single file, the code is organized into logical sections for the database, security, UI components, and business logic.

-   Modern UI/UX: Styled with custom CSS injected into Streamlit for a clean, professional, and user-friendly interface.

🚀 How to Run the Application
-----------------------------

This project is easy to set up and run. All you need is Python and a few standard packages.

### Prerequisites

-   Python 3.8+

-   pip (Python package installer)

### Installation

1.  Clone the repository (or save the core_banking_app.py file):\
    git clone [https://github.com/your-username/core-banking-system.git](https://github.com/your-username/core-banking-system.git)\
    cd core-banking-system

2.  Create a virtual environment (recommended):\
    python -m venv venv\
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

3.  Install the required packages:\
    pip install streamlit pandas faker

### Running the App

1.  Navigate to the directory containing core_banking_app.py.

2.  Run the following command in your terminal:\
    streamlit run core_banking_app.py

3.  Your web browser will automatically open a new tab with the application running.

### Default Login Credentials

The application generates synthetic data on its first run, including default credentials to get you started.

Bank Staff:

-   Username: admin

-   Password: adminpass

Customers:

-   Email: john.doe0@email.com, jane.smith1@email.com, etc.

-   Password: custpass0, custpass1, etc. (The number corresponds to the customer's generated ID).

🗃️ Database Schema
-------------------

The backend is powered by a relational SQLite database with the following tables:

-   customers: Stores customer profiles.

-   accounts: Holds details for each customer's savings and checking accounts.

-   transactions: A ledger of all deposits, withdrawals, and transfers.

-   loans: Tracks loan applications and their lifecycle.

-   bank_staff: Contains credentials for bank employees.

-   audit_log: Records all critical system events.

Each table is carefully designed with appropriate keys and relationships to maintain data integrity. The SQL queries used are commented within the code to explain their purpose, especially for complex transactional logic.