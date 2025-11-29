#!/usr/bin/env python3
"""
OMR Calibration & Accuracy Testing

This script:
1. Downloads the OMR image from the dataset
2. Detects student answers using AI
3. Compares against each answer key in the dataset
4. Calculates marks and compares with manual evaluation
5. Reports accuracy metrics

Usage: python calibrate.py <path_to_excel_dataset>
"""

import os
import sys
import json
import requests
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Auto-install dependencies
def auto_install():
    required = {'pandas': 'pandas', 'openpyxl': 'openpyxl', 'PIL': 'pillow', 'requests': 'requests'}
    import subprocess
    for imp, pkg in required.items():
        try:
            __import__(imp)
        except ImportError:
            print(f"Installing {pkg}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--quiet', pkg])

auto_install()

import pandas as pd
from omr_evaluator import OMREvaluator, open_file_picker

# ============================================
# IMAGE HANDLING
# ============================================

def download_image(url, save_path="temp_omr.jpg"):
    """Download OMR image from URL."""
    print(f"📥 Downloading OMR image...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ Image saved to: {save_path}")
        return save_path
    except Exception as e:
        print(f"❌ Failed to download: {e}")
        return None

# ============================================
# SCORING ENGINE
# ============================================

def calculate_marks(detected_answers, answer_key):
    """
    Calculate marks based on detected answers vs answer key.
    
    Args:
        detected_answers: dict {"1": "A", "2": "B", ...}
        answer_key: dict {"Q1": {"answer": "A", "marks": 20}, ...}
    
    Returns:
        tuple: (total_marks, details)
    """
    total_marks = 0
    details = []
    
    for q_key, q_data in answer_key.items():
        q_num = q_key.replace("Q", "")  # "Q1" -> "1"
        correct_answer = q_data["answer"]
        marks = q_data["marks"]
        
        # Get detected answer (try both "1" and "Q1" formats)
        detected = detected_answers.get(q_num) or detected_answers.get(q_key) or "?"
        
        if detected == correct_answer:
            total_marks += marks
            status = "✅"
        else:
            status = "❌"
        
        details.append({
            "question": q_key,
            "correct": correct_answer,
            "detected": detected,
            "marks_possible": marks,
            "marks_earned": marks if detected == correct_answer else 0,
            "status": status
        })
    
    return total_marks, details

# ============================================
# MAIN CALIBRATION
# ============================================

def run_calibration(excel_path):
    """
    Run full calibration against the dataset.
    """
    print("\n" + "="*70)
    print("🔬 OMR CALIBRATION & ACCURACY TEST")
    print("="*70 + "\n")
    
    # Load dataset
    print(f"📊 Loading dataset: {excel_path}")
    df = pd.read_excel(excel_path)
    print(f"   Found {len(df)} test cases\n")
    
    # Get the OMR image (use first URL)
    image_url = df['Original Answer Sheet Image'].iloc[0]
    print(f"📷 OMR Image URL: {image_url[:60]}...")
    
    # Ask user to select the actual OMR image
    # (URLs in dataset are often document previews, not actual OMR sheets)
    print("\n⚠️  Dataset URLs often contain document previews, not OMR sheets.")
    print("📂 Please select the ACTUAL OMR bubble sheet image...")
    
    image_path = open_file_picker()
    
    if not image_path:
        # Try downloading as fallback
        print("No file selected, trying to download from URL...")
        image_path = download_image(image_url)
        
    if not image_path or not Path(image_path).exists():
        print("❌ No valid image. Exiting.")
        return
    
    # Initialize evaluator and detect answers
    print("\n" + "-"*70)
    print("🤖 DETECTING STUDENT ANSWERS FROM OMR")
    print("-"*70 + "\n")
    
    evaluator = OMREvaluator()
    result = evaluator.evaluate(image_path)
    
    # Extract detected answers (flatten the structure)
    detected_answers = {}
    for q_num, data in result.get('answers', {}).items():
        if isinstance(data, dict):
            detected_answers[q_num] = data.get('answer', '?')
        else:
            detected_answers[q_num] = data
    
    print("\n📝 Detected Student Answers:")
    for q, a in sorted(detected_answers.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0):
        print(f"   Q{q}: {a}")
    
    # Now compare against each test case
    print("\n" + "-"*70)
    print("📊 COMPARING AGAINST ALL TEST CASES")
    print("-"*70 + "\n")
    
    results = []
    matches = 0
    
    for idx, row in df.iterrows():
        roll_no = row['Student Roll Number']
        answer_key = json.loads(row['Correct Answers Key'])
        manual_marks = row['Extracted Marks']
        auto_marks_original = row['Auto Calculated Marks']
        marks_matched = row['Marks Matched']
        
        # Calculate our marks
        our_marks, details = calculate_marks(detected_answers, answer_key)
        
        # Compare
        matches_manual = (our_marks == manual_marks)
        if matches_manual:
            matches += 1
            match_icon = "✅"
        else:
            match_icon = "❌"
        
        results.append({
            "roll": roll_no,
            "manual": manual_marks,
            "original_auto": auto_marks_original,
            "our_marks": our_marks,
            "matches_manual": matches_manual,
            "original_matched": marks_matched
        })
        
        print(f"Roll {roll_no}: Manual={manual_marks}, Our AI={our_marks}, Original Auto={auto_marks_original} {match_icon}")
    
    # Summary
    print("\n" + "="*70)
    print("📈 CALIBRATION RESULTS SUMMARY")
    print("="*70)
    
    accuracy = (matches / len(df)) * 100
    
    print(f"\n✅ Our AI matched manual scoring: {matches}/{len(df)} ({accuracy:.1f}%)")
    
    # Compare with original auto system
    original_matches = sum(1 for r in results if r['original_matched'] == 'Yes')
    original_accuracy = (original_matches / len(df)) * 100
    print(f"📊 Original auto matched manual:  {original_matches}/{len(df)} ({original_accuracy:.1f}%)")
    
    improvement = accuracy - original_accuracy
    if improvement > 0:
        print(f"\n🎉 Our system is {improvement:.1f}% MORE accurate!")
    elif improvement < 0:
        print(f"\n⚠️  Our system is {abs(improvement):.1f}% less accurate. Needs tuning.")
    else:
        print(f"\n📊 Same accuracy as original system.")
    
    # Show mismatches for analysis
    mismatches = [r for r in results if not r['matches_manual']]
    if mismatches:
        print(f"\n" + "-"*70)
        print(f"🔍 MISMATCHES TO ANALYZE ({len(mismatches)} cases):")
        print("-"*70)
        for r in mismatches:
            diff = r['our_marks'] - r['manual']
            print(f"   Roll {r['roll']}: Our={r['our_marks']}, Manual={r['manual']} (diff: {diff:+d})")
    
    # Save detailed results
    results_df = pd.DataFrame(results)
    results_path = "calibration_results.csv"
    results_df.to_csv(results_path, index=False)
    print(f"\n💾 Detailed results saved to: {results_path}")
    
    print("\n" + "="*70 + "\n")
    
    return results, detected_answers

# ============================================
# ENTRY POINT
# ============================================

def main():
    print("\n" + "="*70)
    print("🔬 OMR CALIBRATION TOOL")
    print("="*70)
    print("Compare AI detection against manual evaluation")
    print("="*70 + "\n")
    
    # Get dataset path
    if len(sys.argv) >= 2:
        excel_path = sys.argv[1]
    else:
        print("📂 Please select the Excel dataset file...")
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            excel_path = filedialog.askopenfilename(
                title="Select Dataset Excel File",
                filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
            )
            root.destroy()
        except Exception:
            excel_path = input("Enter path to Excel dataset: ").strip()
    
    if not excel_path:
        print("❌ No file selected.")
        sys.exit(1)
    
    if not Path(excel_path).exists():
        print(f"❌ File not found: {excel_path}")
        sys.exit(1)
    
    try:
        run_calibration(excel_path)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

