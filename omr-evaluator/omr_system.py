#!/usr/bin/env python3
"""
🎯 COMPLETE OMR EVALUATION SYSTEM

This system handles:
1. OMR image detection (using AI)
2. Mark calculation (student answers vs answer key)
3. Batch processing (multiple students)
4. Accuracy reporting

For REAL usage:
    python omr_system.py --image student001.jpg --key answer_key.json

For TESTING with synthetic dataset:
    python omr_system.py --test-dataset dataset.xlsx
"""

import sys
import json
import argparse
import pandas as pd
from pathlib import Path

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except: pass

# ============================================
# MARK CALCULATION ENGINE
# ============================================

class MarkCalculator:
    """Calculate marks from student answers vs answer key."""
    
    def __init__(self, answer_key):
        """
        Args:
            answer_key: dict like {"Q1": {"answer": "A", "marks": 20}, ...}
                       OR string like "ABCDB"
        """
        if isinstance(answer_key, str):
            # Convert simple string format to full format
            self.answer_key = {
                f"Q{i+1}": {"answer": ans, "marks": 20}
                for i, ans in enumerate(answer_key)
            }
        elif isinstance(answer_key, dict) and 'Q1' in answer_key:
            self.answer_key = answer_key
        else:
            # Try to parse JSON string
            self.answer_key = json.loads(answer_key) if isinstance(answer_key, str) else answer_key
    
    def calculate(self, student_answers):
        """
        Calculate marks.
        
        Args:
            student_answers: dict {"1": "A", "2": "B"} or string "ABCDB"
        
        Returns:
            tuple: (total_marks, details)
        """
        if isinstance(student_answers, str):
            student_answers = {str(i+1): ans for i, ans in enumerate(student_answers)}
        
        total = 0
        details = []
        
        for q_key, q_data in self.answer_key.items():
            q_num = q_key.replace("Q", "")
            correct = q_data["answer"]
            max_marks = q_data["marks"]
            
            student_ans = student_answers.get(q_num, student_answers.get(q_key, "X"))
            earned = max_marks if student_ans == correct else 0
            total += earned
            
            details.append({
                "question": q_key,
                "correct_answer": correct,
                "student_answer": student_ans,
                "marks_earned": earned,
                "marks_possible": max_marks,
                "is_correct": earned > 0
            })
        
        return total, details

# ============================================
# DATASET TESTING
# ============================================

def test_with_dataset(dataset_path):
    """
    Test mark calculation with synthetic dataset.
    For rows with 100 marks, we know student answered perfectly.
    """
    print("\n" + "=" * 70)
    print("🧪 TESTING MARK CALCULATION WITH DATASET")
    print("=" * 70)
    
    df = pd.read_excel(dataset_path)
    print(f"\n📊 Loaded {len(df)} test cases")
    
    print("\n" + "-" * 70)
    print("Testing calculation logic...")
    print("-" * 70)
    
    passed = 0
    failed = 0
    
    for idx, row in df.iterrows():
        roll = row['Student Roll Number']
        answer_key = json.loads(row['Correct Answers Key'])
        manual_marks = row['Extracted Marks']
        
        # For perfect scores (100), student answered all correctly
        if manual_marks == 100:
            student_answers = ''.join([answer_key[f'Q{i}']['answer'] for i in range(1, 6)])
            calc = MarkCalculator(answer_key)
            total, _ = calc.calculate(student_answers)
            
            if total == manual_marks:
                passed += 1
                status = "✅ PASS"
            else:
                failed += 1
                status = "❌ FAIL"
            
            print(f"Roll {roll}: Key={student_answers}, Manual={manual_marks}, Calc={total} {status}")
    
    print("\n" + "-" * 70)
    print(f"Perfect score tests: {passed} passed, {failed} failed")
    print("-" * 70)
    
    # Now test the full calculation logic
    print("\n" + "-" * 70)
    print("Testing with synthetic student answers...")
    print("-" * 70)
    
    # For each row, derive what student answers would give the manual marks
    all_passed = True
    
    for idx, row in df.iterrows():
        roll = row['Student Roll Number']
        answer_key = json.loads(row['Correct Answers Key'])
        manual_marks = row['Extracted Marks']
        
        # For 100 marks: student = answer key
        if manual_marks == 100:
            student = ''.join([answer_key[f'Q{i}']['answer'] for i in range(1, 6)])
        elif manual_marks in [95, 90, 85]:
            # 4 correct = 80 marks, but we need 95/90/85
            # This dataset uses 20 marks per question, so 95/90/85 are impossible!
            # 5*20=100, 4*20=80, 3*20=60, 2*20=40, 1*20=20, 0*20=0
            # So 95, 90, 85 are NOT possible with 20 marks each!
            continue  # Skip impossible marks
        elif manual_marks == 80:
            # 4 correct out of 5
            # Get one wrong
            correct = [answer_key[f'Q{i}']['answer'] for i in range(1, 6)]
            wrong_q = 4  # Miss Q5
            student_list = correct.copy()
            # Change one answer to wrong
            wrong_options = [x for x in 'ABCD' if x != correct[wrong_q]]
            student_list[wrong_q] = wrong_options[0]
            student = ''.join(student_list)
        else:
            continue
        
        calc = MarkCalculator(answer_key)
        total, _ = calc.calculate(student)
        
        if total != manual_marks:
            all_passed = False
            print(f"❌ Roll {roll}: Expected {manual_marks}, got {total}")
    
    if all_passed:
        print("✅ All valid test cases passed!")
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 DATASET ANALYSIS")
    print("=" * 70)
    
    marks_dist = df['Extracted Marks'].value_counts().sort_index()
    print("\nMarks distribution in dataset:")
    for marks, count in marks_dist.items():
        possible = marks % 20 == 0
        status = "✅ valid" if possible else "⚠️ impossible (not divisible by 20)"
        print(f"  {marks} marks: {count} students {status}")
    
    impossible = [m for m in df['Extracted Marks'] if m % 20 != 0]
    if impossible:
        print(f"\n⚠️  Note: {len(set(impossible))} mark values ({set(impossible)}) are impossible")
        print("   with 20 marks per question (only 0,20,40,60,80,100 are possible)")

# ============================================
# SINGLE EVALUATION
# ============================================

def evaluate_single(image_path, answer_key):
    """
    Evaluate a single OMR sheet.
    
    Args:
        image_path: Path to OMR image
        answer_key: Answer key (string like "ABCDB" or JSON)
    """
    from detect_omr import detect_answers, get_groq_token
    
    print("\n" + "=" * 70)
    print("🎯 SINGLE OMR EVALUATION")
    print("=" * 70)
    
    # Detect answers
    api_key = get_groq_token()
    result = detect_answers(image_path, api_key)
    
    if not result:
        print("❌ Detection failed")
        return None
    
    student_answers = result.get('answers', {})
    
    # Calculate marks
    calc = MarkCalculator(answer_key)
    total, details = calc.calculate(student_answers)
    
    # Display results
    print("\n" + "-" * 70)
    print("RESULTS")
    print("-" * 70)
    
    for d in details:
        status = "✅" if d['is_correct'] else "❌"
        print(f"{d['question']}: Student={d['student_answer']}, "
              f"Correct={d['correct_answer']} → {d['marks_earned']}/{d['marks_possible']} {status}")
    
    print("-" * 70)
    print(f"TOTAL: {total}/{sum(d['marks_possible'] for d in details)}")
    
    return total, details

# ============================================
# MAIN
# ============================================

def main():
    parser = argparse.ArgumentParser(description="OMR Evaluation System")
    parser.add_argument('--test-dataset', help='Test with Excel dataset')
    parser.add_argument('--image', help='OMR image to evaluate')
    parser.add_argument('--key', help='Answer key (ABCDB format or JSON file)')
    args = parser.parse_args()
    
    print("\n" + "=" * 70)
    print("🎯 OMR EVALUATION SYSTEM")
    print("=" * 70)
    
    if args.test_dataset:
        test_with_dataset(args.test_dataset)
    elif args.image and args.key:
        evaluate_single(args.image, args.key)
    else:
        # Interactive mode
        print("\nUsage:")
        print("  Test dataset:     python omr_system.py --test-dataset data.xlsx")
        print("  Single evaluate:  python omr_system.py --image sheet.jpg --key ABCDB")
        print("\nRunning interactive test with default dataset...")
        
        default_dataset = r"C:\Users\DrRay\Downloads\PS1E.xlsx"
        if Path(default_dataset).exists():
            test_with_dataset(default_dataset)
        else:
            print("Default dataset not found. Please provide arguments.")

if __name__ == "__main__":
    main()

