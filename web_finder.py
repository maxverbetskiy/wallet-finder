import time
import requests
from flask import Flask, request, jsonify, render_template_string
import webbrowser
from threading import Timer
import traceback
import os # <-- НОВАЯ СТРОКА

app = Flask(__name__)

# --- USER CREDENTIALS (Your IDs and Key) ---
API_KEY = os.environ.get("DUNE_API_KEY") # <-- ИЗМЕНЕНО!

# 1. ID for Ethereum/BSC (Optimized Byte Search)
ID_EVM = 6317721 

# 2. ID for Bitcoin (Text Search)
ID_BTC = 6317873

# --- HTML TEMPLATE (Full English Interface) ---
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wallet Finder v2.1</title>
    <style>
        :root { --bg-color: #0f172a; --card-bg: #1e293b; --text-main: #f8fafc; --accent: #3b82f6; --accent-hover: #2563eb; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: var(--bg-color); color: var(--text-main); display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .container { background-color: var(--card-bg); padding: 2rem; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); width: 100%; max-width: 600px; text-align: center; }
        h1 { margin-bottom: 0.5rem; font-size: 1.8rem; }
        p.subtitle { color: #94a3b8; margin-bottom: 2rem; font-size: 0.9rem; }
        
        /* Network Switch Styles */
        .network-switch { 
            display: flex; background: #0f172a; border-radius: 8px; padding: 4px; 
            margin-bottom: 25px; border: 1px solid #334155; 
        }
        .radio-option { 
            flex: 1; text-align: center; padding: 12px; cursor: pointer; 
            border-radius: 6px; transition: 0.3s; color: #64748b; font-weight: bold; 
            user-select: none;
        }
        .radio-option:hover { color: #94a3b8; }
        .radio-option.active { 
            background-color: var(--accent); color: white; 
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4); 
        }
        
        .input-group { display: flex; gap: 10px; margin-bottom: 20px; }
        input { width: 100%; padding: 14px; background: #0f172a; border: 1px solid #334155; border-radius: 8px; color: white; font-family: monospace; font-size: 1.1rem; }
        input:focus { outline: 2px solid var(--accent); border-color: transparent; }
        
        button { width: 100%; padding: 16px; background-color: var(--accent); color: white; border: none; border-radius: 8px; font-size: 1rem; font-weight: bold; cursor: pointer; transition: 0.2s; }
        button:hover { background-color: var(--accent-hover); transform: translateY(-1px); }
        button:disabled { background-color: #475569; cursor: not-allowed; transform: none; }
        
        .results { margin-top: 20px; text-align: left; max-height: 350px; overflow-y: auto; padding-right: 5px; }
        .results::-webkit-scrollbar { width: 6px; }
        .results::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
        
        .result-item { background: #334155; padding: 12px; margin-bottom: 8px; border-radius: 8px; font-family: monospace; font-size: 0.9rem; display: flex; justify-content: space-between; align-items: center; }
        .network-tag { font-size: 0.7rem; padding: 3px 8px; border-radius: 4px; background: #0f172a; color: #cbd5e1; text-transform: uppercase; }
        
        .loading { display: none; color: var(--accent); margin-top: 15px; font-weight: 500; }
        .error { color: #ef4444; margin-top: 15px; display: none; background: rgba(239, 68, 68, 0.1); padding: 10px; border-radius: 8px; }
    </style>
</head>
<body>
<div class="container">
    <h1>🕵️ Wallet Finder v2.1</h1>
    <p class="subtitle">Search addresses by partial match</p>

    <div class="network-switch">
        <div class="radio-option active" id="btn-evm" onclick="setNetwork('evm')">Ethereum / BSC</div>
        <div class="radio-option" id="btn-btc" onclick="setNetwork('btc')">Bitcoin (BTC)</div>
    </div>

    <div class="input-group">
        <input type="text" id="prefix" placeholder="Prefix (e.g., 0xbdaa...)" value="0xbdaa">
        <input type="text" id="suffix" placeholder="Suffix (e.g., ...8dbd)" value="8dbd">
    </div>

    <button onclick="searchWallet()" id="searchBtn">Find Wallet</button>
    
    <div class="loading" id="loading">📡 Scanning blockchain...</div>
    <div class="error" id="error"></div>
    <div class="results" id="resultsArea"></div>
</div>

<script>
    let currentNetwork = 'evm';

    function setNetwork(net) {
        currentNetwork = net;
        // Update button visual styles
        document.getElementById('btn-evm').className = net === 'evm' ? 'radio-option active' : 'radio-option';
        document.getElementById('btn-btc').className = net === 'btc' ? 'radio-option active' : 'radio-option';
        
        const prefixInput = document.getElementById('prefix');
        const suffixInput = document.getElementById('suffix');

        // Update placeholders
        if(net === 'btc') {
            prefixInput.placeholder = 'Prefix (e.g., 1A1z...)';
            prefixInput.value = ''; 
            suffixInput.placeholder = 'Suffix (e.g., ...P3q)';
            suffixInput.value = '';
        } else {
            prefixInput.placeholder = 'Prefix (e.g., 0xbdaa...)';
            prefixInput.value = '0xbdaa';
            suffixInput.placeholder = 'Suffix (e.g., ...8dbd)';
            suffixInput.value = '8dbd';
        }
    }

    async function searchWallet() {
        const prefix = document.getElementById('prefix').value.trim();
        const suffix = document.getElementById('suffix').value.trim();
        const btn = document.getElementById('searchBtn');
        const loading = document.getElementById('loading');
        const resultsArea = document.getElementById('resultsArea');
        const errorDiv = document.getElementById('error');

        if (!prefix && !suffix) {
            errorDiv.style.display = 'block';
            errorDiv.innerText = 'Please enter at least one character!';
            return;
        }

        resultsArea.innerHTML = '';
        errorDiv.style.display = 'none';
        btn.disabled = true;
        
        loading.innerText = currentNetwork === 'evm' ? '📡 Scanning EVM (up to 3 min)...' : '📡 Scanning Bitcoin (may take time)...';
        loading.style.display = 'block';

        try {
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prefix, suffix, network: currentNetwork })
            });
            const data = await response.json();
            
            if (!response.ok || data.error) throw new Error(data.error || 'Unknown server error');

            if (!data.results || data.results.length === 0) {
                resultsArea.innerHTML = '<div style="text-align:center; color: #94a3b8; padding: 20px;">No results found 😔</div>';
            } else {
                data.results.forEach(row => {
                    const div = document.createElement('div');
                    div.className = 'result-item';
                    
                    let shortAddress = row.address;
                    if (row.address.length > 42) shortAddress = row.address.substring(0, 20) + '...' + row.address.substring(row.address.length - 15);

                    div.innerHTML = `
                        <span title="${row.address}" onclick="navigator.clipboard.writeText('${row.address}')" style="cursor:copy">${shortAddress}</span>
                        <span class="network-tag">${row.network}</span>
                    `;
                    resultsArea.appendChild(div);
                });
            }
        } catch (err) {
            errorDiv.style.display = 'block';
            errorDiv.innerText = 'ERROR: ' + err.message;
        } finally {
            btn.disabled = false;
            loading.style.display = 'none';
        }
    }
</script>
</body>
</html>
"""

# --- SERVER LOGIC ---
def execute_query(prefix, suffix, network_mode):
    headers = {"X-Dune-Api-Key": API_KEY}
    
    # Select Query ID based on mode
    if network_mode == 'btc':
        target_query_id = ID_BTC
    else:
        target_query_id = ID_EVM

    url_execute = f"https://api.dune.com/api/v1/query/{target_query_id}/execute"
    
    params = {
        "query_parameters": {
            "prefix": prefix,
            "suffix": suffix
        }
    }
    
    print(f"1. Launching search ({network_mode.upper()})... Query ID: {target_query_id}")
    resp = requests.post(url_execute, headers=headers, json=params)
    
    # --- NEW API RATE LIMIT CHECK ---
    if resp.status_code == 429:
        raise Exception("API Rate Limit Exceeded. Please wait 5 minutes and try again.")
    # -------------------------------
    
    if resp.status_code != 200:
        try: error_msg = resp.json().get('error', resp.text)
        except: error_msg = resp.text
        raise Exception(f"Dune API Error ({resp.status_code}): {error_msg}")
        
    execution_id = resp.json()['execution_id']
    print(f"2. Task accepted! Execution ID: {execution_id}")
    
    url_status = f"https://api.dune.com/api/v1/execution/{execution_id}/results"
    
    # Wait loop (60 attempts * 3 sec = 3 minutes total)
    for i in range(60): 
        time.sleep(3) 
        try:
            status_resp = requests.get(url_status, headers=headers)
            if status_resp.status_code != 200: continue
            
            data = status_resp.json()
            state = data.get('state')
            print(f"   Check {i+1}/60: Status {state}")
            
            if state == 'QUERY_STATE_COMPLETED':
                return data['result']['rows']
            elif state == 'QUERY_STATE_FAILED':
                # Generic failure on SQL execution side
                raise Exception("SQL Error on Dune side (Check query syntax)")
        except Exception as e:
            # Handle API/Network errors in the polling loop
            if "SQL Error" in str(e): raise e
            if "429" in str(e): raise Exception("API Rate Limit Exceeded. Please wait 5 minutes and try again.")
            print(f"Network error during polling: {e}")
            continue
            
    raise Exception("Timeout: Server did not respond within 3 minutes.")

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

@app.route('/api/search', methods=['POST'])
def search():
    data = request.json
    try:
        rows = execute_query(
            data.get('prefix', '').strip(), 
            data.get('suffix', '').strip(),
            data.get('network', 'evm')
        )
        return jsonify({'results': rows})
    except Exception as e:
        print("!!! CRITICAL PYTHON ERROR !!!")
        traceback.print_exc()
        # Return error message to the client
        return jsonify({'error': str(e)}), 500

def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000/')

if __name__ == '__main__':
    # Это важно для хостинга: Flask должен слушать HOST/PORT, который дает Render
    port = int(os.environ.get("PORT", 5000))
    # Timer(1, open_browser).start() # Убираем автозапуск браузера
    app.run(host='0.0.0.0', port=port) # <-- ИЗМЕНЕНО