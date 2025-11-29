#!/usr/bin/env python3
"""
Analyze the dataset to understand the expected answers.
Reverse-engineer what student answers would produce the manual marks.
"""
import sys
if sys.platform == 'win32':
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

import pandas as pd
import json
from itertools import product

DATASET = r"C:\Users\DrRay\Downloads\PS1E.xlsx"

def find_answers_for_marks(answer_key, target_marks):
    """
    Find what student answers would give the target marks.
    Returns list of possible answer combinations.
    """
    questions = sorted(answer_key.keys())
    options = ['A', 'B', 'C', 'D']
    
    valid_combos = []
    
    # Try all possible answer combinations (4^5 = 1024)
    for combo in product(options, repeat=len(questions)):
        answers = {q.replace('Q',''): a for q, a in zip(questions, combo)}
        
        # Calculate marks
        marks = 0
        for q, k in answer_key.items():
            q_num = q.replace('Q', '')
            if answers.get(q_num) == k['answer']:
                marks += k['marks']
        
        if marks == target_marks:
            valid_combos.append(''.join(combo))
    
    return valid_combos

# Load dataset
df = pd.read_excel(DATASET)

print("=" * 70)
print("DATASET ANALYSIS")
print("=" * 70)
print("Finding what student answers would produce the manual marks...\n")

print(f"{'Roll':<8} {'Manual':<8} {'Answer Key':<20} {'Possible Student Answers'}")
print("-" * 70)

all_possible = {}

for idx, row in df.iterrows():
    roll = row['Student Roll Number']
    manual = row['Extracted Marks']
    key = json.loads(row['Correct Answers Key'])
    
    # Get correct answers from key
    correct = ''.join([key[f'Q{i}']['answer'] for i in range(1, 6)])
    
    # Find what student answers would give manual marks
    possible = find_answers_for_marks(key, manual)
    
    all_possible[roll] = possible
    
    # Show first few
    if len(possible) <= 3:
        possible_str = ', '.join(possible)
    else:
        possible_str = f"{possible[0]}, {possible[1]}, ... ({len(possible)} options)"
    
    print(f"{roll:<8} {manual:<8} {correct:<20} {possible_str}")

print("-" * 70)

# Check if there's a common pattern
print("\n" + "=" * 70)
print("LOOKING FOR PATTERNS")
print("=" * 70)

# Check first row (Roll 101, 100 marks)
row101 = df.iloc[0]
key101 = json.loads(row101['Correct Answers Key'])
correct101 = ''.join([key101[f'Q{i}']['answer'] for i in range(1, 6)])

print(f"\nRoll 101: Manual=100, Answer Key={correct101}")
print("For 100 marks, student must have answered ALL correctly.")
print(f"So Roll 101's student answers = {correct101}")

# This means each row might have DIFFERENT student answers
print("\n" + "=" * 70)
print("CONCLUSION")
print("=" * 70)
print("""
This dataset represents 20 DIFFERENT students:
- Each student has different answers on their sheet
- Each row has a different answer key
- The 'Extracted Marks' is what they got

The single OMR image URL is just a SAMPLE/PLACEHOLDER.
For real evaluation, you'd need 20 different OMR images.

For THIS dataset to work, the system needs to:
1. Have the student's answers as INPUT (not from image)
2. Compare with the answer key
3. Calculate marks

The image detection part is NOT testable with this synthetic dataset.
""")

