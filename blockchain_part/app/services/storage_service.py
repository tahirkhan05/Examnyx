import boto3
from botocore.exceptions import ClientError
from typing import Optional, Dict, Any, List
import os
from datetime import datetime, timedelta
import mimetypes
from app.config import settings
from app.utils.hashing import HashingEngine
import io


class S3StorageService:
    """
    AWS S3 storage service for off-chain data storage
    Stores actual OMR sheet files while blockchain stores only hashes
    """
    
    def __init__(self):
        self.bucket_name = settings.S3_BUCKET_NAME
        self.region = settings.AWS_REGION
        
        # Initialize S3 client
        self.s3_client = None
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=self.region
            )
    
    def is_configured(self) -> bool:
        """Check if S3 is properly configured"""
        return self.s3_client is not None
    
    def upload_file(
        self,
        file_content: bytes,
        file_name: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Upload file to S3
        
        Args:
            file_content: File content as bytes
            file_name: Name of the file
            content_type: MIME type of the file
            metadata: Additional metadata
        
        Returns:
            Upload result with URL and hash
        """
        if not self.is_configured():
            # Fallback to local storage if S3 not configured
            return self._upload_local(file_content, file_name, metadata)
        
        try:
            # Generate file hash
            file_hash = HashingEngine.hash_file(file_content)
            
            # Detect content type if not provided
            if not content_type:
                content_type, _ = mimetypes.guess_type(file_name)
                if not content_type:
                    content_type = 'application/octet-stream'
            
            # Prepare metadata
            s3_metadata = metadata or {}
            s3_metadata['file_hash'] = file_hash
            s3_metadata['upload_timestamp'] = datetime.utcnow().isoformat()
            
            # Generate S3 key (path in bucket)
            date_prefix = datetime.utcnow().strftime('%Y/%m/%d')
            s3_key = f"omr_sheets/{date_prefix}/{file_hash}_{file_name}"
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type,
                Metadata=s3_metadata
            )
            
            # Generate URL
            s3_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
            
            return {
                "success": True,
                "s3_url": s3_url,
                "s3_key": s3_key,
                "file_hash": file_hash,
                "bucket": self.bucket_name,
                "region": self.region,
                "uploaded_at": datetime.utcnow().isoformat()
            }
        
        except ClientError as e:
            return {
                "success": False,
                "error": str(e),
                "fallback": self._upload_local(file_content, file_name, metadata)
            }
    
    def _upload_local(
        self,
        file_content: bytes,
        file_name: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Fallback: Upload to local storage
        
        Args:
            file_content: File content
            file_name: File name
            metadata: Metadata
        
        Returns:
            Upload result
        """
        # Create local storage directory
        local_storage_dir = "temp_storage/omr_sheets"
        os.makedirs(local_storage_dir, exist_ok=True)
        
        # Generate file hash
        file_hash = HashingEngine.hash_file(file_content)
        
        # Save file locally
        date_prefix = datetime.utcnow().strftime('%Y_%m_%d')
        local_path = os.path.join(local_storage_dir, f"{date_prefix}_{file_hash}_{file_name}")
        
        with open(local_path, 'wb') as f:
            f.write(file_content)
        
        # Save metadata
        if metadata:
            metadata_path = local_path + ".meta.json"
            import json
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
        
        return {
            "success": True,
            "storage_type": "local",
            "local_path": local_path,
            "file_hash": file_hash,
            "uploaded_at": datetime.utcnow().isoformat()
        }
    
    def download_file(self, s3_key: str) -> Optional[bytes]:
        """
        Download file from S3
        
        Args:
            s3_key: S3 object key
        
        Returns:
            File content as bytes or None
        """
        if not self.is_configured():
            return None
        
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return response['Body'].read()
        
        except ClientError as e:
            print(f"Error downloading from S3: {e}")
            return None
    
    def generate_presigned_url(
        self,
        s3_key: str,
        expiration: int = 3600
    ) -> Optional[str]:
        """
        Generate presigned URL for temporary access
        
        Args:
            s3_key: S3 object key
            expiration: URL expiration in seconds (default 1 hour)
        
        Returns:
            Presigned URL or None
        """
        if not self.is_configured():
            return None
        
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=expiration
            )
            return url
        
        except ClientError as e:
            print(f"Error generating presigned URL: {e}")
            return None
    
    def verify_file_integrity(
        self,
        s3_key: str,
        expected_hash: str
    ) -> bool:
        """
        Verify file integrity by comparing hashes
        
        Args:
            s3_key: S3 object key
            expected_hash: Expected file hash
        
        Returns:
            True if hash matches, False otherwise
        """
        file_content = self.download_file(s3_key)
        
        if not file_content:
            return False
        
        actual_hash = HashingEngine.hash_file(file_content)
        return actual_hash == expected_hash
    
    def get_file_metadata(self, s3_key: str) -> Optional[Dict[str, Any]]:
        """
        Get file metadata from S3
        
        Args:
            s3_key: S3 object key
        
        Returns:
            Metadata dictionary or None
        """
        if not self.is_configured():
            return None
        
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            return {
                "content_type": response.get('ContentType'),
                "content_length": response.get('ContentLength'),
                "last_modified": response.get('LastModified'),
                "metadata": response.get('Metadata', {}),
                "etag": response.get('ETag')
            }
        
        except ClientError as e:
            print(f"Error getting metadata: {e}")
            return None
    
    def delete_file(self, s3_key: str) -> bool:
        """
        Delete file from S3
        
        Args:
            s3_key: S3 object key
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_configured():
            return False
        
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return True
        
        except ClientError as e:
            print(f"Error deleting file: {e}")
            return False
    
    def list_files(
        self,
        prefix: str = "omr_sheets/",
        max_keys: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List files in S3 bucket
        
        Args:
            prefix: Key prefix to filter
            max_keys: Maximum number of keys to return
        
        Returns:
            List of file information
        """
        if not self.is_configured():
            return []
        
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            files = []
            for obj in response.get('Contents', []):
                files.append({
                    "key": obj['Key'],
                    "size": obj['Size'],
                    "last_modified": obj['LastModified'].isoformat(),
                    "etag": obj['ETag']
                })
            
            return files
        
        except ClientError as e:
            print(f"Error listing files: {e}")
            return []
    
    def create_storage_mapping(
        self,
        sheet_id: str,
        s3_url: str,
        file_hash: str,
        blockchain_hash: str
    ) -> Dict[str, Any]:
        """
        Create mapping between on-chain and off-chain storage
        
        Args:
            sheet_id: Sheet identifier
            s3_url: S3 URL
            file_hash: File hash
            blockchain_hash: Blockchain hash
        
        Returns:
            Storage mapping
        """
        return {
            "sheet_id": sheet_id,
            "storage": {
                "type": "s3",
                "url": s3_url,
                "file_hash": file_hash
            },
            "blockchain": {
                "hash": blockchain_hash,
                "stored_on_chain": False,
                "hash_verification": "on-chain"
            },
            "mapping_created_at": datetime.utcnow().isoformat()
        }


# Global instance
s3_service = None


def get_s3_service() -> S3StorageService:
    """Get or create S3 service singleton"""
    global s3_service
    if s3_service is None:
        s3_service = S3StorageService()
    return s3_service


# Export
__all__ = ["S3StorageService", "get_s3_service"]
