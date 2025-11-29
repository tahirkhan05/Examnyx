#!/usr/bin/env python3
"""
OMR Mark Calculator

Workflow:
1. Load detected answers (from AI or manual input)
2. Load answer keys from dataset
3. Calculate marks for each student
4. Compare with manual marks
5. Generate accuracy report

Usage:
    python mark_calculator.py                    # Interactive mode
    python mark_calculator.py dataset.xlsx      # With dataset file
"""

import sys
import json
import pandas as pd
from pathlib import Path

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except: pass

# ============================================
# ANSWER INPUT
# ============================================

def get_detected_answers():
    """
    Get detected answers - either from file or manual input.
    """
    print("\n📝 STUDENT ANSWER INPUT")
    print("-" * 50)
    
    # Check if we have saved detection results
    if Path("detected_answers.json").exists():
        print("Found detected_answers.json from previous detection.")
        use_file = input("Use these answers? (y/n): ").strip().lower()
        
        if use_file == 'y':
            with open("detected_answers.json") as f:
                data = json.load(f)
            return data.get('answers', {})
    
    # Manual input
    print("\nEnter the student's answers for Q1-Q5:")
    print("(Enter A, B, C, or D for each question)")
    
    answers = {}
    for i in range(1, 6):
        while True:
            ans = input(f"  Q{i}: ").strip().upper()
            if ans in ['A', 'B', 'C', 'D', 'X', '']:
                answers[str(i)] = ans if ans else 'X'
                break
            print("    Invalid. Enter A, B, C, D, or X (blank)")
    
    return answers

def input_answers_directly():
    """Quick input of all 5 answers at once."""
    print("\nEnter answers for Q1-Q5 (e.g., 'ABCDA'): ", end="")
    raw = input().strip().upper()
    
    answers = {}
    for i, char in enumerate(raw[:5], 1):
        if char in 'ABCD':
            answers[str(i)] = char
        else:
            answers[str(i)] = 'X'
    
    # Pad if less than 5
    for i in range(len(raw) + 1, 6):
        answers[str(i)] = 'X'
    
    return answers

# ============================================
# MARK CALCULATION
# ============================================

def calculate_marks(student_answers, answer_key):
    """
    Calculate marks based on student answers vs answer key.
    
    Args:
        student_answers: dict {"1": "A", "2": "B", ...}
        answer_key: dict from dataset {"Q1": {"answer": "A", "marks": 20}, ...}
    
    Returns:
        tuple: (total_marks, question_details)
    """
    total = 0
    details = []
    
    for q_key, q_data in answer_key.items():
        q_num = q_key.replace("Q", "")
        correct = q_data["answer"]
        marks = q_data["marks"]
        
        student_ans = student_answers.get(q_num, 'X')
        earned = marks if student_ans == correct else 0
        total += earned
        
        details.append({
            "q": q_key,
            "correct": correct,
            "student": student_ans,
            "marks": earned,
            "max": marks,
            "status": "✅" if earned > 0 else "❌"
        })
    
    return total, details

# ============================================
# DATASET COMPARISON
# ============================================

def run_comparison(dataset_path, student_answers):
    """
    Run comparison against all rows in dataset.
    """
    print("\n" + "=" * 60)
    print("📊 MARK CALCULATION RESULTS")
    print("=" * 60)
    
    # Load dataset
    df = pd.read_excel(dataset_path)
    print(f"\n📂 Loaded {len(df)} test cases")
    
    # Show student answers
    print("\n📝 Student Answers Being Used:")
    for q in sorted(student_answers.keys(), key=lambda x: int(x)):
        print(f"   Q{q}: {student_answers[q]}")
    
    print("\n" + "-" * 60)
    print("COMPARING WITH EACH ANSWER KEY:")
    print("-" * 60)
    print(f"{'Roll':<8} {'Manual':<8} {'Calculated':<12} {'Match':<8} Details")
    print("-" * 60)
    
    results = []
    matches = 0
    
    for _, row in df.iterrows():
        roll = row['Student Roll Number']
        answer_key = json.loads(row['Correct Answers Key'])
        manual_marks = row['Extracted Marks']
        
        # Calculate
        calc_marks, details = calculate_marks(student_answers, answer_key)
        
        # Check match
        is_match = (calc_marks == manual_marks)
        if is_match:
            matches += 1
            match_str = "✅ YES"
        else:
            match_str = "❌ NO"
        
        # Detail string
        detail_str = " ".join([f"Q{d['q'][-1]}:{d['status']}" for d in details])
        
        print(f"{roll:<8} {manual_marks:<8} {calc_marks:<12} {match_str:<8} {detail_str}")
        
        results.append({
            "roll": roll,
            "manual": manual_marks,
            "calculated": calc_marks,
            "match": is_match,
            "details": details
        })
    
    # Summary
    print("\n" + "=" * 60)
    print("📈 SUMMARY")
    print("=" * 60)
    
    accuracy = (matches / len(df)) * 100
    print(f"\n✅ Calculation matched manual: {matches}/{len(df)} ({accuracy:.1f}%)")
    
    # Analyze mismatches
    mismatches = [r for r in results if not r['match']]
    if mismatches:
        print(f"\n⚠️  {len(mismatches)} mismatches found:")
        for r in mismatches[:5]:  # Show first 5
            diff = r['calculated'] - r['manual']
            print(f"   Roll {r['roll']}: Calculated={r['calculated']}, Manual={r['manual']} (diff: {diff:+d})")
    
    # Save results
    output_df = pd.DataFrame([{
        "Roll": r['roll'],
        "Manual": r['manual'],
        "Calculated": r['calculated'],
        "Match": "Yes" if r['match'] else "No"
    } for r in results])
    
    output_df.to_csv("calculation_results.csv", index=False)
    print(f"\n💾 Results saved to: calculation_results.csv")
    
    return results, accuracy

# ============================================
# INTERACTIVE MODE
# ============================================

def interactive_mode():
    """
    Interactive mark calculation.
    """
    print("\n" + "=" * 60)
    print("🧮 OMR MARK CALCULATOR")
    print("=" * 60)
    print("Calculate marks and compare with manual evaluation")
    print("=" * 60)
    
    # Get dataset
    if len(sys.argv) >= 2:
        dataset_path = sys.argv[1]
    else:
        print("\n📂 Select dataset file...")
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            dataset_path = filedialog.askopenfilename(
                title="Select Excel Dataset",
                filetypes=[("Excel", "*.xlsx"), ("All", "*.*")]
            )
            root.destroy()
        except:
            dataset_path = input("Enter dataset path: ").strip()
    
    if not dataset_path or not Path(dataset_path).exists():
        print("❌ No valid dataset file")
        return
    
    # Get answer input method
    print("\n📝 How to input student answers?")
    print("  1. Enter answers manually (e.g., ABCDA)")
    print("  2. Use detected_answers.json (if exists)")
    print("  3. Run AI detection on OMR image")
    
    choice = input("\nChoice (1/2/3): ").strip()
    
    if choice == '1':
        student_answers = input_answers_directly()
    elif choice == '2':
        if Path("detected_answers.json").exists():
            with open("detected_answers.json") as f:
                data = json.load(f)
            student_answers = data.get('answers', {})
        else:
            print("No detected_answers.json found. Using manual input.")
            student_answers = input_answers_directly()
    elif choice == '3':
        print("\nRunning AI detection...")
        import detect_omr
        student_answers = detect_omr.main()
        if not student_answers:
            print("Detection failed. Using manual input.")
            student_answers = input_answers_directly()
    else:
        student_answers = input_answers_directly()
    
    # Run comparison
    run_comparison(dataset_path, student_answers)
    
    print("\n" + "=" * 60 + "\n")

# ============================================
# QUICK TEST
# ============================================

def quick_test():
    """
    Quick test with known values.
    """
    print("\n🧪 QUICK TEST MODE")
    print("-" * 40)
    
    # Based on the OMR image, the actual student answers appear to be:
    # Q1: A, Q2: B, Q3: C, Q4: D, Q5: A
    student_answers = {"1": "A", "2": "B", "3": "C", "4": "D", "5": "A"}
    
    print("Testing with answers: Q1:A, Q2:B, Q3:C, Q4:D, Q5:A")
    
    # Sample answer key (Roll 101)
    answer_key = {
        "Q1": {"answer": "A", "marks": 20},
        "Q2": {"answer": "B", "marks": 20},
        "Q3": {"answer": "C", "marks": 20},
        "Q4": {"answer": "D", "marks": 20},
        "Q5": {"answer": "B", "marks": 20}  # Note: B, not A
    }
    
    total, details = calculate_marks(student_answers, answer_key)
    
    print(f"\nAnswer Key: Q1:A, Q2:B, Q3:C, Q4:D, Q5:B")
    print("-" * 40)
    
    for d in details:
        print(f"{d['q']}: Student={d['student']}, Correct={d['correct']} → {d['marks']}/{d['max']} {d['status']}")
    
    print("-" * 40)
    print(f"TOTAL: {total}/100")
    
    return total

# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    if "--test" in sys.argv:
        quick_test()
    else:
        interactive_mode()

