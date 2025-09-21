import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import time
from faker import Faker
from datetime import datetime, timedelta
import base64

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Bank of Dhanbad",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- STYLING & ASSETS ---
def get_image_as_base64(file):
    """Reads a local image file and returns it as a base64 encoded string."""
    try:
        with open(file, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return None

def load_login_css():
    """Injects custom CSS exclusively for the login page."""
    img_base64 = get_image_as_base64("background.png")
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700;900&display=swap');
        
        body {{
            font-family: 'Poppins', sans-serif;
        }}

        /* --- LOGIN PAGE STYLES (REFINED V4 - LOGIN ONLY) --- */
        .stApp {{
            background-color: #111827; /* Dark Gray/Blue Fallback */
            background-image: url("data:image/png;base64,{img_base64}");
            background-size: cover;
        }}

        @keyframes typing {{
            from {{ width: 0; }}
            to {{ width: 100%; }}
        }}

        @keyframes blink-caret {{
            from, to {{ border-color: transparent; }}
            50% {{ border-color: #D1D5DB; }} /* Grey cursor */
        }}

        .login-title-container {{
            display: inline-block;
        }}

        .login-title {{
            font-size: 7rem;
            font-weight: 900;
            color: #D1D5DB; /* Light Grey */
            text-align: center;
            padding: 1rem;
            text-shadow: 3px 3px 10px rgba(0, 0, 0, 0.7);
            overflow: hidden;
            border-right: .15em solid #D1D5DB; /* The typewriter cursor */
            white-space: nowrap;
            margin: 0 auto;
            letter-spacing: .1em;
            animation: typing 3.5s steps(30, end), blink-caret .75s step-end infinite;
        }}
        
        .login-subtitle {{
            font-size: 1.4rem;
            font-weight: 600;
            color: #D1D5DB;
            text-align: center;
            text-shadow: 1px 1px 5px rgba(0, 0, 0, 0.8);
            margin-bottom: 2rem;
        }}
        
        div[data-testid="stRadio"] label p,
        div[data-testid="stTextInput"] label {{
            color: #D1D5DB !important;
            font-weight: 600;
            text-shadow: 1px 1px 5px rgba(0,0,0,0.8);
        }}

        .radio-container-with-border {{
            border-bottom: 3px solid #000000; /* Black line */
            padding-bottom: 1rem;
            margin-bottom: 2rem;
        }}
        
        .stButton>button {{
            border-radius: 8px;
            padding: 10px 24px;
            font-weight: 600;
            border: none;
            color: white;
            background: linear-gradient(90deg, #0D21A1, #2563EB);
            transition: all 0.3s ease-in-out;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }}

        .stButton>button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
        }}

        .stRadio [role="radiogroup"] {{
            justify-content: center;
        }}

    </style>
    """, unsafe_allow_html=True)

def load_dashboard_css():
    """Injects simpler CSS for the main application dashboard."""
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700;900&display=swap');
        
        body { font-family: 'Poppins', sans-serif; }
        
        .stApp { background: #F0F4F8; } /* Revert to standard dashboard background */

        .main .block-container {
            padding-top: 2rem; padding-bottom: 2rem; padding-left: 5rem; padding-right: 5rem;
        }

        .st-emotion-cache-16txtl3 {
            background-color: #FFFFFF; border-right: 1px solid #E0E0E0; box-shadow: 2px 0px 5px rgba(0,0,0,0.05);
        }
        
        [data-testid="stSidebarNav"]::before {
            content: "Bank of Dhanbad"; margin-left: 20px; margin-top: 20px; font-size: 24px; font-weight: 700; color: #0D21A1;
        }

        .stButton>button {
            border-radius: 8px; padding: 10px 24px; font-weight: 600; border: none; color: white;
            background: linear-gradient(90deg, #0D21A1, #2563EB); transition: all 0.3s ease-in-out;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }
        .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3); }
        .stButton[kind="secondary"]>button { background: linear-gradient(90deg, #6b7280, #4b5563); }
    </style>
    """, unsafe_allow_html=True)

# --- DATABASE SETUP ---
DB_NAME = "banking_v2.db"

class Database:
    def __init__(self, db_name):
        self.db_name = db_name
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()

    def execute_query(self, query, params=()):
        try:
            self.cursor.execute(query, params)
            self.conn.commit()
            return self.cursor
        except sqlite3.Error as e:
            st.error(f"Database error: {e}")
            return None

    def fetch_one(self, query, params=()):
        cursor = self.execute_query(query, params)
        return cursor.fetchone() if cursor else None

    def fetch_all(self, query, params=()):
        cursor = self.execute_query(query, params)
        return cursor.fetchall() if cursor else []

    def close(self):
        self.conn.close()

db = Database(DB_NAME)

def setup_database():
    # Customer Table: Added 'status' for approval workflow
    db.execute_query("""
    CREATE TABLE IF NOT EXISTS customers (
        customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Pending', -- Pending, Active, Rejected
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Accounts, Transactions, Loans, Staff, and Audit Log tables remain the same
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
    );""")
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
    );""")
    db.execute_query("""
    CREATE TABLE IF NOT EXISTS loans (
        loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        loan_amount REAL NOT NULL,
        interest_rate REAL NOT NULL,
        term_months INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'Pending',
        application_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        approval_date TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    );""")
    db.execute_query("""
    CREATE TABLE IF NOT EXISTS bank_staff (
        staff_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL
    );""")
    db.execute_query("""
    CREATE TABLE IF NOT EXISTS audit_log (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        action TEXT NOT NULL,
        details TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );""")

# --- SYNTHETIC DATA GENERATION ---
def generate_synthetic_data(num_customers=20):
    if db.fetch_one("SELECT COUNT(*) FROM customers")[0] > 0:
        return
    fake = Faker()
    hashed_password = hash_password("adminpass")
    db.execute_query("INSERT OR IGNORE INTO bank_staff (username, password_hash, role) VALUES (?, ?, ?)",
                     ('admin', hashed_password, 'Manager'))

    for i in range(num_customers):
        first_name, last_name = fake.first_name(), fake.last_name()
        email = f"{first_name.lower()}.{last_name.lower()}{i}@email.com"
        password = f"custpass{i}"
        
        # Pre-approve some customers for demo purposes
        status = 'Active' if i % 2 == 0 else 'Pending'
        
        customer_id = db.execute_query(
            "INSERT INTO customers (first_name, last_name, email, password_hash, status) VALUES (?, ?, ?, ?, ?)",
            (first_name, last_name, email, hash_password(password), status)
        ).lastrowid
        
        if status == 'Active':
            db.execute_query(
                "INSERT INTO accounts (customer_id, account_number, account_type, balance) VALUES (?, ?, ?, ?)",
                (customer_id, f"SAV{str(customer_id).zfill(8)}", 'Savings', fake.random_int(min=500, max=50000))
            )
            db.execute_query(
                "INSERT INTO accounts (customer_id, account_number, account_type, balance) VALUES (?, ?, ?, ?)",
                (customer_id, f"CHK{str(customer_id).zfill(8)}", 'Checking', fake.random_int(min=100, max=10000))
            )
    st.toast("Synthetic data generated!", icon="🎉")

# --- SECURITY & HELPERS ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_hash, provided_password):
    return stored_hash == hash_password(provided_password)

def log_audit(user_id, action, details=""):
    db.execute_query("INSERT INTO audit_log (user_id, action, details) VALUES (?, ?, ?)",
                     (str(user_id), action, details))

# --- UI COMPONENTS & PAGES ---

def login_page():
    """Renders the main login and signup page with an improved, modern UI."""
    # Wrap title in a container to center the animation properly
    st.markdown('<div style="text-align: center;"><div class="login-title-container"><h1 class="login-title">Welcome to Bank of Dhanbad</h1></div></div>', unsafe_allow_html=True)
    st.markdown('<p class="login-subtitle">Your trusted financial partner.</p>', unsafe_allow_html=True)

    if 'form_to_show' not in st.session_state:
        st.session_state.form_to_show = 'Login'

    _, center_col, _ = st.columns([1,2,1]) # Wider center column for forms
    with center_col:
        # Wrap the radio button in a div to apply the blue border
        st.markdown('<div class="radio-container-with-border">', unsafe_allow_html=True)
        selected_option = st.radio(
            "Select an option", 
            ["Login", "Create an Account"], 
            horizontal=True, 
            label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)

        st.session_state.form_to_show = selected_option
        
        if st.session_state.form_to_show == "Login":
            login_form()
        else:
            signup_form()

def login_form():
    """Displays the login form for both customers and staff."""
    login_type = st.radio("I am a:", ("Customer", "Bank Staff"), horizontal=True)

    if login_type == "Customer":
        email = st.text_input("Email", key="customer_email")
        password = st.text_input("Password", type="password", key="customer_password")
        if st.button("Login as Customer", use_container_width=True):
            customer = db.fetch_one("SELECT * FROM customers WHERE email = ?", (email,))
            if customer:
                if customer[5] != 'Active':
                    st.warning("Your account is not active. Please wait for admin approval or contact the bank.")
                    log_audit(email, "Login Failed: Account not active")
                elif verify_password(customer[4], password):
                    st.session_state['logged_in'] = True
                    st.session_state['user_type'] = 'customer'
                    st.session_state['user_info'] = customer
                    log_audit(customer[0], "Customer Login Success")
                    st.rerun()
                else:
                    st.error("Invalid email or password.")
                    log_audit(email, "Customer Login Failed: Invalid credentials")
            else:
                st.error("Invalid email or password.")

    else: # Bank Staff
        username = st.text_input("Username", key="staff_username")
        password = st.text_input("Password", type="password", key="staff_password")
        if st.button("Login as Staff", use_container_width=True):
            staff = db.fetch_one("SELECT * FROM bank_staff WHERE username = ?", (username,))
            if staff and verify_password(staff[2], password):
                st.session_state['logged_in'] = True
                st.session_state['user_type'] = 'staff'
                st.session_state['user_info'] = staff
                log_audit(staff[0], "Staff Login Success")
                st.rerun()
            else:
                st.error("Invalid username or password.")
                log_audit(username, "Staff Login Failed")

def signup_form():
    """Displays the form for new customers to create an account request."""
    st.subheader("Open Your Account Today!")
    with st.form("signup_form"):
        first_name = st.text_input("First Name")
        last_name = st.text_input("Last Name")
        email = st.text_input("Email Address")
        password = st.text_input("Create Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")

        submitted = st.form_submit_button("Submit Application", use_container_width=True)
        if submitted:
            if not all([first_name, last_name, email, password]):
                st.error("Please fill all the fields.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            elif db.fetch_one("SELECT customer_id FROM customers WHERE email = ?", (email,)):
                 st.error("An account with this email already exists.")
            else:
                hashed_password = hash_password(password)
                db.execute_query(
                    "INSERT INTO customers (first_name, last_name, email, password_hash, status) VALUES (?, ?, ?, ?, 'Pending')",
                    (first_name, last_name, email, hashed_password)
                )
                st.success("Application submitted! Your account is pending approval from a bank administrator.")
                st.info("You will not be able to log in until your account is approved.")
                log_audit(email, "New Account Application")
                time.sleep(2)
                st.session_state.form_to_show = 'Login'
                st.rerun()

# --- Customer-facing Pages (functions are the same, just called from main app logic) ---
def customer_dashboard():
    customer_id, first_name, _, _, _, status, _ = st.session_state['user_info']
    st.title(f"Welcome, {first_name}!")
    st.markdown("Your financial overview at a glance.")
    accounts = db.fetch_all("SELECT account_id, account_number, account_type, balance FROM accounts WHERE customer_id = ?", (customer_id,))
    if not accounts:
        st.warning("You have no accounts with us yet.")
        return
    total_balance = sum(acc[3] for acc in accounts)
    col1, col2 = st.columns(2)
    col1.metric(label="Total Balance", value=f"${total_balance:,.2f}")
    col2.metric(label="Number of Accounts", value=len(accounts))
    st.subheader("Your Accounts")
    for acc in accounts:
        with st.container(border=True):
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"**{acc[2]} Account**")
            c2.markdown(f"*{acc[1]}*")
            c3.markdown(f"**Balance: ${acc[3]:,.2f}**")

def customer_transactions():
    customer_id = st.session_state['user_info'][0]
    accounts = db.fetch_all("SELECT account_id, account_number, account_type, balance FROM accounts WHERE customer_id = ?", (customer_id,))
    if not accounts: st.warning("You need an account to perform transactions."); return
    account_options = {f"{acc[2]} ({acc[1]}) - Bal: ${acc[3]:,.2f}": acc[0] for acc in accounts}
    st.header("Perform a Transaction")
    tab1, tab2, tab3 = st.tabs(["💸 Transfer", "📥 Deposit", "📤 Withdraw"])
    with tab1: # Transfer
        st.subheader("Transfer Funds")
        from_account_choice = st.selectbox("From Account", options=account_options.keys(), key="transfer_from")
        from_account_id = account_options[from_account_choice]
        to_account_number = st.text_input("Recipient Account Number")
        amount = st.number_input("Amount", min_value=0.01, step=0.01, format="%.2f", key="transfer_amount")
        description = st.text_area("Description (Optional)", key="transfer_desc")
        if st.button("Execute Transfer"):
            try:
                to_account = db.fetch_one("SELECT account_id FROM accounts WHERE account_number = ?", (to_account_number,))
                if not to_account: st.error("Recipient account number does not exist."); return
                to_account_id = to_account[0]
                if from_account_id == to_account_id: st.error("Cannot transfer to the same account."); return
                sender_balance = db.fetch_one("SELECT balance FROM accounts WHERE account_id = ?", (from_account_id,))[0]
                if sender_balance < amount: st.error("Insufficient funds for this transfer."); return
                db.execute_query("BEGIN TRANSACTION;")
                db.execute_query("UPDATE accounts SET balance = balance - ? WHERE account_id = ?", (amount, from_account_id))
                db.execute_query("UPDATE accounts SET balance = balance + ? WHERE account_id = ?", (amount, to_account_id))
                db.execute_query("INSERT INTO transactions (from_account_id, to_account_id, transaction_type, amount, description) VALUES (?, ?, 'Transfer', ?, ?)", (from_account_id, to_account_id, amount, f"To {to_account_number}: {description}"))
                #db.execute_query("COMMIT;")
                st.success(f"Successfully transferred ${amount:,.2f} to account {to_account_number}.")
                log_audit(customer_id, "Transfer Success", f"Amount: {amount}, From: {from_account_id}, To: {to_account_id}")
            except Exception as e:
                db.execute_query("ROLLBACK;")
                st.error(f"An error occurred. Transaction rolled back. Details: {e}")
    with tab2: # Deposit
        st.subheader("Deposit Funds")
        deposit_account_choice = st.selectbox("To Account", options=account_options.keys(), key="deposit_to")
        deposit_account_id = account_options[deposit_account_choice]
        deposit_amount = st.number_input("Amount", min_value=0.01, step=0.01, format="%.2f", key="deposit_amount")
        if st.button("Make Deposit"):
            try:
                db.execute_query("BEGIN TRANSACTION;")
                db.execute_query("UPDATE accounts SET balance = balance + ? WHERE account_id = ?", (deposit_amount, deposit_account_id))
                db.execute_query("INSERT INTO transactions (to_account_id, transaction_type, amount, description) VALUES (?, 'Deposit', ?, 'Cash/Check Deposit')", (deposit_account_id, deposit_amount))
                #db.execute_query("COMMIT;")
                st.success(f"Successfully deposited ${deposit_amount:,.2f}.")
                log_audit(customer_id, "Deposit Success", f"Amount: {deposit_amount}, To: {deposit_account_id}")
            except Exception as e:
                db.execute_query("ROLLBACK;"); st.error(f"Deposit failed. Error: {e}")
    with tab3: # Withdraw
        st.subheader("Withdraw Funds")
        withdraw_account_choice = st.selectbox("From Account", options=account_options.keys(), key="withdraw_from")
        withdraw_account_id = account_options[withdraw_account_choice]
        withdraw_amount = st.number_input("Amount", min_value=0.01, step=0.01, format="%.2f", key="withdraw_amount")
        if st.button("Make Withdrawal"):
            current_balance = db.fetch_one("SELECT balance FROM accounts WHERE account_id = ?", (withdraw_account_id,))[0]
            if current_balance < withdraw_amount: st.error("Insufficient funds.")
            else:
                try:
                    db.execute_query("BEGIN TRANSACTION;")
                    db.execute_query("UPDATE accounts SET balance = balance - ? WHERE account_id = ?", (withdraw_amount, withdraw_account_id))
                    db.execute_query("INSERT INTO transactions (from_account_id, transaction_type, amount, description) VALUES (?, 'Withdrawal', ?, 'Cash Withdrawal')", (withdraw_account_id, withdraw_amount))
                    #db.execute_query("COMMIT;")
                    st.success(f"Successfully withdrew ${withdraw_amount:,.2f}.")
                    log_audit(customer_id, "Withdrawal Success")
                except Exception as e:
                    db.execute_query("ROLLBACK;"); st.error(f"Withdrawal failed. Error: {e}")


def customer_history():
    st.header("Transaction History")
    customer_id = st.session_state['user_info'][0]
    query = """
        SELECT t.transaction_date, t.description, t.transaction_type,
            CASE WHEN t.from_account_id IN (SELECT account_id FROM accounts WHERE customer_id = ?) THEN -t.amount ELSE t.amount END as amount,
            a.account_type || ' (' || a.account_number || ')' as account
        FROM transactions t
        JOIN accounts a ON a.account_id = CASE WHEN t.from_account_id IN (SELECT account_id FROM accounts WHERE customer_id = ?) THEN t.from_account_id ELSE t.to_account_id END
        WHERE t.from_account_id IN (SELECT account_id FROM accounts WHERE customer_id = ?) OR t.to_account_id IN (SELECT account_id FROM accounts WHERE customer_id = ?)
        ORDER BY t.transaction_date DESC;
    """
    transactions = db.fetch_all(query, (customer_id, customer_id, customer_id, customer_id))
    if transactions:
        df = pd.DataFrame(transactions, columns=["Date", "Description", "Type", "Amount ($)", "Account"])
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d %H:%M:%S')
        st.dataframe(df.style.apply(lambda x: ['color: red' if x.name == 'Amount ($)' and v < 0 else 'color: green' for v in x], axis=0), use_container_width=True, hide_index=True)
    else: st.info("No transaction history found.")

def customer_loans():
    st.header("Loans"); customer_id = st.session_state['user_info'][0]
    tab1, tab2 = st.tabs(["Apply for a New Loan", "View My Loans"])
    with tab1:
        st.subheader("Loan Application Form")
        with st.form("loan_application"):
            loan_amount = st.number_input("Loan Amount ($)", min_value=1000.0, step=100.0, format="%.2f")
            term_months = st.selectbox("Loan Term (Months)", [12, 24, 36, 48, 60])
            if st.form_submit_button("Submit Application"):
                db.execute_query("INSERT INTO loans (customer_id, loan_amount, interest_rate, term_months, status) VALUES (?, ?, ?, ?, 'Pending')", (customer_id, loan_amount, 5.0, term_months))
                st.success("Your loan application has been submitted successfully!")
    with tab2:
        st.subheader("Your Loan Status")
        loans = db.fetch_all("SELECT loan_amount, interest_rate, term_months, status, application_date FROM loans WHERE customer_id = ?", (customer_id,))
        if loans: st.dataframe(pd.DataFrame(loans, columns=["Amount ($)", "Rate (%)", "Term (Months)", "Status", "Application Date"]), use_container_width=True, hide_index=True)
        else: st.info("You have not applied for any loans.")

# --- Bank Staff Pages ---
def bank_dashboard():
    st.title("Bank Administration Dashboard")
    total_customers = db.fetch_one("SELECT COUNT(*) FROM customers WHERE status = 'Active'")[0]
    pending_accounts = db.fetch_one("SELECT COUNT(*) FROM customers WHERE status = 'Pending'")[0]
    total_deposits = db.fetch_one("SELECT SUM(balance) FROM accounts")[0]
    pending_loans = db.fetch_one("SELECT COUNT(*) FROM loans WHERE status = 'Pending'")[0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Active Customers", total_customers)
    col2.metric("Pending Account Apps", pending_accounts, delta=pending_accounts, delta_color="inverse")
    col3.metric("Total Deposits", f"${total_deposits:,.2f}")
    col4.metric("Pending Loan Apps", pending_loans, delta=pending_loans, delta_color="inverse")
    
def bank_account_requests():
    """Page for admins to approve or reject new account applications."""
    st.header("New Account Applications")
    pending_customers = db.fetch_all("SELECT customer_id, first_name, last_name, email, created_at FROM customers WHERE status = 'Pending'")

    if not pending_customers:
        st.info("No pending account applications.")
        return

    for cust in pending_customers:
        cust_id, fname, lname, email, date = cust
        with st.expander(f"Application from {fname} {lname} ({email}) - Submitted: {date.split()[0]}"):
            col1, col2, _ = st.columns([1,1,4])
            if col1.button("Approve", key=f"approve_cust_{cust_id}"):
                try:
                    # 1. Update customer status
                    db.execute_query("UPDATE customers SET status = 'Active' WHERE customer_id = ?", (cust_id,))
                    
                    # 2. Create default accounts for the new customer
                    db.execute_query("INSERT INTO accounts (customer_id, account_number, account_type, balance) VALUES (?, ?, 'Savings', 10.0)", (cust_id, f"SAV{str(cust_id).zfill(8)}"))
                    db.execute_query("INSERT INTO accounts (customer_id, account_number, account_type, balance) VALUES (?, ?, 'Checking', 0.0)", (cust_id, f"CHK{str(cust_id).zfill(8)}"))
                    
                    st.success(f"Account for {fname} {lname} has been approved and created.")
                    log_audit(st.session_state['user_info'][0], "Account Approved", f"Customer ID: {cust_id}")
                    st.rerun()
                except Exception as e:
                    st.error(f"An error occurred: {e}")

            if col2.button("Reject", key=f"reject_cust_{cust_id}", type="secondary"):
                db.execute_query("UPDATE customers SET status = 'Rejected' WHERE customer_id = ?", (cust_id,))
                st.warning(f"Account for {fname} {lname} has been rejected.")
                log_audit(st.session_state['user_info'][0], "Account Rejected", f"Customer ID: {cust_id}")
                st.rerun()

def bank_loan_management():
    st.header("Loan Application Management")
    pending_loans = db.fetch_all("SELECT l.loan_id, c.first_name || ' ' || c.last_name, l.loan_amount, l.term_months, l.application_date FROM loans l JOIN customers c ON l.customer_id = c.customer_id WHERE l.status = 'Pending'")
    if not pending_loans: st.info("No pending loan applications."); return
    for loan in pending_loans:
        loan_id, name, amount, term, date = loan
        with st.expander(f"Application from {name} for ${amount:,.2f}"):
            st.write(f"**Applicant:** {name}"); st.write(f"**Amount:** ${amount:,.2f}"); st.write(f"**Term:** {term} months")
            col1, col2 = st.columns(2)
            if col1.button("Approve", key=f"approve_{loan_id}"):
                db.execute_query("UPDATE loans SET status='Approved', approval_date=CURRENT_TIMESTAMP WHERE loan_id=?", (loan_id,))
                customer_id = db.fetch_one("SELECT customer_id FROM loans WHERE loan_id = ?", (loan_id,))[0]
                account_to_credit = db.fetch_one("SELECT account_id FROM accounts WHERE customer_id = ? LIMIT 1", (customer_id,))
                if account_to_credit:
                    try:
                        db.execute_query("BEGIN TRANSACTION;")
                        db.execute_query("UPDATE accounts SET balance = balance + ? WHERE account_id = ?", (amount, account_to_credit[0]))
                        db.execute_query("INSERT INTO transactions (to_account_id, transaction_type, amount, description) VALUES (?, 'Loan Disbursement', ?, ?)", (account_to_credit[0], amount, f"Loan ID {loan_id}"))
                        db.execute_query("COMMIT;")
                        st.success(f"Loan {loan_id} approved and funds disbursed."); st.rerun()
                    except Exception as e:
                        db.execute_query("ROLLBACK;"); st.error(f"Failed to disburse funds: {e}")
            if col2.button("Reject", key=f"reject_{loan_id}", type="secondary"):
                db.execute_query("UPDATE loans SET status='Rejected' WHERE loan_id=?", (loan_id,))
                st.warning(f"Loan {loan_id} rejected."); st.rerun()

def bank_financial_reports():
    st.header("Financial Reports")
    report_type = st.selectbox("Select Report", ["Balance Sheet", "Income Statement", "Cash Flow Statement"])
    if report_type == "Balance Sheet":
        total_cash = db.fetch_one("SELECT SUM(balance) FROM accounts")[0] or 0
        outstanding_loans = db.fetch_one("SELECT SUM(loan_amount) FROM loans WHERE status = 'Approved'")[0] or 0
        assets = {'Category': ['Cash (Customer Deposits)', 'Loans Receivable'], 'Amount': [total_cash, outstanding_loans]}
        liabilities = {'Category': ["Customer Deposits (Liability)", "Bank Equity"], 'Amount': [total_cash, outstanding_loans]} # Simplified equity
        col1, col2 = st.columns(2)
        with col1: st.write("**Assets**"); st.dataframe(pd.DataFrame(assets), hide_index=True); st.metric("Total Assets", f"${(total_cash + outstanding_loans):,.2f}")
        with col2: st.write("**Liabilities & Equity**"); st.dataframe(pd.DataFrame(liabilities), hide_index=True); st.metric("Total Liab. & Equity", f"${(total_cash + outstanding_loans):,.2f}")
    
def bank_audit_log():
    st.header("System Audit Log")
    logs = db.fetch_all("SELECT timestamp, user_id, action, details FROM audit_log ORDER BY timestamp DESC LIMIT 1000")
    if logs: st.dataframe(pd.DataFrame(logs, columns=["Timestamp", "User ID", "Action", "Details"]), use_container_width=True, hide_index=True)
    else: st.info("No audit logs found.")

# --- MAIN APP LOGIC ---
def main():
    setup_database()

    if 'logged_in' not in st.session_state:
        st.session_state.update({'logged_in': False, 'user_type': None, 'user_info': None})

    if 'data_generated' not in st.session_state:
        with st.spinner('Setting up the bank for the first time...'):
            generate_synthetic_data()
            st.session_state['data_generated'] = True
            time.sleep(1)

    if not st.session_state['logged_in']:
        load_login_css()
        login_page()
    else:
        load_dashboard_css()
        with st.sidebar:
            st.markdown("## BS.") # Bank Logo
            user_info = st.session_state['user_info']
            page_options = []
            if st.session_state['user_type'] == 'customer':
                st.subheader(f"Welcome {user_info[1]}")
                page_options = ["Dashboard", "Transactions", "History", "Loans"]
            elif st.session_state['user_type'] == 'staff':
                st.subheader(f"Welcome {user_info[1]}")
                st.write(f"Role: {user_info[3]}")
                page_options = ["Dashboard", "Account Requests", "Loan Management", "Financial Reports", "Audit Log"]

            page = st.radio("Navigation", page_options, label_visibility="collapsed")

            if st.button("Logout", use_container_width=True, type="secondary"):
                log_audit(user_info[0], f"{st.session_state['user_type'].capitalize()} Logout")
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

        # Page Display Logic
        if st.session_state['user_type'] == 'customer':
            if page == "Dashboard": customer_dashboard()
            elif page == "Transactions": customer_transactions()
            elif page == "History": customer_history()
            elif page == "Loans": customer_loans()
        
        elif st.session_state['user_type'] == 'staff':
            if page == "Dashboard": bank_dashboard()
            elif page == "Account Requests": bank_account_requests()
            elif page == "Loan Management": bank_loan_management()
            elif page == "Financial Reports": bank_financial_reports()
            elif page == "Audit Log": bank_audit_log()

if __name__ == "__main__":
    main()

















