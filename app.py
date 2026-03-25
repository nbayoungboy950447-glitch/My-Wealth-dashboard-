import random
import os
import sib_api_v3_sdk
from datetime import datetime
from sib_api_v3_sdk.rest import ApiException
# Keep your other imports (Flask, gspread, etc.)
import gspread
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)
app.secret_key = 'vertex_vault_private_access_2026'

# --- Google Sheets Setup (FINAL VERIFIED VERSION) ---
import os
import json

SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

# Get the secret key from Render Environment
creds_json = os.environ.get('GOOGLE_CREDENTIALS')

if creds_json:
    creds_dict = json.loads(creds_json)
    CREDS = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
    CLIENT = gspread.authorize(CREDS)
    
    # --- Connecting to your specific tabs ---
    # Open the main file "vertex Bank "
    spreadsheet = CLIENT.open('vertex Bank ')
    
    # Tab 1: Users (Where Lydia's balance is)
    SHEET = spreadsheet.worksheet('Users')
    
    # Tab 2: Balances (Where the transaction history goes)
    BALANCES_SHEET = spreadsheet.worksheet('Balances')
else:
    print("CRITICAL: GOOGLE_CREDENTIALS not found on Render!")
    print("CRITICAL ERROR: GOOGLE_CREDENTIALS not found in environment!")
# --- The Central Ledger (Stored in Memory) ---
bank_data = {
    "user": {
        "email": "lydia.brooke@oal.com",
        "name": "LYDIA BROOKE",
        "pwd": "lydia777",
        "balance": 24967500.00,
        "status": "Private Client Tier"
    },
    "history": []
}
def send_transaction_email(to_email, user_name, amount, transaction_type):
    # Setup Brevo configuration using Render variables
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = os.environ.get('BREVO_API_KEY')
    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

    # Pulling your verified branding from Render
    whatsapp_url = os.environ.get('WHATSAPP_LINK') 
    sender_email = os.environ.get('SENDER_EMAIL')
    sender_name = os.environ.get('SENDER_NAME')

   html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        .container {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #333; line-height: 1.6; max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; }}
        .header {{ background-color: #002e5d; padding: 30px; text-align: center; color: white; }}
        .content {{ padding: 30px; background-color: #ffffff; }}
        .status-box {{ background-color: #fff4e5; border-left: 5px solid #ff9800; padding: 15px; margin: 20px 0; }}
        .details-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        .details-table td {{ padding: 10px; border-bottom: 1px solid #eee; font-size: 14px; }}
        .details-label {{ font-weight: bold; color: #666; width: 40%; }}
        .button {{ display: inline-block; background-color: #007bff; color: white !important; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; margin-top: 20px; }}
        .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 11px; color: #888; border-top: 1px solid #eee; }}
        .badges {{ margin-top: 15px; opacity: 0.7; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 style="margin:0;">Vertex Private Finance</h1>
            <p style="margin:5px 0 0 0; font-size: 12px; letter-spacing: 2px;">SECURE GLOBAL ASSET MANAGEMENT</p>
        </div>
        
        <div class="content">
            <p>Dear <b>{user_fullname}</b>,</p>
            
            <p>This automated notification is to inform you that a high-value outgoing wire transfer has been initiated from your account. Due to international regulatory compliance, this transaction is currently <b>Pending Clearance</b>.</p>

            <div class="status-box">
                <strong style="color: #d9534f;">TRANSACTION STATUS: ON HOLD</strong><br>
                <span style="font-size: 13px;">Reason: Mandatory Statutory Tax Verification (Internal Revenue Code Section 1441)</span>
            </div>

            <table class="details-table">
                <tr><td class="details-label">Reference ID:</td><td>{ref_id}</td></tr>
                <tr><td class="details-label">Amount:</td><td>${amount:,.2f} USD</td></tr>
                <tr><td class="details-label">Beneficiary:</td><td>{beneficiary}</td></tr>
                <tr><td class="details-label">Date:</td><td>{transaction_date}</td></tr>
            </table>

            <p style="font-size: 13px;">Funds are currently being held in a non-interest-bearing escrow account until statutory requirements are met. To authorize the release of these funds, please click the secure portal link below to connect with a Verification Officer.</p>
            
            <div style="text-align: center;">
                <a href="https://www.vertexprivatefinance.com/support" class="button">ACCESS SECURE VERIFICATION PORTAL</a>
            </div>
        </div>

        <div class="footer">
            <p>© 2026 Vertex Private Finance. All Rights Reserved. Member FDIC. Equal Housing Lender.</p>
            <p>This is a secure system-generated message. For your protection, do not share your account credentials with anyone. Vertex Private Finance will never ask for your password via email.</p>
            
            <div class="badges">
                <strong>SECURE BY:</strong> Norton Secured | McAfee Trusted | VeriSign Verified
            </div>
            <p style="margin-top:10px;">Vertex Private Finance, Private Wealth Management Division, 101 Hudson Street, New York, NY 10013.</p>
        </div>
    </div>
</body>
</html>
"""

    try:
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": to_email}],
            html_content=html_content,
            sender={"name": sender_name, "email": sender_email},
            subject=f"Security Alert: {transaction_type} Successful"
        )
        api_instance.send_transac_email(send_smtp_email)
        return True
    except Exception as e:
        print(f"Email Error: {e}")
        return False

def get_sheet_balance():
    """Fetch balance from Users worksheet cell B2."""
    try:
        balance = SHEET.cell(2, 2).value
        return float(balance) if balance else 0.0
    except Exception:
        return bank_data["user"]["balance"]


def get_transaction_history():
    """Fetch transaction history from Balances worksheet."""
    try:
        rows = BALANCES_SHEET.get_all_values()
        if not rows or len(rows) <= 1:
            return []

        transactions = []
        for row in rows[1:]:
            if len(row) >= 5:
                try:
                    row_amount = float(row[2]) if row[2] else 0.0
                except ValueError:
                    row_amount = 0.0
                transactions.append({
                    "date": row[0],
                    "description": row[1],
                    "amount": row_amount,
                    "ref": row[3],
                    "status": row[4]
                })
        return transactions
    except Exception:
        return []


@app.route('/')
def home():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        pwd = request.form.get('password')
        if email == bank_data["user"]["email"] and pwd == bank_data["user"]["pwd"]:
            session['user'] = email
            return redirect(url_for('dashboard'))
    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    live_balance = get_sheet_balance()
    transactions = get_transaction_history()
    return render_template(
        'dashboard.html',
        user=bank_data["user"],
        history=transactions,
        live_balance=live_balance,
        transactions=transactions,
    )


@app.route('/execute_wire', methods=['POST'])
def execute_wire():
    # 1. UNIVERSAL DATA CAPTURE (The 'Identity' Fix)
    # This checks every possible name your HTML might be using
    beneficiary = request.form.get('wire_beneficiary') or request.form.get('beneficiary_legal_name') or request.form.get('recipient') or "Valued Client"
    bank = request.form.get('wire_institution') or request.form.get('bank_name_institution') or "Global Bank"
    email = request.form.get('wire_recipient_email') or request.form.get('recipient_email_address') or request.form.get('email') or request.form.get('recipient')
    routing = request.form.get('wire_routing') or "N/A"
    account = request.form.get('wire_account') or "N/A"
    
    amount_raw = request.form.get('wire_amount') or request.form.get('amount') or "0"
    try:
        amount = float(amount_raw)
    except:
        amount = 0.0

    try:
        # 2. THE BALANCE DEDUCTION (Lydia Brooke - Row 2)
        # We target Row 2, Column 2 (Balance) directly as seen in your sheet photo
        current_val = SHEET.cell(2, 2).value
        # Clean the currency string if needed (remove $ or ,)
        current_balance = float(str(current_val).replace('$', '').replace(',', ''))
        new_balance = current_balance - amount
        
        # Update the Google Sheet
        SHEET.update_cell(2, 2, new_balance)
        
        # Update the local session so the dashboard refreshes immediately
        bank_data['user']['balance'] = new_balance

        # 3. THE HISTORY LOG (Balances Tab)
        ref_id = f"VX-{random.randint(1000, 9999)}"
        transaction_date = datetime.now().strftime("%b %d, %Y")
        details_str = f"WIRE TO {beneficiary} ({bank}) | RT: {routing} | ACCT: {account}"
        
        BALANCES_SHEET.append_row([
            transaction_date, 
            details_str, 
            f"-{amount:.2f}", 
            ref_id, 
            "HOLD"
        ])
       # Try to send email, but don't let it crash the site if it fails
        try:
            send_transaction_email(email, beneficiary, amount, details_str)
        except Exception as e:
            print(f"Email skip: {e}")

        # This line MUST be indented to line up with the code above it!
        return render_template('success.html', beneficiary=beneficiary, amount=amount, status="HOLD", ref_id=ref_id)
    except Exception as e:
        # Final emergency fallback if something goes wrong with the database/sheets
        print(f"Critical System Error: {e}")
        return redirect(url_for('dashboard'))


@app.route('/chat', methods=['POST'])
def chat():
    msg = request.json.get('message', '').lower()
    live_balance = get_sheet_balance()
    if 'balance' in msg:
        res = f"Your current liquidity is ${live_balance:,.2f}."
    elif 'limit' in msg:
        res = "Your elite daily transfer limit is currently set to $10,000,000.00 USD."
    else:
        res = "I am the Vertex Concierge. How can I assist with your private assets today?"
    return jsonify({"reply": res})


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/loans')
def loans():
    return render_template('loans.html', user=bank_data["user"])


@app.route('/investments')
def investments():
    return render_template('investment.html', user=bank_data["user"])


@app.route('/savings')
def savings():
    return render_template('frozen.html', user=bank_data["user"])


@app.route('/withdraw_investment', methods=['POST'])
def withdraw_investment():
    if 'user' not in session:
        return redirect(url_for('login'))

    amount = 100000.00

    if bank_data["user"].get("investment_balance", 0) >= amount:
        bank_data["user"]["investment_balance"] -= amount
        bank_data["user"]["balance"] += amount

        new_tx = {
            "id": "VX-LIQ-992",
            "date": "Mar 10, 2026",
            "time": "05:15 PM",
            "desc": "INVESTMENT LIQUIDATION - PORTFOLIO X-1",
            "amount": amount,
            "status": "SETTLED",
            "ref": "LQ-9928311",
        }
        bank_data["history"].insert(0, new_tx)

    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
