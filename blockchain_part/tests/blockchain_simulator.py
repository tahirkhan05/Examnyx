"""
Blockchain Simulator - Local Testing Tool

This script simulates the complete OMR evaluation lifecycle:
1. Creates fake OMR sheets
2. Triggers blockchain block creation for each stage
3. Validates chain integrity
4. Outputs expected hash sequences
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from app.blockchain import get_blockchain, Blockchain
from app.utils.hashing import HashingEngine
from datetime import datetime
import json
import random


class BlockchainSimulator:
    """Simulates complete OMR evaluation blockchain lifecycle"""
    
    def __init__(self):
        self.blockchain = get_blockchain(difficulty=2)  # Lower difficulty for testing
        self.sheets = []
        print("🔗 Blockchain Simulator Initialized")
        print(f"Genesis Block Hash: {self.blockchain.chain[0].hash}")
        print("-" * 80)
    
    def create_fake_sheet(self, sheet_number: int) -> dict:
        """Create a fake OMR sheet"""
        sheet_id = f"SHEET_{sheet_number:04d}"
        roll_number = f"ROLL{2024000 + sheet_number}"
        
        sheet = {
            "sheet_id": sheet_id,
            "roll_number": roll_number,
            "exam_id": "EXAM_2024_FINAL",
            "student_name": f"Student {sheet_number}",
            "file_hash": HashingEngine.hash_string(f"fake_file_content_{sheet_number}")
        }
        
        self.sheets.append(sheet)
        return sheet
    
    def simulate_scan_block(self, sheet: dict):
        """Simulate scan block creation"""
        print(f"\n📄 Creating SCAN block for {sheet['sheet_id']}")
        
        data = {
            "sheet_id": sheet["sheet_id"],
            "roll_number": sheet["roll_number"],
            "exam_id": sheet["exam_id"],
            "file_hash": sheet["file_hash"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        block = self.blockchain.create_block(
            block_type="scan",
            data=data,
            mine=True
        )
        
        print(f"   ✅ Block #{block.index} created")
        print(f"   Hash: {block.hash}")
        print(f"   Previous: {block.previous_hash}")
        print(f"   Nonce: {block.nonce}")
        
        return block
    
    def simulate_bubble_block(self, sheet: dict):
        """Simulate bubble interpretation block"""
        print(f"\n🔵 Creating BUBBLE block for {sheet['sheet_id']}")
        
        # Generate fake bubble data
        bubbles = []
        for i in range(1, 51):  # 50 questions
            bubbles.append({
                "question_number": i,
                "detected_answer": random.choice(["A", "B", "C", "D"]),
                "confidence": round(random.uniform(0.85, 0.99), 2)
            })
        
        data = {
            "sheet_id": sheet["sheet_id"],
            "bubbles": bubbles,
            "total_bubbles": len(bubbles),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        block = self.blockchain.create_block(
            block_type="bubble",
            data=data,
            mine=True
        )
        
        print(f"   ✅ Block #{block.index} created")
        print(f"   Hash: {block.hash}")
        print(f"   Detected {len(bubbles)} bubbles")
        
        return block
    
    def simulate_score_block(self, sheet: dict):
        """Simulate AI scoring block"""
        print(f"\n🤖 Creating SCORE block for {sheet['sheet_id']}")
        
        predictions = []
        for i in range(1, 51):
            predictions.append({
                "question_number": i,
                "predicted_answer": random.choice(["A", "B", "C", "D"]),
                "confidence": round(random.uniform(0.80, 0.98), 2)
            })
        
        data = {
            "sheet_id": sheet["sheet_id"],
            "model_name": "model_a",
            "predictions": predictions,
            "overall_confidence": 0.93,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        block = self.blockchain.create_block(
            block_type="score",
            data=data,
            mine=True
        )
        
        print(f"   ✅ Block #{block.index} created")
        print(f"   Hash: {block.hash}")
        print(f"   Model: {data['model_name']}")
        
        return block
    
    def simulate_verify_block(self, sheet: dict):
        """Simulate verification block with signatures"""
        print(f"\n✅ Creating VERIFY block for {sheet['sheet_id']}")
        
        signatures = [
            {"signer_type": "ai-verifier", "signature_hash": HashingEngine.hash_string("ai_sig")},
            {"signer_type": "human-verifier", "signature_hash": HashingEngine.hash_string("human_sig")},
            {"signer_type": "admin-controller", "signature_hash": HashingEngine.hash_string("admin_sig")}
        ]
        
        data = {
            "sheet_id": sheet["sheet_id"],
            "signatures": signatures,
            "verification_status": "approved",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        block = self.blockchain.create_block(
            block_type="verify",
            data=data,
            mine=True
        )
        
        print(f"   ✅ Block #{block.index} created")
        print(f"   Hash: {block.hash}")
        print(f"   Signatures: {len(signatures)}")
        
        return block
    
    def simulate_result_block(self, sheet: dict):
        """Simulate final result block"""
        print(f"\n🎯 Creating RESULT block for {sheet['sheet_id']}")
        
        correct = random.randint(30, 48)
        total = 50
        
        data = {
            "sheet_id": sheet["sheet_id"],
            "roll_number": sheet["roll_number"],
            "total_questions": total,
            "correct_answers": correct,
            "incorrect_answers": total - correct,
            "total_marks": correct * 2,
            "percentage": (correct / total) * 100,
            "grade": "A" if correct >= 45 else "B" if correct >= 35 else "C",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        block = self.blockchain.create_block(
            block_type="result",
            data=data,
            mine=True
        )
        
        print(f"   ✅ Block #{block.index} created")
        print(f"   Hash: {block.hash}")
        print(f"   Marks: {data['total_marks']}/{total * 2} ({data['percentage']:.1f}%)")
        print(f"   Grade: {data['grade']}")
        
        return block
    
    def simulate_complete_lifecycle(self, num_sheets: int = 3):
        """Simulate complete lifecycle for multiple sheets"""
        print(f"\n{'=' * 80}")
        print(f"🎬 SIMULATING COMPLETE LIFECYCLE FOR {num_sheets} SHEETS")
        print(f"{'=' * 80}")
        
        for i in range(1, num_sheets + 1):
            print(f"\n{'*' * 80}")
            print(f"📋 SHEET {i}/{num_sheets}")
            print(f"{'*' * 80}")
            
            sheet = self.create_fake_sheet(i)
            
            # Simulate each stage
            self.simulate_scan_block(sheet)
            self.simulate_bubble_block(sheet)
            self.simulate_score_block(sheet)
            self.simulate_verify_block(sheet)
            self.simulate_result_block(sheet)
    
    def validate_chain_integrity(self):
        """Validate blockchain integrity"""
        print(f"\n{'=' * 80}")
        print("🔍 VALIDATING BLOCKCHAIN INTEGRITY")
        print(f"{'=' * 80}")
        
        is_valid, error = self.blockchain.validate_chain()
        
        print(f"\nTotal Blocks: {len(self.blockchain.chain)}")
        print(f"Validation Status: {'✅ VALID' if is_valid else '❌ INVALID'}")
        
        if error:
            print(f"Error: {error}")
        
        # Show block type distribution
        stats = self.blockchain.get_chain_statistics()
        print(f"\nBlock Type Distribution:")
        for block_type, count in stats['block_types'].items():
            print(f"  {block_type.upper()}: {count}")
        
        return is_valid
    
    def output_hash_sequence(self):
        """Output expected hash sequence"""
        print(f"\n{'=' * 80}")
        print("📝 HASH SEQUENCE")
        print(f"{'=' * 80}")
        
        for block in self.blockchain.chain:
            print(f"\nBlock #{block.index} ({block.block_type.upper()})")
            print(f"  Hash:     {block.hash}")
            print(f"  Previous: {block.previous_hash}")
            print(f"  Merkle:   {block.merkle_root}")
    
    def export_simulation_results(self, filename: str = "simulation_results.json"):
        """Export simulation results to JSON"""
        results = {
            "simulation_timestamp": datetime.utcnow().isoformat(),
            "total_blocks": len(self.blockchain.chain),
            "total_sheets": len(self.sheets),
            "is_valid": self.blockchain.validate_chain()[0],
            "blockchain": self.blockchain.export_chain(),
            "sheets": self.sheets
        }
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Simulation results exported to: {filename}")
        return filename


def main():
    """Main simulation function"""
    print("\n" + "=" * 80)
    print(" OMR BLOCKCHAIN SIMULATOR")
    print("=" * 80)
    
    # Create simulator
    simulator = BlockchainSimulator()
    
    # Run complete lifecycle simulation
    simulator.simulate_complete_lifecycle(num_sheets=3)
    
    # Validate chain
    simulator.validate_chain_integrity()
    
    # Output hash sequence
    simulator.output_hash_sequence()
    
    # Export results
    simulator.export_simulation_results()
    
    print(f"\n{'=' * 80}")
    print("✅ SIMULATION COMPLETED SUCCESSFULLY")
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    main()
