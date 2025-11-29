import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import uuid
from app.utils.hashing import HashingEngine


class AuditLogger:
    """
    Comprehensive JSON-based audit logging system
    Tracks all events chronologically with blockchain hash references
    """
    
    def __init__(self, log_directory: str = "audit_logs"):
        self.log_directory = log_directory
        self._ensure_log_directory()
    
    def _ensure_log_directory(self):
        """Create log directory if it doesn't exist"""
        Path(self.log_directory).mkdir(parents=True, exist_ok=True)
    
    def _get_log_file_path(self, sheet_id: str) -> str:
        """Get log file path for a specific sheet"""
        return os.path.join(self.log_directory, f"{sheet_id}.json")
    
    def _get_master_log_path(self) -> str:
        """Get master log file path"""
        return os.path.join(self.log_directory, "master_log.json")
    
    def create_log_entry(
        self,
        sheet_id: str,
        event_type: str,
        event_data: Dict[str, Any],
        blockchain_hash: Optional[str] = None,
        actor: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new audit log entry
        
        Args:
            sheet_id: Sheet identifier
            event_type: Type of event (scan, bubble, score, verify, result, recheck)
            event_data: Event-specific data
            blockchain_hash: Associated blockchain hash
            actor: Who triggered the event
            metadata: Additional metadata
        
        Returns:
            Log entry dictionary
        """
        log_entry = {
            "log_id": str(uuid.uuid4()),
            "sheet_id": sheet_id,
            "event_type": event_type,
            "event_data": event_data,
            "blockchain_hash": blockchain_hash,
            "actor": actor or "system",
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat(),
            "event_hash": HashingEngine.hash_dict({
                "sheet_id": sheet_id,
                "event_type": event_type,
                "event_data": event_data,
                "timestamp": datetime.utcnow().isoformat()
            })
        }
        
        return log_entry
    
    def append_log(
        self,
        sheet_id: str,
        event_type: str,
        event_data: Dict[str, Any],
        blockchain_hash: Optional[str] = None,
        actor: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Append log entry to sheet's audit log
        
        Args:
            sheet_id: Sheet identifier
            event_type: Event type
            event_data: Event data
            blockchain_hash: Blockchain hash
            actor: Actor
            metadata: Metadata
        
        Returns:
            Created log entry
        """
        log_entry = self.create_log_entry(
            sheet_id=sheet_id,
            event_type=event_type,
            event_data=event_data,
            blockchain_hash=blockchain_hash,
            actor=actor,
            metadata=metadata
        )
        
        # Get log file path
        log_file = self._get_log_file_path(sheet_id)
        
        # Load existing logs or create new
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                logs = json.load(f)
        else:
            logs = {
                "sheet_id": sheet_id,
                "created_at": datetime.utcnow().isoformat(),
                "entries": []
            }
        
        # Append new entry
        logs["entries"].append(log_entry)
        logs["updated_at"] = datetime.utcnow().isoformat()
        logs["entry_count"] = len(logs["entries"])
        
        # Save logs
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2)
        
        # Also append to master log
        self._append_to_master_log(log_entry)
        
        return log_entry
    
    def _append_to_master_log(self, log_entry: Dict[str, Any]):
        """Append entry to master log"""
        master_log_file = self._get_master_log_path()
        
        # Load existing master log
        if os.path.exists(master_log_file):
            with open(master_log_file, 'r') as f:
                master_log = json.load(f)
        else:
            master_log = {
                "created_at": datetime.utcnow().isoformat(),
                "entries": []
            }
        
        # Append entry
        master_log["entries"].append(log_entry)
        master_log["updated_at"] = datetime.utcnow().isoformat()
        master_log["entry_count"] = len(master_log["entries"])
        
        # Save
        with open(master_log_file, 'w') as f:
            json.dump(master_log, f, indent=2)
    
    def get_sheet_logs(self, sheet_id: str) -> Optional[Dict[str, Any]]:
        """
        Get all logs for a specific sheet
        
        Args:
            sheet_id: Sheet identifier
        
        Returns:
            Log data or None if not found
        """
        log_file = self._get_log_file_path(sheet_id)
        
        if not os.path.exists(log_file):
            return None
        
        with open(log_file, 'r') as f:
            return json.load(f)
    
    def get_sheet_timeline(self, sheet_id: str) -> List[Dict[str, Any]]:
        """
        Get chronological timeline of events for a sheet
        
        Args:
            sheet_id: Sheet identifier
        
        Returns:
            List of events sorted by timestamp
        """
        logs = self.get_sheet_logs(sheet_id)
        
        if not logs:
            return []
        
        return sorted(
            logs.get("entries", []),
            key=lambda x: x["timestamp"]
        )
    
    def get_logs_by_type(
        self,
        sheet_id: str,
        event_type: str
    ) -> List[Dict[str, Any]]:
        """
        Get logs filtered by event type
        
        Args:
            sheet_id: Sheet identifier
            event_type: Event type to filter
        
        Returns:
            Filtered logs
        """
        logs = self.get_sheet_logs(sheet_id)
        
        if not logs:
            return []
        
        return [
            entry for entry in logs.get("entries", [])
            if entry["event_type"] == event_type
        ]
    
    def get_logs_by_blockchain_hash(
        self,
        blockchain_hash: str
    ) -> List[Dict[str, Any]]:
        """
        Get logs associated with a blockchain hash
        
        Args:
            blockchain_hash: Blockchain hash
        
        Returns:
            Associated logs
        """
        master_log_file = self._get_master_log_path()
        
        if not os.path.exists(master_log_file):
            return []
        
        with open(master_log_file, 'r') as f:
            master_log = json.load(f)
        
        return [
            entry for entry in master_log.get("entries", [])
            if entry.get("blockchain_hash") == blockchain_hash
        ]
    
    def verify_log_integrity(self, sheet_id: str) -> tuple[bool, Optional[str]]:
        """
        Verify integrity of log file
        
        Args:
            sheet_id: Sheet identifier
        
        Returns:
            (is_valid, error_message)
        """
        logs = self.get_sheet_logs(sheet_id)
        
        if not logs:
            return False, "Log file not found"
        
        # Verify each entry's hash
        for entry in logs.get("entries", []):
            expected_hash = HashingEngine.hash_dict({
                "sheet_id": entry["sheet_id"],
                "event_type": entry["event_type"],
                "event_data": entry["event_data"],
                "timestamp": entry["timestamp"]
            })
            
            if entry.get("event_hash") != expected_hash:
                return False, f"Invalid hash for log entry {entry['log_id']}"
        
        return True, None
    
    def generate_audit_report(
        self,
        sheet_id: str
    ) -> Dict[str, Any]:
        """
        Generate comprehensive audit report for a sheet
        
        Args:
            sheet_id: Sheet identifier
        
        Returns:
            Audit report
        """
        logs = self.get_sheet_logs(sheet_id)
        
        if not logs:
            return {"error": "No logs found"}
        
        entries = logs.get("entries", [])
        
        # Count events by type
        event_counts = {}
        for entry in entries:
            event_type = entry["event_type"]
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        # Get blockchain hashes
        blockchain_hashes = [
            entry.get("blockchain_hash")
            for entry in entries
            if entry.get("blockchain_hash")
        ]
        
        # Verify integrity
        is_valid, error = self.verify_log_integrity(sheet_id)
        
        return {
            "sheet_id": sheet_id,
            "total_events": len(entries),
            "event_types": event_counts,
            "first_event": entries[0]["timestamp"] if entries else None,
            "last_event": entries[-1]["timestamp"] if entries else None,
            "blockchain_hashes": blockchain_hashes,
            "integrity_verified": is_valid,
            "integrity_error": error,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def export_logs(
        self,
        sheet_id: str,
        output_path: Optional[str] = None
    ) -> str:
        """
        Export logs to a file
        
        Args:
            sheet_id: Sheet identifier
            output_path: Optional output path
        
        Returns:
            Path to exported file
        """
        logs = self.get_sheet_logs(sheet_id)
        
        if not logs:
            raise ValueError(f"No logs found for sheet {sheet_id}")
        
        if not output_path:
            output_path = f"audit_export_{sheet_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(output_path, 'w') as f:
            json.dump(logs, f, indent=2)
        
        return output_path


# Global logger instance
audit_logger = None


def get_audit_logger() -> AuditLogger:
    """Get or create audit logger singleton"""
    global audit_logger
    if audit_logger is None:
        audit_logger = AuditLogger()
    return audit_logger


# Export
__all__ = ["AuditLogger", "get_audit_logger"]
