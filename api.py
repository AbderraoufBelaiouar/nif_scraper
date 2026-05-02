#!/usr/bin/env python3
"""
NIF Checker API - REST API for checking Algerian Tax Identification Number
Usage: python api.py (local) or gunicorn -w 4 -b 0.0.0.0:$PORT api:app (production)
"""

import os
from flask import Flask, request, jsonify
from nif_checker import check_nif, SCRAPINGANT_API_KEY

app = Flask(__name__)


@app.route('/debug', methods=['GET'])
def debug():
    return jsonify({
        'api_key_set': bool(SCRAPINGANT_API_KEY),
        'api_key_prefix': SCRAPINGANT_API_KEY[:8] + '...' if SCRAPINGANT_API_KEY else '',
    })


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})


@app.route('/api/check-nif', methods=['GET', 'POST'])
def check_nif_api():
    if request.method == 'GET':
        nif = request.args.get('nif')
    else:
        data = request.get_json() or {}
        nif = data.get('nif')

    if not nif:
        return jsonify({
            'status': 'error',
            'message': 'NIF parameter is required'
        }), 400

    result = check_nif(nif)
    return jsonify(result)


@app.route('/api/check-nif/<nif>', methods=['GET'])
def check_nif_path(nif):
    result = check_nif(nif)
    return jsonify(result)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)