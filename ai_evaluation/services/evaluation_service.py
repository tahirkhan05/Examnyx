"""
Core evaluation services using AWS Bedrock
Contains all business logic for solving, verifying, and objection handling
"""

import json
import re
from typing import Dict, Any
from bedrock_client import bedrock_client
from models.schemas import (
    QuestionSolveResponse, 
    AnswerVerificationResponse, 
    StudentObjectionResponse,
    MatchStatus
)


def solve_question(
    question_text: str, 
    subject: str, 
    difficulty_level: str
) -> QuestionSolveResponse:
    """
    Solve a question using AWS Bedrock
    
    Args:
        question_text: The question to solve
        subject: Subject area
        difficulty_level: Difficulty (easy/medium/hard)
        
    Returns:
        QuestionSolveResponse with solution and explanation
    """
    
    system_prompt = f"""You are an expert {subject} teacher and problem solver.
Solve problems with scientific accuracy and logical reasoning.
Provide clear, step-by-step explanations suitable for {difficulty_level} level students."""

    prompt = f"""Question: {question_text}

Provide your answer in valid JSON format with these exact fields:
- ai_solution: your final answer (concise)
- explanation: step-by-step reasoning (clear but concise)
- confidence: score from 0 to 1

Respond ONLY with valid JSON, no other text:
{{
    "ai_solution": "your answer",
    "explanation": "your explanation",
    "confidence": 0.95
}}"""

    try:
        response = bedrock_client.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,  # Lower temperature for accuracy
            max_tokens=4096  # Increased for complete responses
        )
        
        # Parse JSON response
        result = _extract_json(response)
        
        return QuestionSolveResponse(**result)
    except Exception as e:
        # Fallback: return error details for debugging
        raise ValueError(f"Failed to solve question. Error: {str(e)}. Response: {response[:500] if 'response' in locals() else 'No response'}")


def verify_with_key(
    question_text: str,
    ai_solution: str, 
    official_key: str,
    subject: str = None
) -> AnswerVerificationResponse:
    """
    Verify AI's answer against official answer key
    
    Args:
        question_text: Original question
        ai_solution: AI's generated answer
        official_key: Official answer key
        subject: Optional subject for context
        
    Returns:
        AnswerVerificationResponse with match status and analysis
    """
    
    system_prompt = """You are an expert evaluator comparing answers for correctness.
You must:
- Determine if answers are equivalent (accounting for different notations)
- Identify if alternative valid solutions exist
- Detect incorrect or ambiguous answer keys
- Flag cases requiring human review"""

    subject_context = f"Subject: {subject}\n" if subject else ""
    
    prompt = f"""{subject_context}Question: {question_text}
AI Answer: {ai_solution}
Official Key: {official_key}

Compare these answers. Respond ONLY with valid JSON:
{{
    "ai_solution": "{ai_solution}",
    "official_key": "{official_key}",
    "match_status": "match",
    "confidence": 0.95,
    "reasoning": "brief comparison (2-3 sentences)",
    "flag_for_human": false
}}

match_status options: "match", "mismatch", "alternative_valid", "wrong_key"
Flag if key appears incorrect or multiple valid answers exist."""

    response = bedrock_client.generate(
        prompt=prompt,
        system_prompt=system_prompt,
        temperature=0.2,
        max_tokens=2048
    )
    
    result = _extract_json(response)
    
    return AnswerVerificationResponse(**result)


def evaluate_student_objection(
    question_text: str,
    student_answer: str,
    student_proof: str,
    official_key: str,
    ai_solution: str = None,
    subject: str = None
) -> StudentObjectionResponse:
    """
    Evaluate a student's objection with scientific reasoning
    
    Args:
        question_text: Original question
        student_answer: Student's submitted answer
        student_proof: Student's justification/proof
        official_key: Official answer key
        ai_solution: Optional AI solution for reference
        subject: Optional subject area
        
    Returns:
        StudentObjectionResponse with validity assessment
    """
    
    system_prompt = """You are an expert academic evaluator handling student objections.
You must:
- Rigorously verify scientific/logical accuracy of student's reasoning
- Cross-check with established facts and principles
- Identify genuine errors in answer keys
- Detect ambiguous questions
- Be fair but maintain academic standards
- Flag controversial cases for human review"""

    subject_context = f"Subject: {subject}\n" if subject else ""
    ai_context = f"AI's Solution: {ai_solution}\n" if ai_solution else ""
    
    prompt = f"""{subject_context}Question: {question_text}
Official Key: {official_key}
{ai_context}
Student's Answer: {student_answer}
Student's Proof: {student_proof}

Evaluate if student's reasoning is scientifically valid. Respond ONLY with valid JSON:
{{
    "student_valid": true,
    "reason": "brief analysis (2-3 sentences)",
    "alternative_valid": false,
    "question_ambiguous": false,
    "key_incorrect": false,
    "flag_for_human_review": true,
    "final_recommendation": "brief recommendation",
    "confidence": 0.95
}}"""

    response = bedrock_client.generate(
        prompt=prompt,
        system_prompt=system_prompt,
        temperature=0.2,
        max_tokens=4096  # Increased for complete responses
    )
    
    result = _extract_json(response)
    
    return StudentObjectionResponse(**result)


def flag_for_human_if_needed(result: Dict[str, Any]) -> bool:
    """
    Determine if human intervention is required
    
    Args:
        result: Dictionary containing evaluation results
        
    Returns:
        True if human review needed
    """
    
    # Check various conditions that require human review
    conditions = [
        result.get("flag_for_human", False),
        result.get("flag_for_human_review", False),
        result.get("key_incorrect", False),
        result.get("question_ambiguous", False),
        result.get("match_status") == "wrong_key",
        result.get("match_status") == "alternative_valid",
        result.get("confidence", 1.0) < 0.7  # Low confidence
    ]
    
    return any(conditions)


def _extract_json(text: str) -> Dict[str, Any]:
    """
    Extract JSON from LLM response (handles markdown code blocks and incomplete JSON)
    
    Args:
        text: Raw text response from LLM
        
    Returns:
        Parsed JSON dictionary
    """
    
    # Strategy 1: Try to find JSON in markdown code block
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
    
    # Strategy 2: Extract JSON by counting braces (handles incomplete responses)
    try:
        start = text.find('{')
        if start != -1:
            brace_count = 0
            in_string = False
            escape_next = False
            
            for i in range(start, len(text)):
                char = text[i]
                
                if escape_next:
                    escape_next = False
                    continue
                    
                if char == '\\':
                    escape_next = True
                    continue
                    
                if char == '"':
                    in_string = not in_string
                elif not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_str = text[start:i+1]
                            return json.loads(json_str)
    except (json.JSONDecodeError, ValueError):
        pass
    
    # Strategy 3: Try to find raw JSON object (simple regex)
    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
    if json_match:
        json_str = json_match.group(0)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
    
    # Strategy 4: Last resort - find first { to last }
    try:
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end > start:
            json_str = text[start:end+1]
            return json.loads(json_str)
    except (json.JSONDecodeError, ValueError):
        pass
    
    # If all strategies fail, raise error with context
    raise ValueError(f"No valid JSON found in response. Response preview: {text[:500]}")
