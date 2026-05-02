#!/usr/bin/env python3
"""
NIF Checker - Check Algerian Tax Identification Number
Usage: python nif_checker.py <NIF_NUMBER>
"""

import os
import sys
import argparse
import warnings
import requests
from bs4 import BeautifulSoup

warnings.filterwarnings('ignore', message='.*Unverified HTTPS request.*')

BASE_URL = "https://nifenligne.mf.gov.dz"
AUTH_URLS = [
    "https://nifenligne.mf.gov.dz/nif.asp",
]

SCRAPINGANT_API_KEY = os.environ.get('SCRAPINGANT_API_KEY', '')

def get_proxy():
    if not SCRAPINGANT_API_KEY:
        return None
    return {
        'http': f'http://scrapingant:{SCRAPINGANT_API_KEY}@proxy.scrapingant.com:8080',
        'https': f'http://scrapingant:{SCRAPINGANT_API_KEY}@proxy.scrapingant.com:8080',
    }


def check_nif(nif_number: str) -> dict:
    """
    Check a NIF number on the DGI website.
    Returns a dict with the result.
    """
    session = requests.Session()

    proxies = get_proxy()

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    
    response = None
    tried_urls = []
    
    for url in AUTH_URLS:
        tried_urls.append(url)
        try:
            resp = session.get(url, headers=headers, timeout=30, verify=False, proxies=proxies)
            if resp.status_code == 200:
                response = resp
                break
        except Exception as e:
            continue
    
    if not response or response.status_code != 200:
        return {
            'status': 'error',
            'message': f'Could not reach any NIF verification page. Tried: {", ".join(tried_urls)}',
            'raw_response': response.text[:2000] if response else None
        }
    
    soup = BeautifulSoup(response.text, 'html.parser')
    form = soup.find('form')
    
    if not form:
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href', '')
            if any(x in href.lower() for x in ['auth', 'verif', 'nif']):
                try:
                    form_url = href if href.startswith('http') else BASE_URL.rstrip('/') + '/' + href
                    if form_url not in tried_urls:
                        tried_urls.append(form_url)
                        resp = session.get(form_url, headers=headers, timeout=30, verify=False, proxies=proxies)
                        soup = BeautifulSoup(resp.text, 'html.parser')
                        form = soup.find('form')
                        if form:
                            response = resp
                            break
                except:
                    continue
    
    if not form:
        return {
            'status': 'error',
            'message': 'No form found on page to submit NIF',
            'raw_response': response.text[:3000]
        }
    
    form_action = form.get('action', '') or BASE_URL + '/nif.asp'
    form_method = form.get('method', 'POST').upper()
    
    inputs = {}
    for input_tag in soup.find_all('input'):
        name = input_tag.get('name')
        value = input_tag.get('value', '')
        input_type = input_tag.get('type', 'text')
        if name and input_type != 'submit':
            inputs[name] = value
    
    if 'nif' in inputs:
        inputs['nif'] = nif_number
    else:
        inputs['nif'] = nif_number
    
    submit_url = form_action if form_action.startswith('http') else BASE_URL + '/nif.asp'
    
    if form_method == 'GET':
        response = session.get(submit_url, params=inputs, headers=headers, timeout=30, verify=False, proxies=proxies)
    else:
        response = session.post(submit_url, data=inputs, headers=headers, timeout=30, verify=False, proxies=proxies)
    
    return parse_response(response.text, nif_number)


def parse_response(html: str, nif: str) -> dict:
    """
    Parse the HTML response to extract NIF information.
    """
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text()
    
    if 'svp' in text.lower() or 'renseigner' in text.lower() or 'saisir un nif' in text.lower():
        return {
            'status': 'invalid',
            'nif': nif,
            'message': 'NIF appears to be invalid or not provided'
        }
    
    if 'trouv' not in text.lower() and ('inexistant' in text.lower() or 'incorrect' in text.lower() or 'invalide' in text.lower()):
        return {
            'status': 'invalid',
            'nif': nif,
            'message': 'NIF not found in database'
        }
    
    tables = soup.find_all('table')
    results = []
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                cell_texts = [c.get_text(strip=True) for c in cells]
                if cell_texts[0] and cell_texts[0] != nif and cell_texts[0] != 'NIF':
                    results.append({
                        'nif': cell_texts[0],
                        'name': cell_texts[1] if len(cell_texts) > 1 else ''
                    })
    
    if results:
        return {
            'status': 'valid',
            'nif': nif,
            'name': results[0]['name'],
            'results': results,
            'message': f'NIF is valid - {len(results)} result(s) found'
        }
    
    if 'trouv' in text.lower():
        return {
            'status': 'valid',
            'nif': nif,
            'name': extract_name(soup),
            'message': 'NIF is valid'
        }
    
    return {
        'status': 'unknown',
        'nif': nif,
        'message': 'Could not determine NIF status',
        'raw_preview': text[:500]
    }


def extract_name(soup: BeautifulSoup) -> str:
    """
    Extract the name/company associated with the NIF.
    """
    name_patterns = ['raison sociale', 'nom', 'denomination', 'nom_prenom', 'nom et prénom']
    
    for pattern in name_patterns:
        elements = soup.find_all(string=lambda t: pattern.lower() in t.lower())
        for elem in elements:
            parent = elem.find_parent()
            if parent:
                next_elem = parent.find_next_sibling()
                if next_elem:
                    text = next_elem.get_text(strip=True)
                    if text and len(text) > 1:
                        return text
    
    headers = soup.find_all(['h1', 'h2', 'h3', 'h4'])
    for header in headers:
        text = header.get_text(strip=True)
        if text and len(text) > 2 and not any(x in text.lower() for x in ['erreur', 'attention']):
            return text
    
    return 'Name not extracted'


def main():
    parser = argparse.ArgumentParser(description='Check Algerian NIF (Numéro d\'Identification Fiscale)')
    parser.add_argument('nif', nargs='?', help='NIF number to check')
    parser.add_argument('--raw', action='store_true', help='Show raw response')
    parser.add_argument('--debug', action='store_true', help='Show debug information')
    
    args = parser.parse_args()
    
    if not args.nif:
        parser.print_help()
        print("\nExample: python nif_checker.py 123456789012345")
        sys.exit(1)
    
    result = check_nif(args.nif)
    
    if args.debug:
        print(f"Status: {result['status']}")
        print(f"Message: {result['message']}")
        if 'raw_response' in result and result['raw_response']:
            print(f"\nRaw Response:\n{result['raw_response'][:1000]}")
        if 'raw_preview' in result and result['raw_preview']:
            print(f"\nRaw Preview:\n{result['raw_preview']}")
        if 'details' in result:
            print(f"Details: {result['details']}")
        sys.exit(0)
    
    if result['status'] == 'valid':
        print(f"✓ NIF {result['nif']} is VALID")
        if result.get('name'):
            print(f"  Name: {result['name']}")
        if result.get('results'):
            for r in result['results']:
                print(f"  {r['nif']} - {r['name']}")
    elif result['status'] == 'invalid':
        print(f"✗ NIF {result['nif']} is INVALID")
        print(f"  {result['message']}")
    elif result['status'] == 'found':
        print(f"? NIF {result['nif']} - Information found")
        if result.get('details'):
            print(f"  Details: {result['details']}")
    elif result['status'] == 'error':
        print(f"Error: {result['message']}")
        if result.get('raw_response'):
            print(f"\nRaw response:\n{result['raw_response'][:500]}")
    else:
        print(f"? NIF {result['nif']} - Status unknown")
        print(f"  {result['message']}")
    
    if args.raw and 'raw_response' in result:
        print(f"\n--- Raw Response ---")
        print(result.get('raw_response', '')[:2000])


if __name__ == '__main__':
    main()