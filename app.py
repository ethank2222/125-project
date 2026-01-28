import search
from flask import Flask, render_template, jsonify, request, session, redirect, url_for
import time
import os
import database

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        return render_template('login.html', error='Need username and password')
    
    user_id = database.authenticate_user(username, password)
    
    if user_id:
        session['user_id'] = user_id
        session['username'] = username
        return redirect(url_for('dashboard'))
    else:
        return render_template('login.html', error='Wrong username or password')

@app.route('/signup')
def signup_page():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('signup.html')

@app.route('/create_account', methods=['POST'])
def create_account():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data'}), 400
        
        username = data.get('username')
        password = data.get('password')
        name = data.get('name')
        
        if not username or not password or not name:
            return jsonify({'success': False, 'error': 'Need username, password, and name'}), 400
        
        if database.username_exists(username):
            return jsonify({'success': False, 'error': 'Username taken'}), 400
        
        prefs = {
            'intent': data.get('intent'),
            'weight': data.get('weight'),
            'height': data.get('height'),
            'age': data.get('age'),
            'gender': data.get('gender'),
            'previous_injuries': data.get('previous_injuries')
        }
        
        user_id = database.create_user(username, password, name, prefs)
        
        if user_id:
            session['user_id'] = user_id
            session['username'] = username
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Could not create account'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    
    user = database.get_user(session['user_id'])
    return render_template('dashboard.html', user=user)

@app.route('/preferences')
def preferences():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    
    user = database.get_user(session['user_id'])
    return render_template('preferences.html', user=user)

@app.route('/update_preferences', methods=['POST'])
def update_preferences():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    data = request.get_json()
    prefs = {
        'intent': data.get('intent'),
        'weight': data.get('weight'),
        'height': data.get('height'),
        'age': data.get('age'),
        'gender': data.get('gender'),
        'previous_injuries': data.get('previous_injuries')
    }
    
    database.update_preferences(session['user_id'], prefs)
    return jsonify({'success': True})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/askQuestion', methods=['POST'])
def askQuestion():
    if 'user_id' not in session:
        return jsonify({'error': 'Need to login'}), 401
    
    try:
        start = time.perf_counter()

        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({'error': 'Need a question'}), 400
        
        q = data['question']
        results, num = search.searchDocuments(q)
        end = time.perf_counter()
        
        time_taken = end - start

        return jsonify({'time': (time_taken*1000),'message': results, 'numHits': num})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)