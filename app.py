import search
from flask import Flask, render_template, jsonify, request
import time

app = Flask(__name__)
@app.route('/')
def home():
    return render_template('index.html')


@app.route('/askQuestion', methods=['POST'])
def askQuestion():
    startTime = time.perf_counter()

    data = request.get_json()
    query = data['question']
    responseObj, numHits = search.searchDocuments(query)
    endTime = time.perf_counter()
    
    elapsedTime = endTime - startTime

    return jsonify({'time': (elapsedTime*1000),'message': responseObj, 'numHits': numHits})

if __name__ == '__main__':
    app.run(debug=True)