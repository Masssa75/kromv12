#!/usr/bin/env python3
"""
Flask server to view CA verification results with manual verification tracking
"""

from flask import Flask, render_template_string, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CA Verification Results - Manual Verification</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1500px;
            margin: 0 auto;
        }
        
        h1 {
            color: white;
            text-align: center;
            margin-bottom: 10px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        
        .subtitle {
            color: rgba(255,255,255,0.9);
            text-align: center;
            margin-bottom: 30px;
            font-size: 1.2em;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            text-align: center;
        }
        
        .stat-number {
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .stat-label {
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .legitimate { color: #10b981; }
        .fake { color: #ef4444; }
        .error { color: #f59e0b; }
        .total { color: #6366f1; }
        .verified { color: #8b5cf6; }
        .wrong { color: #ec4899; }
        
        .results-table {
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 1px;
        }
        
        td {
            padding: 12px 15px;
            border-bottom: 1px solid #f0f0f0;
        }
        
        tr:hover {
            background: #f9fafb;
        }
        
        tr.manually-verified {
            background: #f0fdf4;
        }
        
        tr.manually-wrong {
            background: #fef2f2;
        }
        
        .verdict-badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
        }
        
        .verdict-legitimate {
            background: #d1fae5;
            color: #065f46;
        }
        
        .verdict-fake {
            background: #fee2e2;
            color: #991b1b;
        }
        
        .verdict-error {
            background: #fed7aa;
            color: #92400e;
        }
        
        .verdict-no-website {
            background: #e5e7eb;
            color: #4b5563;
        }
        
        .location-type {
            display: inline-block;
            padding: 3px 8px;
            background: #eff6ff;
            color: #1e40af;
            border-radius: 5px;
            font-size: 0.8em;
        }
        
        .contract-address {
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
            color: #6b7280;
            cursor: pointer;
            transition: all 0.2s;
            word-break: break-all;
            max-width: 250px;
            display: inline-block;
        }
        
        .contract-address:hover {
            color: #4b5563;
            background: #f3f4f6;
            padding: 2px 4px;
            border-radius: 3px;
        }
        
        .search-btn {
            background: #6366f1;
            color: white;
            border: none;
            padding: 4px 8px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.9em;
            transition: all 0.2s;
            min-width: 32px;
        }
        
        .search-btn:hover {
            background: #4f46e5;
            transform: scale(1.05);
        }
        
        .website-link {
            color: #6366f1;
            text-decoration: none;
            word-break: break-all;
        }
        
        .website-link:hover {
            text-decoration: underline;
        }
        
        .found-location {
            font-size: 0.85em;
            word-break: break-all;
        }
        
        .location-link {
            color: #10b981;
            text-decoration: none;
            transition: all 0.2s;
        }
        
        .location-link:hover {
            color: #059669;
            text-decoration: underline;
        }
        
        .error-message {
            color: #ef4444;
            font-size: 0.85em;
        }
        
        .ticker-badge {
            font-weight: bold;
            color: #1f2937;
        }
        
        .network-badge {
            display: inline-block;
            padding: 2px 6px;
            background: #f3f4f6;
            color: #6b7280;
            border-radius: 3px;
            font-size: 0.75em;
            text-transform: uppercase;
        }
        
        .urls-checked {
            color: #6b7280;
            font-size: 0.9em;
        }
        
        .timestamp {
            color: #9ca3af;
            font-size: 0.8em;
        }
        
        .refresh-note {
            text-align: center;
            color: rgba(255,255,255,0.8);
            margin-top: 20px;
            font-size: 0.9em;
        }
        
        .verification-buttons {
            display: flex;
            gap: 8px;
            align-items: center;
        }
        
        .verify-btn {
            padding: 5px 10px;
            border-radius: 5px;
            border: none;
            font-size: 0.85em;
            cursor: pointer;
            transition: all 0.2s;
            font-weight: 600;
        }
        
        .verify-correct {
            background: #d1fae5;
            color: #065f46;
        }
        
        .verify-correct:hover {
            background: #a7f3d0;
        }
        
        .verify-wrong {
            background: #fee2e2;
            color: #991b1b;
        }
        
        .verify-wrong:hover {
            background: #fecaca;
        }
        
        .add-notes {
            background: #fef3c7;
            color: #92400e;
        }
        
        .add-notes:hover {
            background: #fde68a;
        }
        
        .manual-status {
            display: flex;
            align-items: center;
            gap: 5px;
            font-size: 1.2em;
        }
        
        .status-verified {
            color: #10b981;
        }
        
        .status-wrong {
            color: #ef4444;
        }
        
        .manual-notes {
            font-size: 0.8em;
            color: #6b7280;
            margin-top: 4px;
            font-style: italic;
        }
        
        .notes-modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 10000;
            align-items: center;
            justify-content: center;
        }
        
        .notes-modal-content {
            background: white;
            padding: 30px;
            border-radius: 15px;
            max-width: 500px;
            width: 90%;
        }
        
        .notes-textarea {
            width: 100%;
            height: 100px;
            margin: 10px 0;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-family: inherit;
        }
        
        .modal-buttons {
            display: flex;
            gap: 10px;
            justify-content: flex-end;
        }
        
        .modal-btn {
            padding: 8px 16px;
            border-radius: 5px;
            border: none;
            cursor: pointer;
            font-weight: 600;
        }
        
        .modal-save {
            background: #6366f1;
            color: white;
        }
        
        .modal-cancel {
            background: #e5e7eb;
            color: #4b5563;
        }
        
        .filter-controls {
            background: white;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: flex;
            gap: 15px;
            align-items: center;
        }
        
        .filter-btn {
            padding: 6px 12px;
            border-radius: 5px;
            border: 1px solid #ddd;
            background: white;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .filter-btn.active {
            background: #6366f1;
            color: white;
            border-color: #6366f1;
        }
        
        .bulk-actions {
            margin-left: auto;
        }
        
        .bulk-btn {
            padding: 8px 16px;
            background: #8b5cf6;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: 600;
        }
        
        .bulk-btn:hover {
            background: #7c3aed;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 CA Verification Results</h1>
        <div class="subtitle">Manual Verification Tracking System</div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number total">{{ stats.total }}</div>
                <div class="stat-label">Total Tokens</div>
            </div>
            <div class="stat-card">
                <div class="stat-number legitimate">{{ stats.legitimate }}</div>
                <div class="stat-label">Legitimate</div>
            </div>
            <div class="stat-card">
                <div class="stat-number fake">{{ stats.fake }}</div>
                <div class="stat-label">Fake/Imposter</div>
            </div>
            <div class="stat-card">
                <div class="stat-number error">{{ stats.error }}</div>
                <div class="stat-label">Errors/No Site</div>
            </div>
            <div class="stat-card">
                <div class="stat-number verified">{{ stats.manually_verified }}</div>
                <div class="stat-label">Manually Verified</div>
            </div>
            <div class="stat-card">
                <div class="stat-number wrong">{{ stats.manually_wrong }}</div>
                <div class="stat-label">Marked Wrong</div>
            </div>
        </div>
        
        <div class="filter-controls">
            <span style="font-weight: 600;">Filter:</span>
            <button class="filter-btn active" onclick="filterResults('all')">All</button>
            <button class="filter-btn" onclick="filterResults('unverified')">Unverified</button>
            <button class="filter-btn" onclick="filterResults('verified')">Verified ✓</button>
            <button class="filter-btn" onclick="filterResults('wrong')">Wrong ⚠️</button>
            <div class="bulk-actions">
                <button class="bulk-btn" onclick="markVisibleAsVerified()">Mark Visible as Verified</button>
            </div>
        </div>
        
        <div class="results-table">
            <table>
                <thead>
                    <tr>
                        <th>Token</th>
                        <th>Contract</th>
                        <th>Website</th>
                        <th>System Verdict</th>
                        <th>Found Location</th>
                        <th>Manual Verification</th>
                    </tr>
                </thead>
                <tbody id="results-tbody">
                    {% for result in results %}
                    <tr data-ticker="{{ result.ticker }}" 
                        data-network="{{ result.network }}" 
                        data-contract="{{ result.contract_address }}"
                        data-filter-status="{% if result.manual_verdict == 'CORRECT' %}verified{% elif result.manual_verdict == 'WRONG' %}wrong{% else %}unverified{% endif %}"
                        class="{% if result.manual_verdict == 'CORRECT' %}manually-verified{% elif result.manual_verdict == 'WRONG' %}manually-wrong{% endif %}">
                        <td>
                            <span class="ticker-badge">{{ result.ticker }}</span>
                            <span class="network-badge">{{ result.network }}</span>
                        </td>
                        <td>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <span class="contract-address" title="Click to copy" onclick="copyToClipboard('{{ result.contract_address }}', this)">
                                    {{ result.contract_address }}
                                </span>
                                <button class="search-btn" onclick="searchGoogleSite('{{ result.website_url }}', '{{ result.contract_address }}')" title="Search contract on website">
                                    🔍
                                </button>
                            </div>
                        </td>
                        <td>
                            {% if result.website_url and result.website_url != 'None' %}
                                <a href="{{ result.website_url }}" target="_blank" class="website-link">
                                    {{ result.website_url[:30] }}{% if result.website_url|length > 30 %}...{% endif %}
                                </a>
                            {% else %}
                                <span style="color: #9ca3af;">No website</span>
                            {% endif %}
                        </td>
                        <td>
                            <span class="verdict-badge verdict-{{ result.verdict.lower().replace('_', '-') }}">
                                {% if result.verdict == 'LEGITIMATE' %}
                                    ✅ {{ result.verdict }}
                                {% elif result.verdict == 'FAKE' %}
                                    🚫 {{ result.verdict }}
                                {% elif result.verdict == 'ERROR' or result.verdict == 'WEBSITE_DOWN' %}
                                    ❌ {{ result.verdict }}
                                {% else %}
                                    ⚫ {{ result.verdict }}
                                {% endif %}
                            </span>
                            {% if result.warning_flags %}
                                <div style="margin-top: 5px;">
                                    <span style="background: #fef3c7; color: #92400e; padding: 3px 8px; border-radius: 5px; font-size: 0.75em; display: inline-block;">
                                        ⚠️ {{ result.warning_flags }}
                                    </span>
                                </div>
                            {% endif %}
                        </td>
                        <td>
                            {% if result.found_location %}
                                <div class="found-location">
                                    <span class="location-type">{{ result.location_type or 'found' }}</span>
                                    <br>
                                    <a href="{{ result.found_location }}" target="_blank" class="location-link" 
                                       onclick="openAndSearch('{{ result.found_location }}', '{{ result.contract_address }}'); return false;">
                                        {{ result.found_location[:40] }}{% if result.found_location|length > 40 %}...{% endif %}
                                    </a>
                                </div>
                            {% elif result.error %}
                                <div class="error-message">
                                    {{ result.error[:40] }}{% if result.error|length > 40 %}...{% endif %}
                                </div>
                            {% else %}
                                <span style="color: #9ca3af;">-</span>
                            {% endif %}
                        </td>
                        <td>
                            <div id="verification-{{ result.ticker }}-{{ result.network }}-{{ result.contract_address }}">
                                {% if result.manual_verdict == 'CORRECT' %}
                                    <div class="manual-status">
                                        <span class="status-verified">✓ Verified</span>
                                        <button class="verify-btn verify-wrong" onclick="markAsWrong('{{ result.ticker }}', '{{ result.network }}', '{{ result.contract_address }}')">Change</button>
                                    </div>
                                {% elif result.manual_verdict == 'WRONG' %}
                                    <div class="manual-status">
                                        <span class="status-wrong">⚠️ Wrong</span>
                                        <button class="verify-btn verify-correct" onclick="markAsVerified('{{ result.ticker }}', '{{ result.network }}', '{{ result.contract_address }}')">Change</button>
                                    </div>
                                {% else %}
                                    <div class="verification-buttons">
                                        <button class="verify-btn verify-correct" onclick="markAsVerified('{{ result.ticker }}', '{{ result.network }}', '{{ result.contract_address }}')">✓ Correct</button>
                                        <button class="verify-btn verify-wrong" onclick="markAsWrong('{{ result.ticker }}', '{{ result.network }}', '{{ result.contract_address }}')">⚠️ Wrong</button>
                                        <button class="verify-btn add-notes" onclick="showNotesModal('{{ result.ticker }}', '{{ result.network }}', '{{ result.contract_address }}')">📝</button>
                                    </div>
                                {% endif %}
                                {% if result.manual_notes %}
                                    <div class="manual-notes">{{ result.manual_notes }}</div>
                                {% endif %}
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        
        <div class="refresh-note">
            Page auto-refreshes every 30 seconds | Last updated: {{ current_time }}
            <br>
            <small>Keyboard shortcuts: Y = Mark as Verified, N = Mark as Wrong, / = Add Notes</small>
        </div>
    </div>
    
    <!-- Notes Modal -->
    <div id="notesModal" class="notes-modal">
        <div class="notes-modal-content">
            <h3>Add Notes</h3>
            <p id="notesModalToken" style="margin: 10px 0; color: #6b7280;"></p>
            <textarea id="notesTextarea" class="notes-textarea" placeholder="Enter your notes here..."></textarea>
            <div class="modal-buttons">
                <button class="modal-btn modal-cancel" onclick="closeNotesModal()">Cancel</button>
                <button class="modal-btn modal-save" onclick="saveNotes()">Save</button>
            </div>
        </div>
    </div>
    
    <script>
        let currentNotesToken = null;
        let currentFilter = 'all';
        
        // Auto-refresh every 30 seconds
        setTimeout(() => {
            window.location.reload();
        }, 30000);
        
        // Copy to clipboard function
        function copyToClipboard(text, element) {
            navigator.clipboard.writeText(text).then(() => {
                const originalText = element.innerText;
                element.innerText = '✓ Copied!';
                element.style.color = '#10b981';
                
                setTimeout(() => {
                    element.innerText = originalText;
                    element.style.color = '';
                }, 2000);
            }).catch(err => {
                console.error('Failed to copy:', err);
            });
        }
        
        // Mark as verified (correct)
        function markAsVerified(ticker, network, contract) {
            fetch('/mark_verified', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ticker, network, contract})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateVerificationUI(ticker, network, contract, 'verified');
                    showTooltip('Marked as verified ✓');
                }
            })
            .catch(err => console.error('Error:', err));
        }
        
        // Mark as wrong
        function markAsWrong(ticker, network, contract) {
            fetch('/mark_wrong', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ticker, network, contract})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateVerificationUI(ticker, network, contract, 'wrong');
                    showTooltip('Marked as wrong ⚠️');
                }
            })
            .catch(err => console.error('Error:', err));
        }
        
        // Show notes modal
        function showNotesModal(ticker, network, contract) {
            currentNotesToken = {ticker, network, contract};
            document.getElementById('notesModalToken').textContent = `${ticker} (${network})`;
            document.getElementById('notesModal').style.display = 'flex';
            document.getElementById('notesTextarea').focus();
        }
        
        // Close notes modal
        function closeNotesModal() {
            document.getElementById('notesModal').style.display = 'none';
            document.getElementById('notesTextarea').value = '';
            currentNotesToken = null;
        }
        
        // Save notes
        function saveNotes() {
            if (!currentNotesToken) return;
            
            const notes = document.getElementById('notesTextarea').value;
            
            fetch('/add_notes', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    ticker: currentNotesToken.ticker,
                    network: currentNotesToken.network,
                    contract: currentNotesToken.contract,
                    notes: notes
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showTooltip('Notes saved 📝');
                    closeNotesModal();
                    setTimeout(() => window.location.reload(), 1000);
                }
            })
            .catch(err => console.error('Error:', err));
        }
        
        // Update UI after verification
        function updateVerificationUI(ticker, network, contract, status) {
            const row = document.querySelector(`tr[data-ticker="${ticker}"][data-network="${network}"][data-contract="${contract}"]`);
            const verificationDiv = document.getElementById(`verification-${ticker}-${network}-${contract}`);
            
            if (status === 'verified') {
                row.classList.add('manually-verified');
                row.classList.remove('manually-wrong');
                row.setAttribute('data-filter-status', 'verified');
                verificationDiv.innerHTML = `
                    <div class="manual-status">
                        <span class="status-verified">✓ Verified</span>
                        <button class="verify-btn verify-wrong" onclick="markAsWrong('${ticker}', '${network}', '${contract}')">Change</button>
                    </div>
                `;
            } else if (status === 'wrong') {
                row.classList.add('manually-wrong');
                row.classList.remove('manually-verified');
                row.setAttribute('data-filter-status', 'wrong');
                verificationDiv.innerHTML = `
                    <div class="manual-status">
                        <span class="status-wrong">⚠️ Wrong</span>
                        <button class="verify-btn verify-correct" onclick="markAsVerified('${ticker}', '${network}', '${contract}')">Change</button>
                    </div>
                `;
            }
            
            // Update stats
            updateStats();
        }
        
        // Update statistics
        function updateStats() {
            const verified = document.querySelectorAll('tr.manually-verified').length;
            const wrong = document.querySelectorAll('tr.manually-wrong').length;
            
            // Update stat cards (would need to add IDs to stat cards to update them)
            // For now, just log the changes
            console.log(`Verified: ${verified}, Wrong: ${wrong}`);
        }
        
        // Filter results
        function filterResults(filter) {
            currentFilter = filter;
            const rows = document.querySelectorAll('#results-tbody tr');
            
            // Update filter button states
            document.querySelectorAll('.filter-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            event.target.classList.add('active');
            
            rows.forEach(row => {
                const status = row.getAttribute('data-filter-status');
                
                if (filter === 'all') {
                    row.style.display = '';
                } else if (filter === status) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        }
        
        // Mark all visible as verified
        function markVisibleAsVerified() {
            if (!confirm('Mark all currently visible tokens as verified?')) return;
            
            const visibleRows = document.querySelectorAll('#results-tbody tr:not([style*="display: none"])');
            const tokens = [];
            
            visibleRows.forEach(row => {
                const status = row.getAttribute('data-filter-status');
                if (status === 'unverified') {
                    tokens.push({
                        ticker: row.getAttribute('data-ticker'),
                        network: row.getAttribute('data-network'),
                        contract: row.getAttribute('data-contract')
                    });
                }
            });
            
            if (tokens.length === 0) {
                showTooltip('No unverified tokens to mark');
                return;
            }
            
            fetch('/bulk_verify', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({tokens})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showTooltip(`Marked ${tokens.length} tokens as verified`);
                    setTimeout(() => window.location.reload(), 1500);
                }
            })
            .catch(err => console.error('Error:', err));
        }
        
        // Open website and search for contract
        function openAndSearch(url, contractAddress) {
            const newWindow = window.open(url, '_blank');
            
            navigator.clipboard.writeText(contractAddress).then(() => {
                showTooltip('Contract copied! Use Ctrl+F (or Cmd+F) to search on the opened page');
            }).catch(err => {
                console.error('Failed to copy contract:', err);
            });
        }
        
        // Show tooltip message
        function showTooltip(message) {
            let tooltip = document.getElementById('search-tooltip');
            if (!tooltip) {
                tooltip = document.createElement('div');
                tooltip.id = 'search-tooltip';
                tooltip.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: #10b981;
                    color: white;
                    padding: 12px 20px;
                    border-radius: 8px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    z-index: 10000;
                    font-size: 14px;
                    animation: slideIn 0.3s ease;
                `;
                document.body.appendChild(tooltip);
            }
            
            tooltip.textContent = message;
            tooltip.style.display = 'block';
            
            setTimeout(() => {
                tooltip.style.display = 'none';
            }, 3000);
        }
        
        // Search contract on website using Google site: search
        function searchGoogleSite(websiteUrl, contractAddress) {
            if (!websiteUrl || websiteUrl === 'None') {
                const searchQuery = `"${contractAddress}"`;
                const googleUrl = `https://www.google.com/search?q=${encodeURIComponent(searchQuery)}`;
                window.open(googleUrl, '_blank');
                return;
            }
            
            let domain = websiteUrl;
            try {
                const url = new URL(websiteUrl);
                domain = url.hostname.replace('www.', '');
            } catch (e) {
                domain = websiteUrl.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0];
            }
            
            const searchQuery = `site:${domain} "${contractAddress}"`;
            const googleUrl = `https://www.google.com/search?q=${encodeURIComponent(searchQuery)}`;
            window.open(googleUrl, '_blank');
        }
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Only work when not typing in textarea
            if (e.target.tagName === 'TEXTAREA' || e.target.tagName === 'INPUT') return;
            
            if (e.key === 'y' || e.key === 'Y') {
                // Mark the first unverified token as verified
                const firstUnverified = document.querySelector('tr[data-filter-status="unverified"]');
                if (firstUnverified) {
                    const ticker = firstUnverified.getAttribute('data-ticker');
                    const network = firstUnverified.getAttribute('data-network');
                    const contract = firstUnverified.getAttribute('data-contract');
                    markAsVerified(ticker, network, contract);
                }
            } else if (e.key === 'n' || e.key === 'N') {
                // Mark the first unverified token as wrong
                const firstUnverified = document.querySelector('tr[data-filter-status="unverified"]');
                if (firstUnverified) {
                    const ticker = firstUnverified.getAttribute('data-ticker');
                    const network = firstUnverified.getAttribute('data-network');
                    const contract = firstUnverified.getAttribute('data-contract');
                    markAsWrong(ticker, network, contract);
                }
            } else if (e.key === '/') {
                e.preventDefault();
                // Open notes for the first unverified token
                const firstUnverified = document.querySelector('tr[data-filter-status="unverified"]');
                if (firstUnverified) {
                    const ticker = firstUnverified.getAttribute('data-ticker');
                    const network = firstUnverified.getAttribute('data-network');
                    const contract = firstUnverified.getAttribute('data-contract');
                    showNotesModal(ticker, network, contract);
                }
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    conn = sqlite3.connect('utility_tokens_ca.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all verification results with manual verification data
    cursor.execute("""
        SELECT 
            ticker,
            network,
            contract_address,
            website_url,
            verdict,
            found_location,
            location_type,
            urls_checked,
            error,
            verified_at,
            manual_verified,
            manual_verdict,
            manual_notes,
            manual_verified_at,
            source_type,
            warning_flags
        FROM ca_verification_results
        ORDER BY 
            CASE 
                WHEN manual_verdict = 'WRONG' THEN 0
                WHEN manual_verdict IS NULL THEN 1
                WHEN manual_verdict = 'CORRECT' THEN 2
            END,
            CASE verdict 
                WHEN 'LEGITIMATE' THEN 1
                WHEN 'FAKE' THEN 2
                WHEN 'ERROR' THEN 3
                WHEN 'WEBSITE_DOWN' THEN 4
                ELSE 5
            END,
            ticker
    """)
    
    results = cursor.fetchall()
    
    # Calculate statistics
    stats = {
        'total': len(results),
        'legitimate': sum(1 for r in results if r['verdict'] == 'LEGITIMATE'),
        'fake': sum(1 for r in results if r['verdict'] == 'FAKE'),
        'error': sum(1 for r in results if r['verdict'] in ['ERROR', 'WEBSITE_DOWN', 'NO_WEBSITE']),
        'manually_verified': sum(1 for r in results if r['manual_verdict'] == 'CORRECT'),
        'manually_wrong': sum(1 for r in results if r['manual_verdict'] == 'WRONG')
    }
    
    conn.close()
    
    return render_template_string(
        HTML_TEMPLATE,
        results=results,
        stats=stats,
        current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )

@app.route('/mark_verified', methods=['POST'])
def mark_verified():
    data = request.json
    ticker = data['ticker']
    network = data['network']
    contract = data['contract']
    
    conn = sqlite3.connect('utility_tokens_ca.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE ca_verification_results 
        SET manual_verified = 1,
            manual_verdict = 'CORRECT',
            manual_verified_at = datetime('now')
        WHERE ticker = ? AND network = ? AND contract_address = ?
    """, (ticker, network, contract))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/mark_wrong', methods=['POST'])
def mark_wrong():
    data = request.json
    ticker = data['ticker']
    network = data['network']
    contract = data['contract']
    
    conn = sqlite3.connect('utility_tokens_ca.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE ca_verification_results 
        SET manual_verified = 1,
            manual_verdict = 'WRONG',
            manual_verified_at = datetime('now')
        WHERE ticker = ? AND network = ? AND contract_address = ?
    """, (ticker, network, contract))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/add_notes', methods=['POST'])
def add_notes():
    data = request.json
    ticker = data['ticker']
    network = data['network']
    contract = data['contract']
    notes = data['notes']
    
    conn = sqlite3.connect('utility_tokens_ca.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE ca_verification_results 
        SET manual_notes = ?,
            manual_verified_at = datetime('now')
        WHERE ticker = ? AND network = ? AND contract_address = ?
    """, (notes, ticker, network, contract))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/bulk_verify', methods=['POST'])
def bulk_verify():
    data = request.json
    tokens = data['tokens']
    
    conn = sqlite3.connect('utility_tokens_ca.db')
    cursor = conn.cursor()
    
    for token in tokens:
        cursor.execute("""
            UPDATE ca_verification_results 
            SET manual_verified = 1,
                manual_verdict = 'CORRECT',
                manual_verified_at = datetime('now')
            WHERE ticker = ? AND network = ? AND contract_address = ?
        """, (token['ticker'], token['network'], token['contract']))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'count': len(tokens)})

if __name__ == '__main__':
    print("="*60)
    print("CA VERIFICATION RESULTS VIEWER - ENHANCED")
    print("="*60)
    print("Starting server at http://localhost:5003")
    print("Press Ctrl+C to stop")
    print("")
    print("Keyboard Shortcuts:")
    print("  Y - Mark first unverified as correct")
    print("  N - Mark first unverified as wrong")
    print("  / - Add notes to first unverified")
    print("="*60)
    app.run(debug=True, port=5003, host='0.0.0.0')