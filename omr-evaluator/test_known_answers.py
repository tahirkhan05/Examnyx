#!/usr/bin/env python3
"""Test with known student answers."""
import sys
if sys.platform == 'win32':
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

import pandas as pd
import json

DATASET = r"C:\Users\DrRay\Downloads\PS1E.xlsx"

# Try different possible student answers
test_cases = [
    {"name": "A,B,C,D,A", "answers": {"1":"A","2":"B","3":"C","4":"D","5":"A"}},
    {"name": "A,B,C,D,B", "answers": {"1":"A","2":"B","3":"C","4":"D","5":"B"}},
    {"name": "A,B,C,D,C", "answers": {"1":"A","2":"B","3":"C","4":"D","5":"C"}},
    {"name": "A,B,C,D,D", "answers": {"1":"A","2":"B","3":"C","4":"D","5":"D"}},
]

df = pd.read_excel(DATASET)

print("=" * 70)
print("TESTING DIFFERENT POSSIBLE STUDENT ANSWERS")
print("=" * 70)
print("Finding which answer set matches the manual marks best...\n")

best_matches = 0
best_case = None

for tc in test_cases:
    student = tc["answers"]
    matches = 0
    
    for _, r in df.iterrows():
        key = json.loads(r['Correct Answers Key'])
        manual = r['Extracted Marks']
        
        calc = 0
        for q, k in key.items():
            q_num = q.replace("Q", "")
            if student.get(q_num) == k["answer"]:
                calc += k["marks"]
        
        if calc == manual:
            matches += 1
    
    accuracy = matches / len(df) * 100
    print(f"  {tc['name']}: {matches}/20 matches ({accuracy:.0f}%)")
    
    if matches > best_matches:
        best_matches = matches
        best_case = tc

print("\n" + "=" * 70)
print(f"BEST MATCH: {best_case['name']} with {best_matches}/20 ({best_matches/20*100:.0f}%)")
print("=" * 70)

# Now show detailed results for best case
print(f"\nDetailed results for {best_case['name']}:")
print("-" * 70)
print(f"{'Roll':<8} {'Manual':<10} {'Calculated':<12} {'Match'}")
print("-" * 70)

student = best_case["answers"]
for _, r in df.iterrows():
    roll = r['Student Roll Number']
    key = json.loads(r['Correct Answers Key'])
    manual = r['Extracted Marks']
    
    calc = 0
    for q, k in key.items():
        q_num = q.replace("Q", "")
        if student.get(q_num) == k["answer"]:
            calc += k["marks"]
    
    match = "✅" if calc == manual else "❌"
    print(f"{roll:<8} {manual:<10} {calc:<12} {match}")

print("-" * 70)

