"""
Minimal Hello World application for infrastructure testing
"""
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return {'message': 'Hello from AWS Bedrock RAG API!', 'status': 'infrastructure-test'}

@app.route('/health')
def health():
    return {'status': 'healthy'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
