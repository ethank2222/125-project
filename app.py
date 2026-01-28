import search
from flask import Flask, render_template, jsonify, request
import time
import os

app = Flask(__name__)
@app.route('/')
def home():
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/preferences')
def preferences():
    return render_template('preferences.html')


@app.route('/askQuestion', methods=['POST'])
def askQuestion():
    try:
        startTime = time.perf_counter()

        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({'error': 'Missing question parameter'}), 400
        
        query = data['question']
        responseObj, numHits = search.searchDocuments(query)
        endTime = time.perf_counter()
        
        elapsedTime = endTime - startTime

        return jsonify({'time': (elapsedTime*1000),'message': responseObj, 'numHits': numHits})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)