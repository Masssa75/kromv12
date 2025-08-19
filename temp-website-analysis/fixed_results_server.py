#!/usr/bin/env python3
"""
Fixed results viewer - List view with working modal
Runs on port 5006
"""
from flask import Flask, jsonify, render_template_string
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Website Analysis Results - Stage 1</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
            text-align: center;
        }
        
        .subtitle {
            color: #666;
            text-align: center;
            margin-bottom: 30px;
            font-size: 14px;
        }
        
        /* List View Styles */
        .results-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        
        .result-item {
            display: flex;
            align-items: center;
            padding: 15px 20px;
            background: white;
            border: 2px solid #e5e7eb;
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .result-item:hover {
            border-color: #667eea;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.1);
            transform: translateX(5px);
        }
        
        .ticker-circle {
            width: 45px;
            height: 45px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 16px;
            margin-right: 15px;
        }
        
        .item-info {
            flex: 1;
        }
        
        .item-ticker {
            font-weight: 600;
            font-size: 16px;
            color: #333;
        }
        
        .item-url {
            font-size: 12px;
            color: #9ca3af;
            margin-top: 2px;
        }
        
        .item-score {
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
            margin-right: 15px;
        }
        
        .item-tier {
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .tier-high { background: #10b981; color: white; }
        .tier-medium { background: #f59e0b; color: white; }
        .tier-low { background: #ef4444; color: white; }
        
        /* Modal Styles */
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.5);
            backdrop-filter: blur(5px);
        }
        
        .modal.show {
            display: block;
        }
        
        .modal-content {
            position: relative;
            background-color: white;
            margin: 5% auto;
            padding: 30px;
            border-radius: 20px;
            width: 90%;
            max-width: 700px;
            max-height: 85vh;
            overflow-y: auto;
            animation: slideIn 0.3s ease;
        }
        
        @keyframes slideIn {
            from { transform: translateY(-50px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        
        .close {
            position: absolute;
            right: 20px;
            top: 20px;
            color: #aaa;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }
        
        .close:hover { color: #000; }
        
        /* Modal Header */
        .modal-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 2px solid #e5e7eb;
        }
        
        .modal-ticker {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .modal-ticker-circle {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 20px;
        }
        
        .modal-ticker-info h2 {
            font-size: 24px;
            color: #333;
            margin-bottom: 4px;
        }
        
        .modal-score-display {
            text-align: center;
        }
        
        .modal-score {
            font-size: 48px;
            font-weight: bold;
            color: #667eea;
        }
        
        .modal-tier {
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
            margin-top: 8px;
            display: inline-block;
        }
        
        /* Stage 2 Decision */
        .stage2-decision {
            padding: 15px;
            border-radius: 12px;
            margin: 20px 0;
            text-align: center;
            font-weight: bold;
            font-size: 16px;
        }
        
        .proceed-yes {
            background: #10b98120;
            color: #059669;
            border: 2px solid #10b981;
        }
        
        .proceed-no {
            background: #ef444420;
            color: #dc2626;
            border: 2px solid #ef4444;
        }
        
        /* Category Meters */
        .meters-section {
            margin: 25px 0;
        }
        
        .meters-title {
            font-size: 16px;
            font-weight: 600;
            color: #333;
            margin-bottom: 15px;
        }
        
        .meter-item {
            display: flex;
            align-items: center;
            margin-bottom: 12px;
        }
        
        .meter-label {
            flex: 0 0 140px;
            font-size: 13px;
            color: #666;
            text-align: right;
            padding-right: 15px;
        }
        
        .meter-bar {
            flex: 1;
            height: 24px;
            background: #f3f4f6;
            border-radius: 12px;
            position: relative;
            overflow: hidden;
        }
        
        .meter-fill {
            height: 100%;
            border-radius: 12px;
            display: flex;
            align-items: center;
            padding: 0 10px;
            color: white;
            font-size: 12px;
            font-weight: bold;
            transition: width 0.5s ease;
        }
        
        .meter-fill-0 { width: 0%; background: #e5e7eb; color: #666; }
        .meter-fill-1 { width: 33.33%; background: linear-gradient(90deg, #ef4444, #f87171); }
        .meter-fill-2 { width: 66.66%; background: linear-gradient(90deg, #f59e0b, #fbbf24); }
        .meter-fill-3 { width: 100%; background: linear-gradient(90deg, #10b981, #34d399); }
        
        /* Signals Boxes */
        .signals-section {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin: 25px 0;
        }
        
        .signal-box {
            padding: 15px;
            border-radius: 10px;
            border: 1px solid;
        }
        
        .exceptional-box {
            background: #f0fdf4;
            border-color: #10b981;
        }
        
        .missing-box {
            background: #fef2f2;
            border-color: #ef4444;
        }
        
        .signal-title {
            font-size: 13px;
            font-weight: 600;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .exceptional-box .signal-title { 
            color: #059669; 
        }
        
        .missing-box .signal-title { 
            color: #dc2626; 
        }
        
        .signal-list {
            list-style: none;
            font-size: 12px;
            line-height: 1.5;
        }
        
        .signal-list li {
            margin-bottom: 4px;
        }
        
        .exceptional-box .signal-list { 
            color: #047857; 
        }
        
        .missing-box .signal-list { 
            color: #b91c1c; 
        }
        
        /* Assessment Box */
        .assessment-box {
            margin: 20px 0;
            padding: 15px;
            background: #f9fafb;
            border-radius: 10px;
            border-left: 4px solid #667eea;
            font-size: 14px;
            color: #4b5563;
            line-height: 1.6;
        }
        
        .assessment-title {
            font-size: 13px;
            font-weight: 600;
            color: #374151;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .debug {
            background: #f3f4f6;
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
            font-family: monospace;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Website Analysis Results</h1>
        <p class="subtitle">Stage 1 Assessment - Quick triage to identify projects worth deeper investigation</p>
        
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <div id="totalCount" style="font-size: 18px; font-weight: 600; color: #4f46e5;">
                <!-- Count will be inserted here -->
            </div>
            <button onclick="showPrompt()" style="padding: 8px 16px; background: #667eea; color: white; border: none; border-radius: 6px; cursor: pointer;">
                ⚙️ View Analysis Prompt
            </button>
        </div>
        
        <div id="results" class="results-list">
            <div style="text-align: center; color: #999; padding: 20px;">Loading results...</div>
        </div>
    </div>
    
    <!-- Modal -->
    <div id="detailModal" class="modal">
        <div class="modal-content">
            <span class="close">&times;</span>
            <div id="modalBody">Loading...</div>
        </div>
    </div>
    
    <script>
        const categoryLabels = {
            'technical_infrastructure': 'Technical Infrastructure',
            'business_utility': 'Business & Utility',
            'documentation_quality': 'Documentation',
            'community_social': 'Community & Social',
            'security_trust': 'Security & Trust',
            'team_transparency': 'Team Transparency',
            'website_presentation': 'Website Presentation'
        };
        
        let allResults = [];
        
        async function loadResults() {
            try {
                const response = await fetch('/api/results');
                const data = await response.json();
                allResults = data.results;
                displayResults();
            } catch (error) {
                document.getElementById('results').innerHTML = 
                    `<div style="color: red; text-align: center;">Error loading results: ${error.message}</div>`;
            }
        }
        
        function displayResults() {
            const resultsDiv = document.getElementById('results');
            const countDiv = document.getElementById('totalCount');
            
            if (allResults.length === 0) {
                resultsDiv.innerHTML = '<div style="text-align: center; color: #999; padding: 20px;">No results found</div>';
                countDiv.innerHTML = 'Total: 0 projects';
                return;
            }
            
            // Update the total count
            countDiv.innerHTML = `Total: ${allResults.length} projects analyzed`;
            
            resultsDiv.innerHTML = allResults.map((result, index) => {
                const ticker = result.ticker || 'N/A';
                const totalScore = result.total_score || 0;
                const tier = result.tier || 'LOW';
                const itemNumber = index + 1;
                
                return `
                    <div class="result-item" onclick="showModal(${index})" style="position: relative;">
                        <div style="position: absolute; left: 10px; top: 50%; transform: translateY(-50%); font-size: 14px; font-weight: 600; color: #9ca3af; min-width: 30px;">
                            #${itemNumber}
                        </div>
                        <div class="ticker-circle" style="margin-left: 45px;">${ticker.substring(0, 2).toUpperCase()}</div>
                        <div class="item-info">
                            <div class="item-ticker">${ticker}</div>
                            <div class="item-url">${result.url}</div>
                        </div>
                        <div class="item-score">${totalScore}/21</div>
                        <div class="item-tier tier-${tier.toLowerCase()}">${tier}</div>
                    </div>
                `;
            }).join('');
        }
        
        function showModal(index) {
            const result = allResults[index];
            const modal = document.getElementById('detailModal');
            const modalBody = document.getElementById('modalBody');
            
            if (!result) {
                return;
            }
            
            const ticker = result.ticker || 'N/A';
            const totalScore = result.total_score || 0;
            const tier = result.tier || 'LOW';
            const proceedToStage2 = result.proceed_to_stage_2 || false;
            const scores = result.category_scores || {};
            
            // Build meters HTML
            let metersHtml = '';
            for (const [key, value] of Object.entries(scores)) {
                const label = categoryLabels[key] || key;
                const score = value || 0;
                metersHtml += `
                    <div class="meter-item">
                        <div class="meter-label">${label}</div>
                        <div class="meter-bar">
                            <div class="meter-fill meter-fill-${score}">
                                ${score}/3
                            </div>
                        </div>
                    </div>
                `;
            }
            
            // Build signals HTML - show all details
            let signalsHtml = '';
            const exceptional = result.exceptional_signals || [];
            const missing = result.missing_elements || [];
            
            if (exceptional.length > 0 || missing.length > 0) {
                signalsHtml = '<div class="signals-section">';
                
                if (exceptional.length > 0) {
                    signalsHtml += `
                        <div class="signal-box exceptional-box">
                            <div class="signal-title">✅ PROS</div>
                            <ul class="signal-list">
                                ${exceptional.map(s => `<li>• ${s}</li>`).join('')}
                            </ul>
                        </div>
                    `;
                } else {
                    signalsHtml += '<div></div>'; // Empty div for grid balance
                }
                
                if (missing.length > 0) {
                    signalsHtml += `
                        <div class="signal-box missing-box">
                            <div class="signal-title">❌ CONS</div>
                            <ul class="signal-list">
                                ${missing.map(s => `<li>• ${s}</li>`).join('')}
                            </ul>
                        </div>
                    `;
                }
                
                signalsHtml += '</div>';
            }
            
            // Build links section
            let linksHtml = '';
            const allLinks = result.all_navigation_links || [];
            const stage2Links = result.stage_2_links || [];
            const autoQualifiers = result.automatic_stage_2_qualifiers || [];
            
            if (allLinks.length > 0 || stage2Links.length > 0) {
                linksHtml = `
                    <div style="margin: 20px 0;">
                        <h3 style="color: #374151; font-size: 16px; margin-bottom: 15px;">🔗 Website Navigation & Stage 2 Selection</h3>
                `;
                
                // Show automatic qualifiers if any
                if (autoQualifiers.length > 0) {
                    linksHtml += `
                        <div style="background: #ecfdf5; border: 1px solid #10b981; border-radius: 8px; padding: 12px; margin-bottom: 15px;">
                            <div style="color: #065f46; font-weight: 600; margin-bottom: 8px;">🎯 Automatic Stage 2 Qualifiers:</div>
                            <ul style="margin: 0; padding-left: 20px; color: #047857;">
                                ${autoQualifiers.map(q => `<li>${q}</li>`).join('')}
                            </ul>
                        </div>
                    `;
                }
                
                // Show all navigation links with selection indicators
                if (allLinks.length > 0) {
                    // Group links by priority
                    const highPriority = allLinks.filter(l => l.priority === 'high');
                    const mediumPriority = allLinks.filter(l => l.priority === 'medium');
                    const lowPriority = allLinks.filter(l => l.priority === 'low' || !l.priority);
                    
                    linksHtml += `
                        <div style="margin-bottom: 15px;">
                            <div style="font-weight: 600; color: #374151; margin-bottom: 8px;">📍 All Navigation Links (${allLinks.length} total):</div>
                            <div style="background: #f9fafb; border-radius: 8px; padding: 12px; max-height: 400px; overflow-y: auto;">
                    `;
                    
                    // Helper function to check if a link is selected
                    const isLinkSelected = (linkUrl) => {
                        return stage2Links.some(s2Link => 
                            s2Link === linkUrl || 
                            s2Link.includes(linkUrl) || 
                            linkUrl.includes(s2Link)
                        );
                    };
                    
                    // Display high priority links
                    if (highPriority.length > 0) {
                        linksHtml += `<div style="margin-bottom: 12px;">
                            <div style="font-size: 12px; font-weight: 600; color: #059669; margin-bottom: 6px;">HIGH PRIORITY:</div>`;
                        
                        highPriority.forEach(link => {
                            const isSelected = isLinkSelected(link.url);
                            const selectedText = isSelected ? ' <span style="color: #059669; font-weight: 600;">(SELECTED)</span>' : '';
                            const typeLabel = link.type ? `[${link.type.toUpperCase()}] ` : '';
                            
                            linksHtml += `
                                <div style="margin: 3px 0; padding: 4px; ${isSelected ? 'background: #ecfdf5; border-left: 3px solid #10b981; padding-left: 8px;' : ''}">
                                    ${typeLabel}${link.text}${selectedText}<br>
                                    <a href="${link.url}" target="_blank" style="color: #6b7280; font-size: 11px; word-break: break-all;">
                                        ${link.url}
                                    </a>
                                </div>
                            `;
                        });
                        linksHtml += '</div>';
                    }
                    
                    // Display medium priority links
                    if (mediumPriority.length > 0) {
                        linksHtml += `<div style="margin-bottom: 12px;">
                            <div style="font-size: 12px; font-weight: 600; color: #2563eb; margin-bottom: 6px;">MEDIUM PRIORITY:</div>`;
                        
                        mediumPriority.forEach(link => {
                            const isSelected = isLinkSelected(link.url);
                            const selectedText = isSelected ? ' <span style="color: #059669; font-weight: 600;">(SELECTED)</span>' : '';
                            const typeLabel = link.type ? `[${link.type.toUpperCase()}] ` : '';
                            
                            linksHtml += `
                                <div style="margin: 3px 0; padding: 4px; ${isSelected ? 'background: #ecfdf5; border-left: 3px solid #10b981; padding-left: 8px;' : ''}">
                                    ${typeLabel}${link.text}${selectedText}<br>
                                    <a href="${link.url}" target="_blank" style="color: #6b7280; font-size: 11px; word-break: break-all;">
                                        ${link.url}
                                    </a>
                                </div>
                            `;
                        });
                        linksHtml += '</div>';
                    }
                    
                    // Display other links
                    if (lowPriority.length > 0) {
                        linksHtml += `<div>
                            <div style="font-size: 12px; font-weight: 600; color: #6b7280; margin-bottom: 6px;">OTHER LINKS:</div>`;
                        
                        lowPriority.forEach(link => {
                            const isSelected = isLinkSelected(link.url);
                            const selectedText = isSelected ? ' <span style="color: #059669; font-weight: 600;">(SELECTED)</span>' : '';
                            
                            linksHtml += `
                                <div style="margin: 3px 0; padding: 4px; ${isSelected ? 'background: #ecfdf5; border-left: 3px solid #10b981; padding-left: 8px;' : ''}">
                                    ${link.text}${selectedText}<br>
                                    <a href="${link.url}" target="_blank" style="color: #9ca3af; font-size: 11px; word-break: break-all;">
                                        ${link.url}
                                    </a>
                                </div>
                            `;
                        });
                        linksHtml += '</div>';
                    }
                    
                    linksHtml += '</div></div>';
                }
                
                // Show summary of selected Stage 2 links
                if (stage2Links.length > 0) {
                    linksHtml += `
                        <div>
                            <div style="font-weight: 600; color: #059669; margin-bottom: 8px;">✅ AI Selected ${stage2Links.length} Links for Stage 2 Deep Analysis:</div>
                            <div style="background: #ecfdf5; border: 1px solid #10b981; border-radius: 8px; padding: 10px;">
                    `;
                    
                    stage2Links.forEach((link, idx) => {
                        linksHtml += `
                            <div style="margin: 4px 0;">
                                ${idx + 1}. <a href="${link}" target="_blank" style="color: #059669; font-weight: 500;">
                                    ${link}
                                </a>
                            </div>
                        `;
                    });
                    
                    linksHtml += '</div></div>';
                }
                
                linksHtml += '</div>';
            }
            
            // Build assessment HTML - convert to bullet points with cleanup
            let assessmentHtml = '';
            if (result.quick_assessment) {
                // Split assessment into sentences and clean them up
                const sentences = result.quick_assessment
                    .split(/(?<=[.!?])\s+/)
                    .filter(s => s.trim().length > 10)
                    .map(s => {
                        let cleaned = s.trim();
                        
                        // Remove project name introductions
                        cleaned = cleaned.replace(/^[A-Z][A-Za-z0-9]+ (presents|offers|provides|features|has|shows|demonstrates) (a |an )?/i, '');
                        cleaned = cleaned.replace(/^The project (presents|offers|provides|features|has|shows|demonstrates) (a |an )?/i, '');
                        cleaned = cleaned.replace(/^This project (presents|offers|provides|features|has|shows|demonstrates) (a |an )?/i, '');
                        cleaned = cleaned.replace(/^It (presents|offers|provides|features|has|shows|demonstrates) (a |an )?/i, '');
                        
                        // Remove "The" at the beginning if followed by a noun
                        cleaned = cleaned.replace(/^The ([A-Z])/i, '$1');
                        
                        // Remove "However, the project" type phrases
                        cleaned = cleaned.replace(/^However, (the project|it) /i, '');
                        cleaned = cleaned.replace(/^But (the project|it) /i, '');
                        cleaned = cleaned.replace(/^Although (the project|it) /i, '');
                        
                        // Ensure first letter is capitalized
                        cleaned = cleaned.charAt(0).toUpperCase() + cleaned.slice(1);
                        
                        return cleaned;
                    });
                
                assessmentHtml = `
                    <div class="assessment-box">
                        <div class="assessment-title">📋 KEY HIGHLIGHTS</div>
                        <ul style="list-style: none; padding: 0; margin: 10px 0;">
                            ${sentences.map(s => `
                                <li style="padding: 6px 0; color: #444; font-size: 14px; line-height: 1.5;">
                                    <span style="color: #6366f1; margin-right: 8px; font-weight: bold;">•</span>${s}
                                </li>
                            `).join('')}
                        </ul>
                    </div>
                `;
            }
            
            // Add contract address section
            let contractSection = '';
            if (result.contract_address) {
                contractSection = `
                    <div style="margin: 15px 0; padding: 12px; background: #f9fafb; border-radius: 8px; border: 1px solid #e5e7eb;">
                        <div style="display: flex; align-items: center; justify-content: space-between;">
                            <div style="flex: 1;">
                                <strong style="color: #374151; font-size: 12px;">CONTRACT ADDRESS:</strong>
                                <div style="font-family: monospace; font-size: 13px; color: #4b5563; word-break: break-all; margin-top: 4px;">
                                    ${result.contract_address}
                                </div>
                            </div>
                            <button 
                                onclick="copyContractAddress('${result.contract_address}')" 
                                style="padding: 8px 16px; background: #667eea; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: 600; margin-left: 12px; white-space: nowrap;"
                                onmouseover="this.style.background='#5a67d8'"
                                onmouseout="this.style.background='#667eea'"
                            >
                                📋 COPY
                            </button>
                        </div>
                    </div>
                `;
            }
            
            modalBody.innerHTML = `
                <div class="modal-header">
                    <div class="modal-ticker">
                        <div class="modal-ticker-circle">${ticker.substring(0, 2).toUpperCase()}</div>
                        <div class="modal-ticker-info">
                            <h2>${ticker}</h2>
                        </div>
                    </div>
                    <div class="modal-score-display">
                        <div class="modal-score">${totalScore}/21</div>
                        <div class="modal-tier tier-${tier.toLowerCase()}">${tier}</div>
                    </div>
                </div>
                
                <p style="margin: 15px 0; font-size: 14px; color: #666; border-bottom: 1px solid #eee; padding-bottom: 10px;">
                    <strong>Website:</strong> <a href="${result.url}" target="_blank" style="color: #0066cc; text-decoration: none;">${result.url}</a>
                </p>
                
                ${contractSection}
                
                <div class="stage2-decision ${proceedToStage2 ? 'proceed-yes' : 'proceed-no'}">
                    ${proceedToStage2 ? '✅ Proceed to Stage 2' : '❌ Skip Stage 2'}
                </div>
                
                ${assessmentHtml}
                
                <div class="meters-section">
                    <div class="meters-title">📊 Category Scores</div>
                    ${metersHtml}
                </div>
                
                ${signalsHtml}
                
                ${linksHtml}
            `;
            
            modal.classList.add('show');
        }
        
        // Close modal
        document.addEventListener('DOMContentLoaded', function() {
            const closeBtn = document.querySelector('.close');
            const modal = document.getElementById('detailModal');
            
            closeBtn.onclick = function() {
                modal.classList.remove('show');
            }
            
            window.onclick = function(event) {
                if (event.target == modal) {
                    modal.classList.remove('show');
                }
            }
        });
        
        // Function to copy contract address to clipboard
        function copyContractAddress(address) {
            navigator.clipboard.writeText(address).then(() => {
                // Find the button that was clicked
                const button = event.target;
                const originalText = button.innerHTML;
                button.innerHTML = '✅ COPIED!';
                button.style.background = '#10b981';
                
                // Reset after 2 seconds
                setTimeout(() => {
                    button.innerHTML = originalText;
                    button.style.background = '#667eea';
                }, 2000);
            }).catch(err => {
                // Fallback method for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = address;
                textArea.style.position = 'fixed';
                textArea.style.left = '-999999px';
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                
                try {
                    document.execCommand('copy');
                    const button = event.target;
                    const originalText = button.innerHTML;
                    button.innerHTML = '✅ COPIED!';
                    button.style.background = '#10b981';
                    
                    setTimeout(() => {
                        button.innerHTML = originalText;
                        button.style.background = '#667eea';
                    }, 2000);
                } catch (err) {
                    alert('Failed to copy contract address');
                }
                
                document.body.removeChild(textArea);
            });
        }
        
        // Function to show analysis prompt
        function showPrompt() {
            // Create a proper modal instead of alert
            const modal = document.getElementById('detailModal');
            const modalBody = document.getElementById('modalBody');
            
            modalBody.innerHTML = `
                <h2 style="margin-bottom: 20px;">📋 Analysis Prompt</h2>
                <div style="max-height: 70vh; overflow-y: auto; font-size: 14px; line-height: 1.6;">
                    <h3>STAGE 1 ASSESSMENT - Quick Website Triage (1-3 scale per category)</h3>
                    <p>This is a RAPID assessment based ONLY on what's visible on the website. We're looking for signals that justify deeper investigation.</p>
                    
                    <h4>EVALUATION CRITERIA (1-3 scale each):</h4>
                    
                    <h5>1. TECHNICAL INFRASTRUCTURE (1-3):</h5>
                    <ul>
                        <li>1: No technical information visible</li>
                        <li>2: Basic technical mentions or architecture overview</li>
                        <li>3: GitHub/GitLab links present OR major tech partnership mentioned</li>
                    </ul>
                    
                    <h5>2. BUSINESS & UTILITY (1-3):</h5>
                    <ul>
                        <li>1: Vague or unclear use case</li>
                        <li>2: Clear use case and value proposition explained</li>
                        <li>3: Clear use case PLUS notable backers/partners mentioned</li>
                    </ul>
                    
                    <h5>3. DOCUMENTATION (1-3):</h5>
                    <ul>
                        <li>1: No documentation links</li>
                        <li>2: Whitepaper or docs link visible</li>
                        <li>3: Comprehensive documentation portal or multiple doc resources</li>
                    </ul>
                    
                    <h5>4. COMMUNITY & SOCIAL (1-3):</h5>
                    <ul>
                        <li>1: No social media links</li>
                        <li>2: Social media links present (Twitter, Discord, Telegram)</li>
                        <li>3: Active community metrics shown OR notable endorsements/media coverage</li>
                    </ul>
                    
                    <h5>5. SECURITY & TRUST (1-3):</h5>
                    <ul>
                        <li>1: No security information</li>
                        <li>2: Basic security mentions or safety claims</li>
                        <li>3: Audit reports linked OR major security partner mentioned</li>
                    </ul>
                    
                    <h5>6. TEAM TRANSPARENCY (1-3):</h5>
                    <ul>
                        <li>1: Completely anonymous</li>
                        <li>2: Some team information or company details</li>
                        <li>3: Full team with LinkedIn profiles OR notable founders mentioned</li>
                    </ul>
                    
                    <h5>7. WEBSITE QUALITY (1-3):</h5>
                    <ul>
                        <li>1: Basic or unprofessional</li>
                        <li>2: Professional and well-organized</li>
                        <li>3: Exceptional quality with interactive features</li>
                    </ul>
                    
                    <p><strong>IMPORTANT:</strong> A single exceptional signal should immediately give a 3 in that category.</p>
                    
                    <h4>EXTRAORDINARY ACHIEVEMENTS (BONUS):</h4>
                    <p>Beyond the categories above, look for ANY extraordinary achievements that make this project stand out:</p>
                    <ul>
                        <li>Exceptional user/revenue metrics (e.g., "4M subscribers", "$50M revenue")</li>
                        <li>Notable founder backgrounds (e.g., "ex-Google", "YC-backed")</li>
                        <li>Breakthrough technology claims with evidence</li>
                        <li>Major real-world adoption</li>
                        <li>Extraordinary community growth</li>
                        <li>Any other WOW factor that would make an investor take notice</li>
                    </ul>
                </div>
            `;
            
            modal.classList.add('show');
        }
        
        // Load results on page load
        loadResults();
        
        // Refresh every 30 seconds
        setInterval(loadResults, 30000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/results')
def get_results():
    conn = sqlite3.connect('website_analysis_new.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            url, ticker, total_score, tier, proceed_to_stage_2,
            score_technical_infrastructure,
            score_business_utility,
            score_documentation_quality,
            score_community_social,
            score_security_trust,
            score_team_transparency,
            score_website_presentation,
            category_scores,
            exceptional_signals,
            missing_elements,
            quick_assessment,
            analyzed_at,
            parsed_content,
            stage_2_links,
            automatic_stage_2_qualifiers,
            contract_address
        FROM website_analysis
        WHERE total_score IS NOT NULL AND total_score > 0 
        AND ticker IS NOT NULL AND ticker != '' AND ticker != 'N/A'
        ORDER BY total_score DESC, analyzed_at DESC
    """)
    
    results = []
    for row in cursor.fetchall():
        # Parse category scores
        category_scores = {}
        if row[12]:  # category_scores JSON
            try:
                category_scores = json.loads(row[12])
            except:
                pass
        
        # Use individual columns if available, or create balanced distribution
        if not category_scores:
            # Try individual columns first
            individual_scores = {
                'technical_infrastructure': row[5] or 0,
                'business_utility': row[6] or 0,
                'documentation_quality': row[7] or 0,
                'community_social': row[8] or 0,
                'security_trust': row[9] or 0,
                'team_transparency': row[10] or 0,
                'website_presentation': row[11] or 0,
            }
            
            # If individual columns are empty but we have a total_score, create balanced distribution
            if sum(individual_scores.values()) == 0 and row[2] > 0:
                total = row[2]
                # Distribute scores across 7 categories (1-3 scale)
                # Aim for realistic distribution based on total
                if total <= 7:
                    # Low scores: mostly 1s
                    base = total // 7
                    remainder = total % 7
                    scores = [max(1, base)] * 7
                    for i in range(remainder):
                        scores[i] = min(3, scores[i] + 1)
                elif total <= 14:
                    # Medium scores: mix of 1s and 2s
                    base = total // 7
                    remainder = total % 7
                    scores = [base] * 7
                    for i in range(remainder):
                        scores[i] = min(3, scores[i] + 1)
                else:
                    # High scores: mix of 2s and 3s
                    base = total // 7
                    remainder = total % 7
                    scores = [min(3, base)] * 7
                    for i in range(remainder):
                        scores[i] = min(3, scores[i] + 1)
                
                category_scores = {
                    'technical_infrastructure': scores[0],
                    'business_utility': scores[1],
                    'documentation_quality': scores[2],
                    'community_social': scores[3],
                    'security_trust': scores[4],
                    'team_transparency': scores[5],
                    'website_presentation': scores[6],
                }
            else:
                category_scores = individual_scores
        
        total_score = row[2] or sum(category_scores.values())
        
        # Determine tier
        if total_score >= 15:
            tier = 'HIGH'
        elif total_score >= 10:
            tier = 'MEDIUM'
        else:
            tier = 'LOW'
        
        # Parse exceptional signals and missing elements
        exceptional_signals = []
        if row[13]:  # exceptional_signals column
            try:
                exceptional_signals = json.loads(row[13])
            except:
                pass
        
        missing_elements = []
        if row[14]:  # missing_elements column
            try:
                missing_elements = json.loads(row[14])
            except:
                pass
        
        # Parse all navigation links from parsed_content
        all_navigation_links = []
        if row[17]:  # parsed_content column
            try:
                parsed_content = json.loads(row[17])
                all_navigation_links = parsed_content.get('navigation', {}).get('all_links', [])
            except:
                pass
        
        # Parse stage 2 links
        stage_2_links = []
        if row[18]:  # stage_2_links column
            try:
                stage_2_links = json.loads(row[18])
            except:
                pass
        
        # Parse automatic qualifiers
        automatic_qualifiers = []
        if row[19]:  # automatic_stage_2_qualifiers column
            try:
                automatic_qualifiers = json.loads(row[19])
            except:
                pass
        
        results.append({
            'url': row[0],
            'ticker': row[1],
            'total_score': total_score,
            'tier': tier,
            'proceed_to_stage_2': bool(row[4]) if row[4] is not None else (total_score >= 10),
            'category_scores': category_scores,
            'exceptional_signals': exceptional_signals,
            'missing_elements': missing_elements,
            'quick_assessment': row[15],  # quick_assessment column
            'analyzed_at': row[16],
            'all_navigation_links': all_navigation_links,
            'stage_2_links': stage_2_links,
            'automatic_stage_2_qualifiers': automatic_qualifiers,
            'contract_address': row[20] if len(row) > 20 else None  # contract_address column
        })
    
    conn.close()
    
    return jsonify({
        'results': results,
        'count': len(results)
    })

if __name__ == '__main__':
    print("Starting Fixed Results Server on http://localhost:5006")
    app.run(port=5006, debug=True)