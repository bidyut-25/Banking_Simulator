import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import time
from faker import Faker
from datetime import datetime, timedelta

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Zenith Core Banking",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- STYLING ---
# A function to load and inject CSS for a more polished look
def load_css():
    """Inject custom CSS to style the Streamlit app."""
    st.markdown("""
    <style>
        /* General styling */
        .stApp {
            background-color: #F0F2F6;
        }

        /* Main content area */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            padding-left: 5rem;
            padding-right: 5rem;
        }

        /* Sidebar styling */
        .st-emotion-cache-16txtl3 {
            background-color: #FFFFFF;
            border-right: 1px solid #E0E0E0;
        }

        /* Custom title */
        .title {
            font-size: 3rem;
            font-weight: bold;
            color: #1E3A8A; /* A deep blue */
            text-align: center;
            padding: 1rem;
        }

        /* Metric cards */
        .st-emotion-cache-1b0udgb {
            background-color: #FFFFFF;
            border-radius: 10px;
            padding: 20px !important;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            border-left: 5px solid #1E3A8A;
        }

        /* Buttons */
        .stButton>button {
            border-radius: 8px;
            padding: 10px 20px;
            font-weight: bold;
            border: none;
            color: white;
            background-color: #2563EB; /* A vibrant blue */
            transition: background-color 0.3s, box-shadow 0.3s;
        }

        .stButton>button:hover {
            background-color: #1E40AF;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }

        /* Login/Logout buttons */
        .stButton[kind="secondary"]>button {
            background-color: #DC2626; /* Red for logout/cancel */
        }
        .stButton[kind="secondary"]>button:hover {
            background-color: #B91C1C;
        }

    </style>
    """, unsafe_allow_html=True)

# --- DATABASE SETUP ---
DB_NAME = "banking.db"

class Database:
    """Handles all database interactions for the banking system."""

    def __init__(self, db_name):
        self.db_name = db_name
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()

    def execute_query(self, query, params=()):
        """Executes a given SQL query."""
        try:
            self.cursor.execute(query, params)
            self.conn.commit()
            return self.cursor
        except sqlite3.Error as e:
            st.error(f"Database error: {e}")
            return None

    def fetch_one(self, query, params=()):
        """Fetches a single record."""
        cursor = self.execute_query(query, params)
        if cursor:
            return cursor.fetchone()
        return None

    def fetch_all(self, query, params=()):
        """Fetches all records."""
        cursor = self.execute_query(query, params)
        if cursor:
            return cursor.fetchall()
        return []

    def close(self):
        """Closes the database connection."""
        self.conn.close()

db = Database(DB_NAME)

def setup_database():
    """Creates all necessary tables if they don't exist."""
    # Customer Table
    db.execute_query("""
    CREATE TABLE IF NOT EXISTS customers (
        customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Accounts Table
    db.execute_query("""
    CREATE TABLE IF NOT EXISTS accounts (
        account_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        account_number TEXT UNIQUE NOT NULL,
        account_type TEXT NOT NULL,
        balance REAL NOT NULL DEFAULT 0.0,
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    );
    """)

    # Transactions Table
    db.execute_query("""
    CREATE TABLE IF NOT EXISTS transactions (
        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_account_id INTEGER,
        to_account_id INTEGER,
        transaction_type TEXT NOT NULL,
        amount REAL NOT NULL,
        description TEXT,
        transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (from_account_id) REFERENCES accounts(account_id),
        FOREIGN KEY (to_account_id) REFERENCES accounts(account_id)
    );
    """)

    # Loans Table
    db.execute_query("""
    CREATE TABLE IF NOT EXISTS loans (
        loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        loan_amount REAL NOT NULL,
        interest_rate REAL NOT NULL,
        term_months INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'Pending', -- Pending, Approved, Rejected, Paid
        application_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        approval_date TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    );
    """)

    # Bank Staff Table (for bank-side login)
    db.execute_query("""
    CREATE TABLE IF NOT EXISTS bank_staff (
        staff_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL -- e.g., 'Manager', 'Teller'
    );
    """)
    
    # Audit Log Table
    db.execute_query("""
    CREATE TABLE IF NOT EXISTS audit_log (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT, -- Can be customer_id or staff_id
        action TEXT NOT NULL,
        details TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)


# --- SYNTHETIC DATA GENERATION ---
def generate_synthetic_data(num_customers=20):
    """Populates the database with synthetic data if it's empty."""
    fake = Faker()
    # Check if data already exists
    if db.fetch_one("SELECT COUNT(*) FROM customers")[0] > 0:
        return

    # Generate Bank Staff
    hashed_password = hash_password("adminpass")
    db.execute_query("INSERT OR IGNORE INTO bank_staff (username, password_hash, role) VALUES (?, ?, ?)",
                     ('admin', hashed_password, 'Manager'))

    # Generate Customers
    for i in range(num_customers):
        first_name = fake.first_name()
        last_name = fake.last_name()
        email = f"{first_name.lower()}.{last_name.lower()}{i}@email.com"
        password = f"custpass{i}"
        hashed_password = hash_password(password)
        
        customer_id = db.execute_query(
            "INSERT INTO customers (first_name, last_name, email, password_hash) VALUES (?, ?, ?, ?)",
            (first_name, last_name, email, hashed_password)
        ).lastrowid
        
        # Create a savings and checking account for each customer
        account_number_sav = f"SAV{str(customer_id).zfill(8)}"
        account_number_chk = f"CHK{str(customer_id).zfill(8)}"
        
        initial_balance_sav = fake.random_int(min=500, max=50000)
        initial_balance_chk = fake.random_int(min=100, max=10000)

        db.execute_query(
            "INSERT INTO accounts (customer_id, account_number, account_type, balance) VALUES (?, ?, ?, ?)",
            (customer_id, account_number_sav, 'Savings', initial_balance_sav)
        )
        db.execute_query(
            "INSERT INTO accounts (customer_id, account_number, account_type, balance) VALUES (?, ?, ?, ?)",
            (customer_id, account_number_chk, 'Checking', initial_balance_chk)
        )
    st.toast("Synthetic data generated successfully!", icon="🎉")

# --- SECURITY ---
def hash_password(password):
    """Hashes a password for secure storage."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_hash, provided_password):
    """Verifies a provided password against a stored hash."""
    return stored_hash == hash_password(provided_password)

# --- HELPER FUNCTIONS ---
def log_audit(user_id, action, details=""):
    """Logs an action to the audit log."""
    db.execute_query("INSERT INTO audit_log (user_id, action, details) VALUES (?, ?, ?)",
                     (str(user_id), action, details))

# --- UI COMPONENTS & PAGES ---

def login_page():
    """Renders the main login page for both customers and bank staff."""
    st.markdown('<p class="title">Zenith Core Banking</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.subheader("Customer Login")
        customer_email = st.text_input("Email", key="customer_email")
        customer_password = st.text_input("Password", type="password", key="customer_password")
        if st.button("Customer Login"):
            customer = db.fetch_one("SELECT * FROM customers WHERE email = ?", (customer_email,))
            if customer and verify_password(customer[4], customer_password):
                st.session_state['logged_in'] = True
                st.session_state['user_type'] = 'customer'
                st.session_state['user_info'] = customer
                log_audit(customer[0], "Customer Login Success")
                st.rerun()
            else:
                st.error("Invalid email or password.")
                log_audit(customer_email, "Customer Login Failed")

    with col2:
        st.subheader("Bank Staff Login")
        staff_username = st.text_input("Username", key="staff_username")
        staff_password = st.text_input("Password", type="password", key="staff_password")
        if st.button("Staff Login"):
            staff = db.fetch_one("SELECT * FROM bank_staff WHERE username = ?", (staff_username,))
            if staff and verify_password(staff[2], staff_password):
                st.session_state['logged_in'] = True
                st.session_state['user_type'] = 'staff'
                st.session_state['user_info'] = staff
                log_audit(staff[0], "Staff Login Success")
                st.rerun()
            else:
                st.error("Invalid username or password.")
                log_audit(staff_username, "Staff Login Failed")

def customer_dashboard():
    """Displays the main dashboard for a logged-in customer."""
    customer_id = st.session_state['user_info'][0]
    first_name = st.session_state['user_info'][1]
    
    st.title(f"Welcome, {first_name}!")
    st.markdown("Your financial overview at a glance.")
    
    accounts = db.fetch_all("SELECT account_id, account_number, account_type, balance FROM accounts WHERE customer_id = ?", (customer_id,))
    
    if not accounts:
        st.warning("You have no accounts with us yet.")
        return
        
    total_balance = sum(acc[3] for acc in accounts)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Total Balance", value=f"${total_balance:,.2f}")
    with col2:
        st.metric(label="Number of Accounts", value=len(accounts))

    st.subheader("Your Accounts")
    for acc in accounts:
        with st.container(border=True):
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"**{acc[2]} Account**")
            c2.markdown(f"*{acc[1]}*")
            c3.markdown(f"**Balance: ${acc[3]:,.2f}**")

def customer_transactions():
    """Handles deposits, withdrawals, and transfers for a customer."""
    customer_id = st.session_state['user_info'][0]
    accounts = db.fetch_all("SELECT account_id, account_number, account_type, balance FROM accounts WHERE customer_id = ?", (customer_id,))
    
    if not accounts:
        st.warning("You need an account to perform transactions.")
        return
        
    account_options = {f"{acc[2]} ({acc[1]}) - Balance: ${acc[3]:,.2f}": acc[0] for acc in accounts}

    st.header("Perform a Transaction")
    
    tab1, tab2, tab3 = st.tabs(["💸 Transfer", "📥 Deposit", "📤 Withdraw"])

    with tab1:
        st.subheader("Transfer Funds")
        from_account_choice = st.selectbox("From Account", options=account_options.keys(), key="transfer_from")
        from_account_id = account_options[from_account_choice]
        
        to_account_number = st.text_input("Recipient Account Number")
        amount = st.number_input("Amount", min_value=0.01, step=0.01, format="%.2f", key="transfer_amount")
        description = st.text_area("Description (Optional)", key="transfer_desc")

        if st.button("Execute Transfer"):
            # SQL for transfer is wrapped in a transaction
            try:
                # 1. Check recipient account exists
                to_account = db.fetch_one("SELECT account_id, customer_id FROM accounts WHERE account_number = ?", (to_account_number,))
                if not to_account:
                    st.error("Recipient account number does not exist.")
                    return
                to_account_id = to_account[0]
                
                if from_account_id == to_account_id:
                    st.error("Cannot transfer to the same account.")
                    return

                # 2. Check for sufficient funds
                sender_balance = db.fetch_one("SELECT balance FROM accounts WHERE account_id = ?", (from_account_id,))[0]
                if sender_balance < amount:
                    st.error("Insufficient funds for this transfer.")
                    return

                # 3. Begin Transaction
                db.execute_query("BEGIN TRANSACTION;")
                
                # 4. Debit sender
                db.execute_query("UPDATE accounts SET balance = balance - ? WHERE account_id = ?", (amount, from_account_id))
                
                # 5. Credit receiver
                db.execute_query("UPDATE accounts SET balance = balance + ? WHERE account_id = ?", (amount, to_account_id))
                
                # 6. Log transaction for sender
                db.execute_query("""
                    INSERT INTO transactions (from_account_id, to_account_id, transaction_type, amount, description)
                    VALUES (?, ?, 'Transfer', ?, ?)
                """, (from_account_id, to_account_id, amount, f"To {to_account_number}: {description}"))
                
                # 7. Commit
                # db.execute_query("COMMIT;")
                
                st.success(f"Successfully transferred ${amount:,.2f} to account {to_account_number}.")
                log_audit(customer_id, "Transfer Success", f"Amount: {amount}, From: {from_account_id}, To: {to_account_id}")

            except Exception as e:
                db.execute_query("ROLLBACK;") # Rollback on any failure
                st.error(f"An error occurred. Transaction rolled back. Details: {e}")
                log_audit(customer_id, "Transfer Failed", f"Error: {e}")

    with tab2:
        st.subheader("Deposit Funds")
        deposit_account_choice = st.selectbox("To Account", options=account_options.keys(), key="deposit_to")
        deposit_account_id = account_options[deposit_account_choice]
        deposit_amount = st.number_input("Amount", min_value=0.01, step=0.01, format="%.2f", key="deposit_amount")
        
        if st.button("Make Deposit"):
            try:
                db.execute_query("BEGIN TRANSACTION;")
                db.execute_query("UPDATE accounts SET balance = balance + ? WHERE account_id = ?", (deposit_amount, deposit_account_id))
                db.execute_query("""
                    INSERT INTO transactions (to_account_id, transaction_type, amount, description)
                    VALUES (?, 'Deposit', ?, 'Cash/Check Deposit')
                """, (deposit_account_id, deposit_amount))
                #db.execute_query("COMMIT;")
                st.success(f"Successfully deposited ${deposit_amount:,.2f}.")
                log_audit(customer_id, "Deposit Success", f"Amount: {deposit_amount}, To: {deposit_account_id}")
            except Exception as e:
                db.execute_query("ROLLBACK;")
                st.error(f"Deposit failed. Transaction rolled back. Error: {e}")
                log_audit(customer_id, "Deposit Failed", f"Error: {e}")
    
    with tab3:
        st.subheader("Withdraw Funds")
        withdraw_account_choice = st.selectbox("From Account", options=account_options.keys(), key="withdraw_from")
        withdraw_account_id = account_options[withdraw_account_choice]
        withdraw_amount = st.number_input("Amount", min_value=0.01, step=0.01, format="%.2f", key="withdraw_amount")

        if st.button("Make Withdrawal"):
            current_balance = db.fetch_one("SELECT balance FROM accounts WHERE account_id = ?", (withdraw_account_id,))[0]
            if current_balance < withdraw_amount:
                st.error("Insufficient funds.")
            else:
                try:
                    db.execute_query("BEGIN TRANSACTION;")
                    db.execute_query("UPDATE accounts SET balance = balance - ? WHERE account_id = ?", (withdraw_amount, withdraw_account_id))
                    db.execute_query("""
                        INSERT INTO transactions (from_account_id, transaction_type, amount, description)
                        VALUES (?, 'Withdrawal', ?, 'Cash Withdrawal')
                    """, (withdraw_account_id, withdraw_amount))
                    #db.execute_query("COMMIT;")
                    st.success(f"Successfully withdrew ${withdraw_amount:,.2f}.")
                    log_audit(customer_id, "Withdrawal Success", f"Amount: {withdraw_amount}, From: {withdraw_account_id}")
                except Exception as e:
                    db.execute_query("ROLLBACK;")
                    st.error(f"Withdrawal failed. Transaction rolled back. Error: {e}")
                    log_audit(customer_id, "Withdrawal Failed", f"Error: {e}")

def customer_history():
    """Shows the transaction history for a customer's accounts."""
    st.header("Transaction History")
    customer_id = st.session_state['user_info'][0]
    
    # Query to fetch all transactions linked to the customer's accounts
    query = """
    SELECT
        t.transaction_date,
        t.description,
        t.transaction_type,
        CASE
            WHEN t.from_account_id IN (SELECT account_id FROM accounts WHERE customer_id = ?) THEN -t.amount
            ELSE t.amount
        END as amount,
        a.account_type || ' (' || a.account_number || ')' as account
    FROM transactions t
    JOIN accounts a ON a.account_id =
        CASE
            WHEN t.from_account_id IN (SELECT account_id FROM accounts WHERE customer_id = ?) THEN t.from_account_id
            ELSE t.to_account_id
        END
    WHERE 
        t.from_account_id IN (SELECT account_id FROM accounts WHERE customer_id = ?) OR
        t.to_account_id IN (SELECT account_id FROM accounts WHERE customer_id = ?)
    ORDER BY t.transaction_date DESC;
    """
    
    transactions = db.fetch_all(query, (customer_id, customer_id, customer_id, customer_id))
    
    if transactions:
        df = pd.DataFrame(transactions, columns=["Date", "Description", "Type", "Amount ($)", "Account"])
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        st.dataframe(df.style.apply(lambda x: ['color: red' if x.name == 'Amount ($)' and v < 0 else 'color: green' for v in x], axis=0),
                     use_container_width=True, hide_index=True)
    else:
        st.info("No transaction history found.")

def customer_loans():
    """Allows customers to apply for loans and view existing loan statuses."""
    st.header("Loans")
    customer_id = st.session_state['user_info'][0]

    tab1, tab2 = st.tabs(["Apply for a New Loan", "View My Loans"])

    with tab1:
        st.subheader("Loan Application Form")
        with st.form("loan_application"):
            loan_amount = st.number_input("Loan Amount ($)", min_value=1000.0, step=100.0, format="%.2f")
            interest_rate = 5.0  # Fixed rate for simplicity
            st.info(f"The current fixed interest rate is {interest_rate}%.")
            term_months = st.selectbox("Loan Term (Months)", [12, 24, 36, 48, 60])
            
            submitted = st.form_submit_button("Submit Application")
            if submitted:
                db.execute_query("""
                    INSERT INTO loans (customer_id, loan_amount, interest_rate, term_months, status)
                    VALUES (?, ?, ?, ?, 'Pending')
                """, (customer_id, loan_amount, interest_rate, term_months))
                st.success("Your loan application has been submitted successfully! You will be notified of the decision.")
                log_audit(customer_id, "Loan Application Submitted", f"Amount: {loan_amount}, Term: {term_months}")

    with tab2:
        st.subheader("Your Loan Status")
        loans = db.fetch_all("SELECT loan_amount, interest_rate, term_months, status, application_date FROM loans WHERE customer_id = ?", (customer_id,))
        if loans:
            df = pd.DataFrame(loans, columns=["Amount ($)", "Rate (%)", "Term (Months)", "Status", "Application Date"])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("You have not applied for any loans.")

# --- BANK STAFF PAGES ---
def bank_dashboard():
    """Main dashboard for bank staff."""
    st.title("Bank Administration Dashboard")
    
    total_customers = db.fetch_one("SELECT COUNT(*) FROM customers")[0]
    total_accounts = db.fetch_one("SELECT COUNT(*) FROM accounts")[0]
    total_deposits = db.fetch_one("SELECT SUM(balance) FROM accounts")[0]
    pending_loans = db.fetch_one("SELECT COUNT(*) FROM loans WHERE status = 'Pending'")[0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Customers", total_customers)
    col2.metric("Total Accounts", total_accounts)
    col3.metric("Total Deposits", f"${total_deposits:,.2f}")
    col4.metric("Pending Loan Apps", pending_loans)
    
    st.subheader("Recent Transactions")
    recent_tx = db.fetch_all("""
        SELECT t.transaction_date, c.first_name || ' ' || c.last_name as customer, t.transaction_type, t.amount
        FROM transactions t
        JOIN accounts a ON t.from_account_id = a.account_id OR t.to_account_id = a.account_id
        JOIN customers c ON a.customer_id = c.customer_id
        GROUP BY t.transaction_id
        ORDER BY t.transaction_date DESC LIMIT 10
    """)
    if recent_tx:
        df = pd.DataFrame(recent_tx, columns=["Date", "Customer", "Type", "Amount"])
        st.dataframe(df, use_container_width=True, hide_index=True)

def bank_loan_management():
    """Page for bank staff to approve or reject loans."""
    st.header("Loan Application Management")
    pending_loans = db.fetch_all("""
        SELECT l.loan_id, c.first_name || ' ' || c.last_name, l.loan_amount, l.term_months, l.application_date
        FROM loans l
        JOIN customers c ON l.customer_id = c.customer_id
        WHERE l.status = 'Pending'
    """)
    
    if not pending_loans:
        st.info("No pending loan applications.")
        return

    for loan in pending_loans:
        loan_id, name, amount, term, date = loan
        with st.expander(f"Application from {name} for ${amount:,.2f} ({date})"):
            st.write(f"**Applicant:** {name}")
            st.write(f"**Amount:** ${amount:,.2f}")
            st.write(f"**Term:** {term} months")
            
            col1, col2 = st.columns(2)
            if col1.button("Approve", key=f"approve_{loan_id}"):
                # In a real system, this would trigger a complex workflow. Here we simplify.
                # 1. Update loan status
                db.execute_query("UPDATE loans SET status='Approved', approval_date=CURRENT_TIMESTAMP WHERE loan_id=?", (loan_id,))
                
                # 2. Disburse funds to customer's primary account (simplification: first account found)
                customer_id = db.fetch_one("SELECT customer_id FROM loans WHERE loan_id = ?", (loan_id,))[0]
                account_to_credit = db.fetch_one("SELECT account_id FROM accounts WHERE customer_id = ? AND account_type = 'Checking' LIMIT 1", (customer_id,))
                if not account_to_credit: # if no checking, use savings
                    account_to_credit = db.fetch_one("SELECT account_id FROM accounts WHERE customer_id = ? LIMIT 1", (customer_id,))

                if account_to_credit:
                    account_id_to_credit = account_to_credit[0]
                    try:
                        db.execute_query("BEGIN TRANSACTION;")
                        db.execute_query("UPDATE accounts SET balance = balance + ? WHERE account_id = ?", (amount, account_id_to_credit))
                        db.execute_query("""
                            INSERT INTO transactions (to_account_id, transaction_type, amount, description)
                            VALUES (?, 'Loan Disbursement', ?, ?)
                        """, (account_id_to_credit, amount, f"Loan ID {loan_id} approved"))
                        #db.execute_query("COMMIT;")
                        st.success(f"Loan {loan_id} approved and funds disbursed.")
                        log_audit(st.session_state['user_info'][0], "Loan Approved", f"Loan ID: {loan_id}")
                        st.rerun()
                    except Exception as e:
                        db.execute_query("ROLLBACK;")
                        st.error(f"Failed to disburse funds. Error: {e}")
                        log_audit(st.session_state['user_info'][0], "Loan Disbursement Failed", f"Loan ID: {loan_id}, Error: {e}")
                else:
                    st.error(f"Could not find an account to disburse funds for customer.")

            if col2.button("Reject", key=f"reject_{loan_id}", type="secondary"):
                db.execute_query("UPDATE loans SET status='Rejected' WHERE loan_id=?", (loan_id,))
                st.warning(f"Loan {loan_id} has been rejected.")
                log_audit(st.session_state['user_info'][0], "Loan Rejected", f"Loan ID: {loan_id}")
                st.rerun()

def bank_financial_reports():
    """Generates and displays key financial reports for the bank."""
    st.header("Financial Reports")
    
    report_type = st.selectbox("Select Report", ["Balance Sheet", "Income Statement", "Cash Flow Statement"])

    if report_type == "Balance Sheet":
        st.subheader("Balance Sheet")
        st.markdown("As of today")
        
        # Assets
        total_cash_in_vault = db.fetch_one("SELECT SUM(balance) FROM accounts")[0]
        outstanding_loans = db.fetch_one("SELECT SUM(loan_amount) FROM loans WHERE status = 'Approved'")[0] or 0
        total_assets = total_cash_in_vault + outstanding_loans

        # Liabilities & Equity
        customer_deposits = total_cash_in_vault # In this model, all cash is customer deposits
        # Bank Equity is a simplification here
        bank_equity = total_assets - customer_deposits

        assets_data = {'Category': ['Cash (Customer Deposits)', 'Loans Receivable'], 'Amount': [total_cash_in_vault, outstanding_loans]}
        liabilities_data = {'Category': ["Customer Deposits (Liability)", "Bank Equity"], 'Amount': [customer_deposits, bank_equity]}

        df_assets = pd.DataFrame(assets_data)
        df_liabilities = pd.DataFrame(liabilities_data)
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Assets**")
            st.dataframe(df_assets, hide_index=True)
            st.metric("Total Assets", f"${total_assets:,.2f}")
        with col2:
            st.write("**Liabilities & Equity**")
            st.dataframe(df_liabilities, hide_index=True)
            st.metric("Total Liabilities & Equity", f"${(customer_deposits + bank_equity):,.2f}")

    elif report_type == "Income Statement":
        st.subheader("Income Statement")
        st.markdown("For the last 30 days")
        
        # Revenue: Interest earned from loans
        # Simplification: Calculate potential interest for one month on all approved loans
        interest_income = db.fetch_one("""
            SELECT SUM(loan_amount * (interest_rate / 100 / 12)) 
            FROM loans 
            WHERE status = 'Approved' AND approval_date >= date('now', '-30 days')
        """)[0] or 0

        # Expenses: Interest paid on deposits (simplified to 0 for this model)
        interest_expense = 0.0

        net_income = interest_income - interest_expense
        
        st.metric("Total Interest Revenue", f"${interest_income:,.2f}")
        st.metric("Total Interest Expense", f"${interest_expense:,.2f}")
        st.metric("Net Income", f"${net_income:,.2f}", delta=f"{net_income:,.2f}")

    elif report_type == "Cash Flow Statement":
        st.subheader("Cash Flow Statement")
        st.markdown("For the last 30 days")

        deposits = db.fetch_one("SELECT SUM(amount) FROM transactions WHERE transaction_type = 'Deposit' AND transaction_date >= date('now', '-30 days')")[0] or 0
        withdrawals = db.fetch_one("SELECT SUM(amount) FROM transactions WHERE transaction_type = 'Withdrawal' AND transaction_date >= date('now', '-30 days')")[0] or 0
        loan_disbursements = db.fetch_one("SELECT SUM(amount) FROM transactions WHERE transaction_type = 'Loan Disbursement' AND transaction_date >= date('now', '-30 days')")[0] or 0
        
        cash_from_operations = deposits - withdrawals
        cash_from_investing = -loan_disbursements # Outflow
        
        net_cash_flow = cash_from_operations + cash_from_investing

        data = {
            'Category': ['Deposits', 'Withdrawals', 'Loan Disbursements'],
            'Cash Flow': [deposits, -withdrawals, -loan_disbursements]
        }
        df = pd.DataFrame(data)
        st.bar_chart(df.set_index('Category'))
        st.metric("Net Cash Flow (Last 30 Days)", f"${net_cash_flow:,.2f}")
        
def bank_audit_log():
    """Displays the system's audit log."""
    st.header("System Audit Log")
    logs = db.fetch_all("SELECT timestamp, user_id, action, details FROM audit_log ORDER BY timestamp DESC LIMIT 1000")
    if logs:
        df = pd.DataFrame(logs, columns=["Timestamp", "User ID", "Action", "Details"])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No audit logs found.")


# --- MAIN APP LOGIC ---
def main():
    """The main function that runs the Streamlit app."""
    load_css()
    setup_database()

    # Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
        st.session_state['user_type'] = None
        st.session_state['user_info'] = None

    # Check if this is the first run and populate data
    if 'data_generated' not in st.session_state:
        with st.spinner('Setting up the bank for the first time...'):
            generate_synthetic_data()
            st.session_state['data_generated'] = True
            time.sleep(1) # Give a moment for the user to see the message

    # --- ROUTING ---
    if not st.session_state['logged_in']:
        login_page()
    else:
        # --- SIDEBAR NAVIGATION ---
        with st.sidebar:
            user_info = st.session_state['user_info']
            if st.session_state['user_type'] == 'customer':
                st.subheader(f"Welcome {user_info[1]}")
                st.write(f"ID: {user_info[0]}")
                page = st.radio("Navigation",
                                ["Dashboard", "Transactions", "History", "Loans"])
            elif st.session_state['user_type'] == 'staff':
                st.subheader(f"Welcome {user_info[1]}")
                st.write(f"Role: {user_info[3]}")
                page = st.radio("Navigation",
                                ["Dashboard", "Loan Management", "Financial Reports", "Audit Log"])

            if st.button("Logout", type="secondary"):
                log_audit(user_info[0], f"{st.session_state['user_type'].capitalize()} Logout")
                st.session_state['logged_in'] = False
                st.session_state['user_type'] = None
                st.session_state['user_info'] = None
                st.rerun()

        # --- PAGE DISPLAY ---
        if st.session_state['user_type'] == 'customer':
            if page == "Dashboard":
                customer_dashboard()
            elif page == "Transactions":
                customer_transactions()
            elif page == "History":
                customer_history()
            elif page == "Loans":
                customer_loans()
        
        elif st.session_state['user_type'] == 'staff':
            if page == "Dashboard":
                bank_dashboard()
            elif page == "Loan Management":
                bank_loan_management()
            elif page == "Financial Reports":
                bank_financial_reports()
            elif page == "Audit Log":
                bank_audit_log()

if __name__ == "__main__":
    main()
