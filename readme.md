Banking Simulator - A Python Streamlit Simulation
===================================================

Welcome to Banking Simulator, a comprehensive simulation of a mini core banking system built entirely in Python using the Streamlit framework and an SQL backend. This application provides a dual-interface system for both customers and bank staff, demonstrating key banking operations, ACID-compliant transactions, and automated financial reporting.

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

-   Modern UI/UX: Styled with custom CSS injected into Streamlit for a clean, professional, and user-friendly interface

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
