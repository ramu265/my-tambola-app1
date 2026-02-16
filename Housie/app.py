import os
import random
import uuid
import urllib.parse
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = "housie_super_secret_key"

# Game Database
game_state = {"called_numbers": [], "users": {}}

def generate_proper_tickets(count):
    final_tickets = []
    for _ in range(count):
        ticket = [[0 for _ in range(9)] for _ in range(3)]
        for col in range(9):
            start = col * 10 if col > 0 else 1
            end = col * 10 + 9 if col < 8 else 90
            col_numbers = random.sample(range(start, end + 1), 3)
            col_numbers.sort()
            for row in range(3):
                ticket[row][col] = col_numbers[row]
        for row in range(3):
            cols_to_remove = random.sample(range(9), 4)
            for c in cols_to_remove:
                ticket[row][c] = 0
        final_tickets.append(ticket)
    return final_tickets

@app.route('/')
def home():
    return render_template('admin_login.html')

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('username') == "admin" and request.form.get('password') == "admin123":
        session['admin'] = True
        return redirect(url_for('dashboard'))
    return "Invalid Credentials"

@app.route('/dashboard')
def dashboard():
    if not session.get('admin'): return redirect(url_for('home'))
    return render_template('admin_dashboard.html')

@app.route('/generate_link', methods=['POST'])
def generate_link():
    phone = request.form.get('phone')
    count_raw = request.form.get('ticket_count', 1)
    try:
        count = int(count_raw) if count_raw else 1
    except:
        count = 1
    token = str(uuid.uuid4())[:8]
    game_state["users"][token] = {"tickets": generate_proper_tickets(count)}
    link = f"{request.host_url}ticket/{token}"
    msg = f"Your Tambola Tickets are ready! Open here: {link}"
    whatsapp_url = f"https://api.whatsapp.com/send?phone={phone}&text={urllib.parse.quote(msg)}"
    return jsonify({"whatsapp_url": whatsapp_url})

@app.route('/call_number', methods=['POST'])
def call_number():
    available = [n for n in range(1, 91) if n not in game_state["called_numbers"]]
    if not available: return jsonify({"status": "over"})
    num = random.choice(available)
    game_state["called_numbers"].append(num)
    return jsonify({"number": num, "history": game_state["called_numbers"]})

@app.route('/restart_game', methods=['POST'])
def restart_game():
    game_state["called_numbers"] = []
    return jsonify({"status": "restarted"})

@app.route('/get_updates')
def get_updates():
    return jsonify({"called": game_state["called_numbers"]})

@app.route('/ticket/<token>')
def show_ticket(token):
    user_data = game_state["users"].get(token)
    if not user_data: 
        return "<h1>Ticket Not Found or Expired!</h1><p>Please ask Admin for a new link.</p>"
    return render_template('user_ticket.html', tickets=user_data['tickets'])

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
