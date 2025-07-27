#!/usr/bin/env python3
"""
Autonomous fixer - tests the visualization and automatically applies fixes
"""

import time
import subprocess
import requests
import json
import os
import re

class AutonomousFixer:
    def __init__(self):
        self.fix_count = 0
        self.last_test_result = None
        self.fixes_applied = []
        
    def test_visualization(self):
        """Test if visualization is working"""
        try:
            response = requests.post('http://localhost:5001/api/chat', 
                json={
                    'message': 'Create a simple bar chart showing the top 10 groups by average ROI',
                    'session_id': f'auto_fix_{self.fix_count}'
                },
                timeout=30
            )
            
            data = response.json()
            
            # Check server logs for detailed info
            log_output = self.get_recent_logs()
            
            return {
                'success': 'visualization' in data,
                'tools_used': data.get('tools_used', []),
                'has_json_block': '```json' in data.get('response', ''),
                'log_errors': self.extract_errors_from_logs(log_output),
                'response_text': data.get('response', '')[:500]
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_recent_logs(self):
        """Get recent server logs (would need to be implemented based on your logging setup)"""
        # For now, return empty - in reality would tail the log file
        return ""
    
    def extract_errors_from_logs(self, logs):
        """Extract error patterns from logs"""
        errors = []
        if "Expecting ',' delimiter" in logs:
            errors.append("json_delimiter_error")
        if "triple quotes" in logs:
            errors.append("triple_quote_error")
        if "Failed to parse JSON" in logs:
            errors.append("json_parse_error")
        return errors
    
    def apply_fix(self, fix_type):
        """Apply a specific fix to the code"""
        print(f"\n🔧 Applying fix: {fix_type}")
        
        if fix_type == "enhance_parser":
            # Read the current parser
            with open('all-in-one-server.py', 'r') as f:
                content = f.read()
            
            # Apply a fix (example: make the regex more flexible)
            if 'json_blocks = re.findall' in content:
                # Make the regex more flexible
                old_pattern = r'json_blocks = re.findall\(r\'```json\\s\*\(.*?\)\\s\*```\', response_text, re.DOTALL\)'
                new_pattern = r'json_blocks = re.findall(r\'```json\\s*([\\s\\S]*?)\\s*```\', response_text, re.DOTALL)'
                
                content = re.sub(old_pattern, new_pattern, content)
                
                with open('all-in-one-server.py', 'w') as f:
                    f.write(content)
                
                print("✅ Enhanced regex pattern")
                self.fixes_applied.append("enhanced_regex")
                return True
                
        elif fix_type == "add_fallback":
            # Add another fallback parsing method
            # ... implement specific fix
            pass
            
        return False
    
    def diagnose_issue(self, test_result):
        """Diagnose what's wrong based on test results"""
        if test_result.get('success'):
            return None
            
        # Analyze the failure
        if not test_result.get('tools_used'):
            if test_result.get('has_json_block'):
                return "json_parsing_failed"
            else:
                return "no_json_blocks"
                
        if 'json_delimiter_error' in test_result.get('log_errors', []):
            return "triple_quote_issue"
            
        return "unknown_issue"
    
    def run(self):
        """Main autonomous loop"""
        print("🤖 Autonomous Fixer Starting...")
        print("Will test and fix until visualization works\n")
        
        while True:
            # Test current state
            print(f"\n{'='*60}")
            print(f"Test #{self.fix_count + 1}")
            
            result = self.test_visualization()
            
            if result.get('success'):
                print("🎉 SUCCESS! Visualization is working!")
                print(f"Applied fixes: {self.fixes_applied}")
                break
                
            # Diagnose the issue
            issue = self.diagnose_issue(result)
            print(f"❌ Test failed. Diagnosed issue: {issue}")
            
            # Determine what fix to apply
            if issue == "json_parsing_failed" and "enhanced_regex" not in self.fixes_applied:
                self.apply_fix("enhance_parser")
            elif issue == "triple_quote_issue" and "triple_quote_handler" not in self.fixes_applied:
                self.apply_fix("add_triple_quote_handler")
            else:
                print("🤔 No more fixes to try. Last state:")
                print(json.dumps(result, indent=2))
                
                # Could implement more sophisticated fixes here
                # For example, rewrite the entire parser
                
                break
            
            self.fix_count += 1
            
            # Wait for server to restart
            print("⏳ Waiting for server to restart...")
            time.sleep(5)
            
            if self.fix_count > 10:
                print("❌ Too many attempts. Stopping.")
                break

if __name__ == "__main__":
    fixer = AutonomousFixer()
    fixer.run()