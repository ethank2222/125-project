import search
from flask import Flask, render_template, jsonify, request, session, redirect, url_for
import time
import os
import json
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
            'previous_injuries': data.get('previous_injuries'),
            'avail_days': data.get('avail_days'),
            'avail_mins': data.get('avail_mins')
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
        'previous_injuries': data.get('previous_injuries'),
        'avail_days': data.get('avail_days'),
        'avail_mins': data.get('avail_mins')
    }
    
    database.update_preferences(session['user_id'], prefs)
    return jsonify({'success': True})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/get_exercises')
def get_exercises():
    if 'user_id' not in session:
        return jsonify({'error': 'Need to login'}), 401
    
    exercise_ids = request.args.get('ids')
    if not exercise_ids:
        return jsonify({'error': 'Need exercise IDs'}), 400
    
    try:
        import genPlan
        ids = [int(id.strip()) for id in exercise_ids.split(',') if id.strip()]
        if not ids:
            return jsonify({'exercises': {}})
        
        placeholders = ', '.join(['?'] * len(ids))
        query = f"SELECT id, name FROM exercises WHERE id IN ({placeholders})"
        genPlan.cursor.execute(query, ids)
        results = genPlan.cursor.fetchall()
        
        exercises = {row[0]: row[1] for row in results}
        return jsonify({'exercises': exercises})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_plan')
def get_plan():
    if 'user_id' not in session:
        return jsonify({'error': 'Need to login'}), 401
    
    try:
        import genPlan
        conn = genPlan.conn
        cursor = genPlan.cursor
        cursor.execute("SELECT day, exercises FROM userSplits WHERE userid = ?;", (str(session['user_id']),))
        results = cursor.fetchall()
        
        # Get user's available days to determine the split
        user = database.get_user(session['user_id'])
        if not user or not user.get('avail_days'):
            return jsonify({'error': 'Please set your available days in preferences'}), 400
        
        splitList = genPlan.daysplitter(user['avail_days'])
        dayNames = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        
        plan = {}
        storedPlans = {row[0]: json.loads(row[1]) for row in results}
        
        for i, day in enumerate(splitList):
            dayName = dayNames[i]
            if day == 'rest':
                plan[dayName] = []
            else:
                plan[dayName] = storedPlans.get(day, [])
        
        return jsonify({'success': True, 'plan': plan})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)