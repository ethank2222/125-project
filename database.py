import sqlite3
import hashlib

DB_PATH = 'users.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            intent TEXT,
            weight REAL,
            height REAL,
            age INTEGER,
            gender TEXT,
            previous_injuries TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password, name, preferences):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        pwd_hash = hash_password(password)
        cursor.execute('INSERT INTO users (username, password_hash, name) VALUES (?, ?, ?)', 
                      (username, pwd_hash, name))
        uid = cursor.lastrowid
        
        cursor.execute('''INSERT INTO preferences (user_id, intent, weight, height, age, gender, previous_injuries)
                         VALUES (?, ?, ?, ?, ?, ?, ?)''',
                      (uid, preferences.get('intent'), preferences.get('weight'),
                       preferences.get('height'), preferences.get('age'),
                       preferences.get('gender'), preferences.get('previous_injuries')))
        
        conn.commit()
        return uid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def authenticate_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    password_hash = hash_password(password)
    cursor.execute('SELECT id FROM users WHERE username = ? AND password_hash = ?', 
                  (username, password_hash))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def get_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''SELECT u.id, u.username, u.name, p.intent, p.weight, p.height, p.age, p.gender, p.previous_injuries
                      FROM users u LEFT JOIN preferences p ON u.id = p.user_id WHERE u.id = ?''', 
                  (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {'id': result[0], 'username': result[1], 'name': result[2], 'intent': result[3],
                'weight': result[4], 'height': result[5], 'age': result[6], 'gender': result[7],
                'previous_injuries': result[8]}
    return None

def update_preferences(user_id, preferences):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM preferences WHERE user_id = ?', (user_id,))
    found = cursor.fetchone()
    
    if found:
        cursor.execute('''UPDATE preferences SET intent = ?, weight = ?, height = ?, age = ?, gender = ?, previous_injuries = ?
                         WHERE user_id = ?''',
                      (preferences.get('intent'), preferences.get('weight'), preferences.get('height'),
                       preferences.get('age'), preferences.get('gender'), preferences.get('previous_injuries'), user_id))
    else:
        cursor.execute('''INSERT INTO preferences (user_id, intent, weight, height, age, gender, previous_injuries)
                         VALUES (?, ?, ?, ?, ?, ?, ?)''',
                      (user_id, preferences.get('intent'), preferences.get('weight'),
                       preferences.get('height'), preferences.get('age'),
                       preferences.get('gender'), preferences.get('previous_injuries')))
    
    conn.commit()
    conn.close()

def username_exists(username):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

init_db()
