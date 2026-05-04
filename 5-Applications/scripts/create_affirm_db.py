import sqlite3
import json
import os

# Data from the browser subagent (Current + Past)
data = {
  "current_loans": [
    { "merchant": "Amazon", "amount_due": "$47.04", "due_date": "May 28" },
    { "merchant": "Amazon", "amount_due": "$23.10", "due_date": "Jun 2" },
    { "merchant": "Mint Mobile", "amount_due": "$36.16", "due_date": "Jun 3" },
    { "merchant": "Wolfram Alpha", "amount_due": "$10.55", "due_date": "Jun 10" },
    { "merchant": "Walmart", "amount_due": "$13.41", "due_date": "Jun 11" },
    { "merchant": "vitalrecords", "amount_due": "$11.05", "due_date": "Jun 13" },
    { "merchant": "Mint Mobile", "amount_due": "$10.05", "due_date": "Jun 13" },
    { "merchant": "msi", "amount_due": "$31.34", "due_date": "Jun 14" },
    { "merchant": "eBay", "amount_due": "$11.30", "due_date": "Jun 16" },
    { "merchant": "Agoda.com", "amount_due": "$24.25", "due_date": "Jun 16" },
    { "merchant": "Newegg", "amount_due": "$12.85", "due_date": "Jun 18" },
    { "merchant": "Kimi.com", "amount_due": "$37.67", "due_date": "Jun 21" },
    { "merchant": "Amazon", "amount_due": "$21.25", "due_date": "Jun 21" },
    { "merchant": "Affirm Virtual Card", "amount_due": "$33.58", "due_date": "Jun 22" },
    { "merchant": "Amazon", "amount_due": "$14.24", "due_date": "Jun 23" },
    { "merchant": "Walmart", "amount_due": "$12.06", "due_date": "Jun 26" },
    { "merchant": "Northwest Registered Agents", "amount_due": "$16.58", "due_date": "Jun 27" }
  ],
  "past_loans": [
    { "merchant": "Newegg", "amount": "$101.63", "date": "Apr 28, 2026", "status": "Paid" },
    { "merchant": "Amazon", "amount": "$95.14", "date": "Apr 28, 2026", "status": "Paid" },
    { "merchant": "Amazon", "amount": "$796.97", "date": "Apr 2, 2026", "status": "Paid" },
    { "merchant": "Affirm", "amount": "$45.00", "date": "Apr 2, 2026", "status": "Paid" },
    { "merchant": "Uber", "amount": "$100.00", "date": "Apr 2, 2026", "status": "Paid" },
    { "merchant": "Groupon", "amount": "$140.00", "date": "Feb 26, 2026", "status": "Paid" },
    { "merchant": "Amazon", "amount": "$172.29", "date": "Feb 26, 2026", "status": "Paid" },
    { "merchant": "DoorDash", "amount": "$60.00", "date": "Feb 12, 2026", "status": "Paid" },
    { "merchant": "Priceline", "amount": "$92.00", "date": "Dec 29, 2025", "status": "Paid" },
    { "merchant": "amazons", "amount": "$86.00", "date": "Dec 27, 2025", "status": "Paid" },
    { "merchant": "Expedia", "amount": "$93.95", "date": "Dec 27, 2025", "status": "Paid" },
    { "merchant": "Newegg", "amount": "$440.69", "date": "Sep 22, 2025", "status": "Paid" },
    { "merchant": "It's A 10", "amount": "$65.00", "date": "Aug 9, 2025", "status": "Paid" },
    { "merchant": "Best Buy", "amount": "$670.00", "date": "Jun 30, 2025", "status": "Paid" },
    { "merchant": "amazons", "amount": "$144.00", "date": "May 29, 2025", "status": "Paid" },
    { "merchant": "Amazon", "amount": "$135.76", "date": "Mar 15, 2025", "status": "Paid" },
    { "merchant": "Amazon", "amount": "$171.08", "date": "Feb 26, 2025", "status": "Paid" },
    { "merchant": "Amazon", "amount": "$96.30", "date": "Jan 31, 2025", "status": "Paid" },
    { "merchant": "Newegg", "amount": "$1,891.90", "date": "Jan 9, 2025", "status": "Paid" },
    { "merchant": "Zenni", "amount": "$78.99", "date": "Sep 5, 2024", "status": "Paid" },
    { "merchant": "Ames Lock", "amount": "$250.00", "date": "Jul 18, 2024", "status": "Paid" },
    { "merchant": "Amazon", "amount": "$94.15", "date": "Feb 23, 2024", "status": "Paid" },
    { "merchant": "Newegg", "amount": "$266.42", "date": "Dec 14, 2023", "status": "Paid" },
    { "merchant": "Younits", "amount": "$889.99", "date": "Nov 10, 2015", "status": "Refunded" }
  ],
  "selected_loan_history": [
      { "date": "Jun 27, 2024", "amount": "$1,047.22", "description": "Processed" },
      { "date": "Jul 27, 2024", "amount": "-$47.04", "payment_method": "Visa •••• 3166" },
      { "date": "Aug 28, 2024", "amount": "-$47.04", "payment_method": "Visa •••• 3166" },
      { "date": "Sep 28, 2024", "amount": "-$47.04", "payment_method": "Visa •••• 3166" },
      { "date": "Oct 28, 2024", "amount": "-$47.04", "payment_method": "Visa •••• 3166" },
      { "date": "Nov 27, 2024", "amount": "-$47.04", "payment_method": "Bank Account •••• 9161" },
      { "date": "Dec 25, 2024", "amount": "-$47.04", "payment_method": "Visa •••• 3166" },
      { "date": "Jan 27, 2025", "amount": "-$47.04", "payment_method": "Visa •••• 3166" },
      { "date": "Feb 26, 2025", "amount": "-$47.04", "payment_method": "Visa •••• 3166" },
      { "date": "Mar 15, 2025", "amount": "-$47.04", "payment_method": "Visa •••• 3166" },
      { "date": "Apr 25, 2025", "amount": "-$47.04", "payment_method": "Visa •••• 9388" },
      { "date": "May 24, 2025", "amount": "-$47.04", "payment_method": "Visa •••• 7078" },
      { "date": "Jun 30, 2025", "amount": "-$47.04", "payment_method": "Visa •••• 7078" },
      { "date": "Jul 28, 2025", "amount": "-$47.04", "payment_method": "Visa •••• 7078" },
      { "date": "Sep 25, 2025", "amount": "-$47.04", "payment_method": "Visa •••• 7078" },
      { "date": "Sep 25, 2025", "amount": "-$47.04", "payment_method": "Visa •••• 7078" },
      { "date": "Oct 25, 2025", "amount": "-$47.04", "payment_method": "Visa •••• 7078" },
      { "date": "Nov 24, 2025", "amount": "-$47.04", "payment_method": "Visa •••• 7078" },
      { "date": "Dec 27, 2025", "amount": "-$47.04", "payment_method": "Visa •••• 7078" },
      { "date": "Jan 6, 2026", "amount": "-$47.04", "payment_method": "Visa •••• 7078" },
      { "date": "Feb 4, 2026", "amount": "-$47.04", "payment_method": "Visa •••• 7078" },
      { "date": "Mar 29, 2026", "amount": "-$47.04", "payment_method": "Visa •••• 7078" },
      { "date": "Apr 28, 2026", "amount": "-$47.04", "payment_method": "Visa •••• 7078" }
  ]
}

# Use absolute paths
base_dir = "/home/allaun/Research Stack"
os.makedirs(os.path.join(base_dir, "data"), exist_ok=True)

db_path = os.path.join(base_dir, "shared-data/data/affirm_accounts.db")
json_path = os.path.join(base_dir, "shared-data/data/affirm_accounts.json")

# Connect to SQLite
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Drop tables to start fresh with new schema
cursor.execute('DROP TABLE IF EXISTS transactions')
cursor.execute('DROP TABLE IF EXISTS loans')

# Create tables with status
cursor.execute('''
CREATE TABLE IF NOT EXISTS loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    merchant TEXT,
    amount TEXT,
    date_info TEXT,
    status TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    loan_id INTEGER,
    date TEXT,
    amount TEXT,
    payment_method TEXT,
    description TEXT,
    FOREIGN KEY (loan_id) REFERENCES loans (id)
)
''')

# Insert current loans
for loan in data["current_loans"]:
    cursor.execute('INSERT INTO loans (merchant, amount, date_info, status) VALUES (?, ?, ?, ?)',
                   (loan["merchant"], loan["amount_due"], loan["due_date"], "Active"))

# Insert past loans
for loan in data["past_loans"]:
    cursor.execute('INSERT INTO loans (merchant, amount, date_info, status) VALUES (?, ?, ?, ?)',
                   (loan["merchant"], loan["amount"], loan["date"], loan["status"]))

# Find the ID of the Amazon loan with $47.04 amount (Active)
cursor.execute('SELECT id FROM loans WHERE merchant = "Amazon" AND amount = "$47.04" AND status = "Active" LIMIT 1')
amazon_loan_id = cursor.fetchone()[0]

# Insert transactions for the active Amazon loan
for tx in data["selected_loan_history"]:
    cursor.execute('''
    INSERT INTO transactions (loan_id, date, amount, payment_method, description)
    VALUES (?, ?, ?, ?, ?)
    ''', (amazon_loan_id, tx["date"], tx["amount"], tx.get("payment_method", ""), tx.get("description", "")))

conn.commit()
conn.close()

# Save updated JSON
with open(json_path, "w") as f:
    json.dump(data, f, indent=2)

print(f"Updated database at {db_path} with closed accounts.")
print(f"Updated JSON data at {json_path}")
