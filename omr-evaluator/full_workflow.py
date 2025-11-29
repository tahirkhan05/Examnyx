#!/usr/bin/env python3
"""
Complete OMR Evaluation Workflow

1. Detect answers from OMR image
2. Calculate marks against answer keys
3. Compare with manual evaluation
4. Generate accuracy report

Usage: python full_workflow.py
"""

import sys
import json
import pandas as pd
from pathlib import Path

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except: pass

# Import our modules
from detect_omr import detect_answers, get_groq_token, image_to_base64

# ============================================
# CONFIGURATION
# ============================================

# Default paths - change these to your files
DEFAULT_DATASET = r"C:\Users\DrRay\Downloads\PS1E.xlsx"
DEFAULT_OMR_IMAGE = r"C:\Users\DrRay\Downloads\omr sheet.jpeg"

# ============================================
# FILE PICKER
# ============================================

def pick_file(title, filetypes):
    """Open file picker dialog."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        path = filedialog.askopenfilename(title=title, filetypes=filetypes)
        root.destroy()
        return path
    except:
        return None

# ============================================
# MARK CALCULATION  
# ============================================

def calculate_marks(student_answers, answer_key_json):
    """Calculate marks from student answers vs answer key."""
    answer_key = json.loads(answer_key_json) if isinstance(answer_key_json, str) else answer_key_json
    
    total = 0
    for q_key, q_data in answer_key.items():
        q_num = q_key.replace("Q", "")
        correct = q_data["answer"]
        marks = q_data["marks"]
        
        student_ans = student_answers.get(q_num, 'X')
        if student_ans == correct:
            total += marks
    
    return total

# ============================================
# MAIN WORKFLOW
# ============================================

def main():
    print("\n" + "=" * 70)
    print("🎯 COMPLETE OMR EVALUATION WORKFLOW")
    print("=" * 70)
    print("Step 1: Detect answers from OMR image")
    print("Step 2: Calculate marks for all answer keys")
    print("Step 3: Compare with manual evaluation")
    print("=" * 70)
    
    # ============================================
    # STEP 1: GET OMR IMAGE
    # ============================================
    print("\n📷 STEP 1: SELECT OMR IMAGE")
    print("-" * 50)
    
    # Try default path first
    omr_path = DEFAULT_OMR_IMAGE
    
    if not Path(omr_path).exists():
        print("Default OMR image not found. Please select...")
        omr_path = pick_file("Select OMR Sheet Image", [("Images", "*.jpg *.jpeg *.png")])
    
    if not omr_path or not Path(omr_path).exists():
        print("❌ No OMR image. Exiting.")
        return
    
    print(f"✅ Using: {omr_path}")
    
    # ============================================
    # STEP 2: GET DATASET
    # ============================================
    print("\n📊 STEP 2: SELECT DATASET")
    print("-" * 50)
    
    dataset_path = DEFAULT_DATASET
    
    if not Path(dataset_path).exists():
        print("Default dataset not found. Please select...")
        dataset_path = pick_file("Select Excel Dataset", [("Excel", "*.xlsx")])
    
    if not dataset_path or not Path(dataset_path).exists():
        print("❌ No dataset. Exiting.")
        return
    
    print(f"✅ Using: {dataset_path}")
    
    # Load dataset
    df = pd.read_excel(dataset_path)
    print(f"   Found {len(df)} test cases with {len(json.loads(df['Correct Answers Key'].iloc[0]))} questions each")
    
    # ============================================
    # STEP 3: DETECT ANSWERS FROM OMR
    # ============================================
    print("\n🤖 STEP 3: AI DETECTION")
    print("-" * 50)
    
    api_key = get_groq_token()
    result = detect_answers(omr_path, api_key)
    
    if not result:
        print("❌ Detection failed. Please enter answers manually.")
        print("Enter answers for Q1-Q5 (e.g., ABCDA): ", end="")
        raw = input().strip().upper()
        student_answers = {}
        for i, c in enumerate(raw[:5], 1):
            student_answers[str(i)] = c if c in 'ABCD' else 'X'
    else:
        student_answers = result.get('answers', {})
    
    # Show detected answers
    print("\n📝 DETECTED STUDENT ANSWERS:")
    num_questions = len(json.loads(df['Correct Answers Key'].iloc[0]))
    for i in range(1, num_questions + 1):
        ans = student_answers.get(str(i), '?')
        print(f"   Q{i}: {ans}")
    
    # ============================================
    # STEP 4: CALCULATE & COMPARE
    # ============================================
    print("\n📊 STEP 4: CALCULATION & COMPARISON")
    print("-" * 50)
    print(f"{'Roll':<8} {'Manual':<10} {'AI Calc':<10} {'Original':<10} {'Match'}")
    print("-" * 50)
    
    ai_matches_manual = 0
    orig_matches_manual = 0
    
    for _, row in df.iterrows():
        roll = row['Student Roll Number']
        manual = row['Extracted Marks']
        original_auto = row['Auto Calculated Marks']
        
        # Calculate using our detected answers
        our_marks = calculate_marks(student_answers, row['Correct Answers Key'])
        
        # Check matches
        ai_match = our_marks == manual
        orig_match = row['Marks Matched'] == 'Yes'
        
        if ai_match:
            ai_matches_manual += 1
            match_str = "✅"
        else:
            match_str = "❌"
        
        print(f"{roll:<8} {manual:<10} {our_marks:<10} {original_auto:<10} {match_str}")
    
    # ============================================
    # STEP 5: SUMMARY
    # ============================================
    print("\n" + "=" * 70)
    print("📈 FINAL RESULTS")
    print("=" * 70)
    
    total = len(df)
    ai_accuracy = (ai_matches_manual / total) * 100
    orig_matches_manual = sum(1 for _, r in df.iterrows() if r['Marks Matched'] == 'Yes')
    orig_accuracy = (orig_matches_manual / total) * 100
    
    print(f"\n🤖 Our AI System:")
    print(f"   Matches manual: {ai_matches_manual}/{total} ({ai_accuracy:.1f}%)")
    
    print(f"\n📊 Original Auto System:")
    print(f"   Matches manual: {orig_matches_manual}/{total} ({orig_accuracy:.1f}%)")
    
    diff = ai_accuracy - orig_accuracy
    if diff > 0:
        print(f"\n🎉 Our system is {diff:.1f}% MORE ACCURATE!")
    elif diff < 0:
        print(f"\n⚠️  Our system is {abs(diff):.1f}% less accurate")
        print("   This may be because the OMR image doesn't match the dataset's expected answers.")
    else:
        print(f"\n📊 Same accuracy as original system")
    
    # ============================================
    # STEP 6: SAVE RESULTS
    # ============================================
    results = []
    for _, row in df.iterrows():
        our_marks = calculate_marks(student_answers, row['Correct Answers Key'])
        results.append({
            "Roll": row['Student Roll Number'],
            "Manual": row['Extracted Marks'],
            "AI_Calculated": our_marks,
            "Original_Auto": row['Auto Calculated Marks'],
            "AI_Match": "Yes" if our_marks == row['Extracted Marks'] else "No",
            "Original_Match": row['Marks Matched']
        })
    
    results_df = pd.DataFrame(results)
    results_df.to_csv("final_results.csv", index=False)
    print(f"\n💾 Results saved to: final_results.csv")
    
    # Save detected answers
    with open("student_answers.json", "w") as f:
        json.dump({"answers": student_answers}, f, indent=2)
    print(f"💾 Answers saved to: student_answers.json")
    
    print("\n" + "=" * 70 + "\n")

# ============================================
# RUN
# ============================================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

