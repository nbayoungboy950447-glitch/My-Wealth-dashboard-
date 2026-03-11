import random
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'vertex_vault_private_access_2026'

# --- The Central Ledger (Stored in Memory) ---
bank_data = {
    "user": {
        "email": "lydia.brooke@oal.com",
        "name": "LYDIA BROOKE",
        "pwd": "lydia777",
        "balance": 24967500.00,
        "status": "Private Client Tier"
    },
    "history": [
     {"id": "VX-8812-99", "date": "Mar 10, 2026", "time": "02:45 PM", "desc": "OUTBOUND WIRE - ARMIN DEAN HESTERBERG", "amount": -20000.00, "status": "COMPLETED", "ref": "FW-992837465"},
        {"id": "VX-9921-01", "date": "Mar 10, 2026", "time": "11:20 AM", "desc": "INTERNAL ASSET REALLOCATION", "amount": 125000.00, "status": "SETTLED", "ref": "IA-110293847"},
        {"id": "VX-4412-44", "date": "Mar 08, 2026", "time": "09:12 AM", "desc": "WIRE TRANSFER - SOTHEBY'S", "amount": -43617.84, "status": "COMPLETED", "ref": "FW-883746512"}   
        
        
    ]
}

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
    if 'user' not in session: return redirect(url_for('login'))
    return render_template('dashboard.html', user=bank_data["user"], history=bank_data["history"])

@app.route('/execute_wire', methods=['POST'])
def execute_wire():
    data = request.form
    amount = float(data.get('amount'))
    recipient = data.get('beneficiary')
    
    # Live Deduction Logic
    bank_data["user"]["balance"] -= amount
    new_tx = {
        "id": f"VX-{random.randint(1000, 9999)}",
        "date": datetime.now().strftime("%b %d, %Y"),
        "desc": f"OUTBOUND WIRE - {recipient.upper()}",
        "amount": -amount
    }
    bank_data["history"].insert(0, new_tx)
    return render_template('success.html', recipient=recipient.upper(), amount=amount)

@app.route('/chat', methods=['POST'])
def chat():
    msg = request.json.get('message', '').lower()
    if 'balance' in msg:
        res = f"Your current liquidity is ${bank_data['user']['balance']:,.2f}."
    elif 'limit' in msg:
        res = "Your elite daily transfer limit is currently set to $10,000,000.00 USD."
    else:
        res = "I am the Vertex Concierge. How can I assist with your private assets today?"
    return jsonify({"reply": res})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))
# ... (existing execute_wire code) ...

@app.route('/loans')
def loans():
    return render_template('loans.html', user=bank_data["user"])

@app.route('/investments')
def investments():
    return render_template('investments.html', user=bank_data["user"])

@app.route('/savings')
def savings():
    return render_template('savings.html', user=bank_data["user"])
@app.route('/withdraw_investment', methods=['POST'])
def withdraw_investment():
    # 1. Check if she is logged in
    if 'user' not in session: return redirect(url_for('login'))
    
    # 2. Define the amount
    amount = 100000.00
    
    # 3. Do the Math
    if bank_data["user"]["investment_balance"] >= amount:
        bank_data["user"]["investment_balance"] -= amount
        bank_data["user"]["balance"] += amount
        
        # 4. Write it in the history book
        new_tx = {
            "id": "VX-LIQ-992",
            "date": "Mar 10, 2026",
            "time": "05:15 PM",
            "desc": "INVESTMENT LIQUIDATION - PORTFOLIO X-1",
            "amount": amount,
            "status": "SETTLED",
            "ref": "LQ-9928311"
        }
        bank_data["history"].insert(0, new_tx) # Puts it at the top of the list
        
    return redirect(url_for('dashboard'))
# KEEP THIS AT THE VERY BOTTOM
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
