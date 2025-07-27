#!/bin/bash
cd /Users/marcschwyn/Desktop/projects/KROMV12
echo "Starting NLP analysis at $(date)"
echo "This will analyze 4,543 crypto calls and take 15-20 minutes..."
echo "Progress will be saved to nlp_analysis_progress.json"
echo "Final results will be in full_nlp_analysis_results.json"
echo ""
python3 full-nlp-analysis.py