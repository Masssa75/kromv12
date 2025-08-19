#!/usr/bin/env python3
"""
Simple Flask server to view token discovery data
"""

from flask import Flask, render_template_string
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime

load_dotenv()

app = Flask(__name__)

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Token Discovery Viewer</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, monospace;
            background: #0a0a0a;
            color: #e0e0e0;
            margin: 0;
            padding: 20px;
        }
        h1 {
            color: #fff;
            font-size: 24px;
            margin-bottom: 10px;
        }
        .stats {
            color: #888;
            margin-bottom: 20px;
            font-size: 14px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background: #111;
        }
        th {
            background: #1a1a1a;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            border-bottom: 1px solid #333;
            position: sticky;
            top: 0;
            z-index: 10;
        }
        td {
            padding: 10px 12px;
            border-bottom: 1px solid #222;
        }
        tr:hover {
            background: #1a1a1a;
        }
        a {
            color: #4a9eff;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        .symbol {
            font-weight: 600;
            color: #fff;
        }
        .network {
            text-transform: uppercase;
            font-size: 12px;
            padding: 2px 6px;
            border-radius: 3px;
            background: #222;
            color: #888;
        }
        .network.solana { background: #14f195; color: #000; }
        .network.eth { background: #627eea; color: #fff; }
        .network.base { background: #0052ff; color: #fff; }
        .network.bsc { background: #f3ba2f; color: #000; }
        .network.arbitrum { background: #28a0f0; color: #fff; }
        .liquidity {
            text-align: right;
            font-family: 'SF Mono', Monaco, monospace;
            color: #4ade80;
        }
        .links {
            display: flex;
            gap: 10px;
        }
        .link-btn {
            padding: 4px 8px;
            background: #222;
            border-radius: 4px;
            font-size: 12px;
            transition: background 0.2s;
        }
        .link-btn:hover {
            background: #333;
        }
        .has-website {
            color: #4ade80;
        }
        .no-website {
            color: #666;
        }
        .filter-bar {
            margin-bottom: 20px;
            display: flex;
            gap: 10px;
            align-items: center;
            flex-wrap: wrap;
        }
        select, input[type="text"] {
            background: #1a1a1a;
            color: #e0e0e0;
            border: 1px solid #333;
            padding: 6px 10px;
            border-radius: 4px;
        }
        input[type="text"]:focus {
            outline: none;
            border-color: #4a9eff;
        }
        .search-container {
            display: flex;
            gap: 5px;
            align-items: center;
        }
        .search-btn {
            padding: 6px 12px;
            background: #1a3a1a;
            color: #4ade80;
            border: 1px solid #2a5a2a;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .search-btn:hover {
            background: #2a5a2a;
        }
        .clear-btn {
            padding: 6px 12px;
            background: #3a1a1a;
            color: #ff6b6b;
            border: 1px solid #5a2a2a;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .clear-btn:hover {
            background: #5a2a2a;
        }
        .age {
            color: #888;
            font-size: 12px;
        }
        .pagination {
            margin: 20px 0;
            display: flex;
            gap: 15px;
            align-items: center;
            justify-content: center;
        }
        .page-btn {
            padding: 8px 16px;
            background: #1a1a1a;
            border-radius: 4px;
            transition: background 0.2s;
        }
        .page-btn:hover {
            background: #333;
        }
        .page-info {
            color: #888;
            font-size: 14px;
        }
        .ca-container {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        .ca-text {
            font-family: 'SF Mono', Monaco, monospace;
            font-size: 12px;
            color: #888;
            cursor: pointer;
            padding: 2px 6px;
            border-radius: 3px;
            transition: all 0.2s;
        }
        .ca-text:hover {
            background: #222;
            color: #4a9eff;
        }
        .ca-text.copied {
            background: #1a3a1a;
            color: #4ade80;
        }
    </style>
    <script>
        function copyCA(address, element) {
            navigator.clipboard.writeText(address).then(function() {
                // Show full address temporarily
                const originalText = element.innerText;
                element.innerText = 'Copied!';
                element.classList.add('copied');
                
                setTimeout(() => {
                    element.innerText = originalText;
                    element.classList.remove('copied');
                }, 1500);
            }).catch(function(err) {
                console.error('Failed to copy: ', err);
            });
        }
        
        function updateFilters(updates) {
            const params = new URLSearchParams(window.location.search);
            Object.keys(updates).forEach(key => {
                params.set(key, updates[key]);
            });
            window.location.href = '/?' + params.toString();
        }
        
        function searchCA() {
            const searchValue = document.getElementById('searchInput').value.trim();
            if (searchValue) {
                const params = new URLSearchParams(window.location.search);
                params.set('search', searchValue);
                params.set('page', '1');
                window.location.href = '/?' + params.toString();
            }
        }
        
        function clearSearch() {
            const params = new URLSearchParams(window.location.search);
            params.delete('search');
            params.set('page', '1');
            window.location.href = '/?' + params.toString();
        }
        
        // Allow Enter key to trigger search
        document.addEventListener('DOMContentLoaded', function() {
            const searchInput = document.getElementById('searchInput');
            if (searchInput) {
                searchInput.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        searchCA();
                    }
                });
            }
        });
    </script>
</head>
<body>
    <h1>🔍 Token Discovery Dashboard</h1>
    
    <div class="stats">
        Total Tokens in DB: {{ total_tokens_db }} | 
        Total With Websites: {{ total_with_websites_db }} | 
        Average Liquidity: ${{ avg_liquidity }} |
        Showing: {{ showing_start }}-{{ showing_end }} of {{ filtered_total }}
        {% if search %}
        | <span style="color: #4ade80;">Searching for: "{{ search }}"</span>
        {% endif %}
    </div>
    
    <div class="filter-bar">
        <div class="search-container">
            <label>Search CA:</label>
            <input type="text" id="searchInput" placeholder="Enter contract address..." value="{{ search }}" style="width: 300px;">
            <button class="search-btn" onclick="searchCA()">Search</button>
            {% if search %}
            <button class="clear-btn" onclick="clearSearch()">Clear</button>
            {% endif %}
        </div>
        
        <label>Sort by:</label>
        <select onchange="updateFilters({sort: this.value, page: 1})">
            <option value="liquidity" {% if sort == 'liquidity' %}selected{% endif %}>Liquidity ↓</option>
            <option value="volume" {% if sort == 'volume' %}selected{% endif %}>Volume ↓</option>
            <option value="recent" {% if sort == 'recent' %}selected{% endif %}>Recent ↓</option>
            <option value="age" {% if sort == 'age' %}selected{% endif %}>Oldest ↓</option>
        </select>
        
        <label>Network:</label>
        <select onchange="updateFilters({network: this.value, page: 1})">
            <option value="all" {% if network == 'all' %}selected{% endif %}>All Networks</option>
            <option value="solana" {% if network == 'solana' %}selected{% endif %}>Solana</option>
            <option value="eth" {% if network == 'eth' %}selected{% endif %}>Ethereum</option>
            <option value="base" {% if network == 'base' %}selected{% endif %}>Base</option>
            <option value="arbitrum" {% if network == 'arbitrum' %}selected{% endif %}>Arbitrum</option>
            <option value="bsc" {% if network == 'bsc' %}selected{% endif %}>BSC</option>
            <option value="polygon" {% if network == 'polygon' %}selected{% endif %}>Polygon</option>
        </select>
        
        <label>Has Website:</label>
        <select onchange="updateFilters({has_website: this.value, page: 1})">
            <option value="all" {% if has_website == 'all' %}selected{% endif %}>All</option>
            <option value="yes" {% if has_website == 'yes' %}selected{% endif %}>Yes</option>
            <option value="no" {% if has_website == 'no' %}selected{% endif %}>No</option>
        </select>
        
        <label>Per Page:</label>
        <select onchange="updateFilters({per_page: this.value, page: 1})">
            <option value="50" {% if per_page == 50 %}selected{% endif %}>50</option>
            <option value="100" {% if per_page == 100 %}selected{% endif %}>100</option>
            <option value="200" {% if per_page == 200 %}selected{% endif %}>200</option>
            <option value="all" {% if per_page == 'all' %}selected{% endif %}>All</option>
        </select>
    </div>
    
    <div class="pagination">
        {% if page > 1 %}
        <a href="/?sort={{ sort }}&network={{ network }}&page={{ page - 1 }}&per_page={{ per_page }}{% if search %}&search={{ search }}{% endif %}" class="page-btn">← Previous</a>
        {% endif %}
        
        <span class="page-info">Page {{ page }} of {{ total_pages }}</span>
        
        {% if page < total_pages %}
        <a href="/?sort={{ sort }}&network={{ network }}&page={{ page + 1 }}&per_page={{ per_page }}{% if search %}&search={{ search }}{% endif %}" class="page-btn">Next →</a>
        {% endif %}
    </div>
    
    <table>
        <thead>
            <tr>
                <th>#</th>
                <th>Token</th>
                <th>Contract Address</th>
                <th>Network</th>
                <th><a href="/?sort=liquidity&network={{ network }}&page={{ page }}" style="color: inherit">Liquidity {{ '↓' if sort == 'liquidity' else '' }}</a></th>
                <th><a href="/?sort=volume&network={{ network }}&page={{ page }}" style="color: inherit">Volume 24h {{ '↓' if sort == 'volume' else '' }}</a></th>
                <th>Website</th>
                <th><a href="/?sort=recent&network={{ network }}&page={{ page }}" style="color: inherit">Age {{ '↓' if sort == 'recent' else '' }}</a></th>
                <th>Links</th>
            </tr>
        </thead>
        <tbody>
            {% for token in tokens %}
            <tr>
                <td style="color: #666; font-size: 12px;">{{ loop.index + showing_start - 1 }}</td>
                <td>
                    <span class="symbol">{{ token.symbol or 'Unknown' }}</span>
                </td>
                <td>
                    <div class="ca-container">
                        <span class="ca-text" onclick="copyCA('{{ token.contract_address }}', this)" title="Click to copy">
                            {{ token.contract_address[:6] }}...{{ token.contract_address[-4:] }}
                        </span>
                    </div>
                </td>
                <td>
                    <span class="network {{ token.network }}">{{ token.network }}</span>
                </td>
                <td class="liquidity">
                    ${{ "{:,.0f}".format(token.initial_liquidity_usd) }}
                </td>
                <td class="liquidity">
                    ${{ "{:,.0f}".format(token.initial_volume_24h or 0) }}
                </td>
                <td>
                    {% if token.website_url %}
                        <span class="has-website">✓ Yes</span>
                    {% else %}
                        <span class="no-website">-</span>
                    {% endif %}
                </td>
                <td class="age">
                    {{ token.age }}
                </td>
                <td class="links">
                    <a href="https://dexscreener.com/{{ 'ethereum' if token.network == 'eth' else token.network }}/{{ token.contract_address }}" 
                       target="_blank" class="link-btn">DexScreener</a>
                    <a href="https://www.geckoterminal.com/{{ token.network }}/pools/{{ token.pool_address }}" 
                       target="_blank" class="link-btn">GeckoTerminal</a>
                    {% if token.website_url %}
                    <a href="{{ token.website_url }}" target="_blank" class="link-btn">Website</a>
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>
"""

def format_age(timestamp):
    """Format age as human readable"""
    if not timestamp:
        return "Unknown"
    
    # Parse the timestamp - handle various formats
    try:
        # Remove timezone suffix and microseconds if present
        ts = timestamp.split('+')[0].split('.')[0]
        created = datetime.fromisoformat(ts)
    except:
        return "Unknown"
    
    now = datetime.now()
    diff = now - created
    
    hours = diff.total_seconds() / 3600
    if hours < 1:
        return f"{int(hours * 60)}m ago"
    elif hours < 24:
        return f"{int(hours)}h ago"
    else:
        return f"{int(hours / 24)}d ago"

@app.route('/')
def index():
    from flask import request
    import math
    
    # Get filter parameters
    sort = request.args.get('sort', 'liquidity')
    network = request.args.get('network', 'all')
    page = int(request.args.get('page', 1))
    per_page_str = request.args.get('per_page', '100')
    search = request.args.get('search', '').strip()
    has_website = request.args.get('has_website', 'all')
    
    # Handle 'all' option for per_page
    if per_page_str == 'all':
        per_page = 10000  # Large number to get all
    else:
        per_page = int(per_page_str)
    
    # Get total counts first
    total_count_query = supabase.table('token_discovery').select('*', count='exact')
    total_count_response = total_count_query.execute()
    total_tokens_db = total_count_response.count
    
    # Get count of tokens with websites
    website_count_query = supabase.table('token_discovery').select('*', count='exact').not_.is_('website_url', 'null')
    website_count_response = website_count_query.execute()
    total_with_websites_db = website_count_response.count
    
    # Build main query for filtered results
    query = supabase.table('token_discovery').select('*')
    count_query = supabase.table('token_discovery').select('*', count='exact')
    
    if network != 'all':
        query = query.eq('network', network)
        count_query = count_query.eq('network', network)
    
    if search:
        query = query.ilike('contract_address', f'%{search}%')
        count_query = count_query.ilike('contract_address', f'%{search}%')
    
    if has_website == 'yes':
        query = query.not_.is_('website_url', 'null')
        count_query = count_query.not_.is_('website_url', 'null')
    elif has_website == 'no':
        query = query.is_('website_url', 'null')
        count_query = count_query.is_('website_url', 'null')
    
    # Get filtered count
    count_response = count_query.execute()
    filtered_total = count_response.count
    
    # Calculate pagination
    total_pages = math.ceil(filtered_total / per_page) if per_page_str != 'all' else 1
    offset = (page - 1) * per_page
    
    # Apply sorting
    if sort == 'liquidity':
        query = query.order('initial_liquidity_usd', desc=True)
    elif sort == 'recent':
        query = query.order('first_seen_at', desc=True)
    elif sort == 'volume':
        query = query.order('initial_volume_24h', desc=True)
    elif sort == 'age':
        query = query.order('first_seen_at', desc=False)  # Oldest first
    
    # Apply pagination
    if per_page_str != 'all':
        query = query.range(offset, offset + per_page - 1)
    
    # Execute query
    response = query.execute()
    tokens = response.data
    
    # Add formatted age
    for token in tokens:
        token['age'] = format_age(token.get('first_seen_at'))
    
    # Calculate average liquidity from current page tokens (approximation)
    current_liquidities = [t.get('initial_liquidity_usd', 0) for t in tokens if t.get('initial_liquidity_usd')]
    avg_liquidity = sum(current_liquidities) / len(current_liquidities) if current_liquidities else 0
    
    # Calculate showing range
    showing_start = offset + 1 if tokens else 0
    showing_end = min(offset + len(tokens), filtered_total)
    
    return render_template_string(
        HTML_TEMPLATE,
        tokens=tokens,
        total_tokens_db=total_tokens_db,
        total_with_websites_db=total_with_websites_db,
        filtered_total=filtered_total,
        avg_liquidity=f"{avg_liquidity:,.0f}",
        sort=sort,
        network=network,
        search=search,
        has_website=has_website,
        page=page,
        per_page=per_page if per_page_str != 'all' else 'all',
        total_pages=total_pages,
        showing_start=showing_start,
        showing_end=showing_end
    )

if __name__ == '__main__':
    print("🚀 Token Viewer running at http://localhost:5020")
    print("Press Ctrl+C to stop")
    app.run(host='0.0.0.0', port=5020, debug=True)