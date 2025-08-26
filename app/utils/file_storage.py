import boto3
from botocore.exceptions import ClientError
import aiofiles
import os
from pathlib import Path
from typing import Optional
import logging
from minio import Minio
from minio.error import S3Error
import io

from ..database.config import settings

logger = logging.getLogger(__name__)


class FileStorageManager:
    """File storage manager supporting both local and cloud storage"""
    
    def __init__(self):
        self.storage_type = getattr(settings, 'storage_type', 'local')  # local, s3, minio
        self.local_storage_path = getattr(settings, 'local_storage_path', './storage')
        
        # Initialize cloud storage clients
        self.s3_client = None
        self.minio_client = None
        
        if self.storage_type == 's3':
            self._init_s3_client()
        elif self.storage_type == 'minio':
            self._init_minio_client()
        else:
            self._init_local_storage()
    
    def _init_s3_client(self):
        """Initialize AWS S3 client"""
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region
            )
            logger.info("S3 client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {str(e)}")
            raise
    
    def _init_minio_client(self):
        """Initialize MinIO client"""
        try:
            self.minio_client = Minio(
                settings.minio_endpoint,
                access_key=settings.minio_access_key,
                secret_key=settings.minio_secret_key,
                secure=False  # Set to True for HTTPS
            )
            
            # Create bucket if it doesn't exist
            bucket_name = settings.s3_bucket_name
            if not self.minio_client.bucket_exists(bucket_name):
                self.minio_client.make_bucket(bucket_name)
                logger.info(f"Created MinIO bucket: {bucket_name}")
            
            logger.info("MinIO client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize MinIO client: {str(e)}")
            raise
    
    def _init_local_storage(self):
        """Initialize local storage directory"""
        try:
            Path(self.local_storage_path).mkdir(parents=True, exist_ok=True)
            logger.info(f"Local storage initialized at: {self.local_storage_path}")
        except Exception as e:
            logger.error(f"Failed to initialize local storage: {str(e)}")
            raise
    
    async def upload_file(self, file_content: bytes, file_path: str) -> bool:
        """Upload file to storage"""
        try:
            if self.storage_type == 's3':
                return await self._upload_to_s3(file_content, file_path)
            elif self.storage_type == 'minio':
                return await self._upload_to_minio(file_content, file_path)
            else:
                return await self._upload_to_local(file_content, file_path)
        except Exception as e:
            logger.error(f"Failed to upload file {file_path}: {str(e)}")
            return False
    
    async def download_file(self, file_path: str) -> Optional[bytes]:
        """Download file from storage"""
        try:
            if self.storage_type == 's3':
                return await self._download_from_s3(file_path)
            elif self.storage_type == 'minio':
                return await self._download_from_minio(file_path)
            else:
                return await self._download_from_local(file_path)
        except Exception as e:
            logger.error(f"Failed to download file {file_path}: {str(e)}")
            return None
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from storage"""
        try:
            if self.storage_type == 's3':
                return await self._delete_from_s3(file_path)
            elif self.storage_type == 'minio':
                return await self._delete_from_minio(file_path)
            else:
                return await self._delete_from_local(file_path)
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {str(e)}")
            return False
    
    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists in storage"""
        try:
            if self.storage_type == 's3':
                return await self._file_exists_s3(file_path)
            elif self.storage_type == 'minio':
                return await self._file_exists_minio(file_path)
            else:
                return await self._file_exists_local(file_path)
        except Exception as e:
            logger.error(f"Failed to check file existence {file_path}: {str(e)}")
            return False
    
    async def get_file_size(self, file_path: str) -> Optional[int]:
        """Get file size"""
        try:
            if self.storage_type == 's3':
                return await self._get_file_size_s3(file_path)
            elif self.storage_type == 'minio':
                return await self._get_file_size_minio(file_path)
            else:
                return await self._get_file_size_local(file_path)
        except Exception as e:
            logger.error(f"Failed to get file size {file_path}: {str(e)}")
            return None
    
    # S3 implementations
    async def _upload_to_s3(self, file_content: bytes, file_path: str) -> bool:
        """Upload file to S3"""
        try:
            self.s3_client.put_object(
                Bucket=settings.s3_bucket_name,
                Key=file_path,
                Body=file_content
            )
            logger.info(f"Successfully uploaded {file_path} to S3")
            return True
        except ClientError as e:
            logger.error(f"S3 upload error: {str(e)}")
            return False
    
    async def _download_from_s3(self, file_path: str) -> Optional[bytes]:
        """Download file from S3"""
        try:
            response = self.s3_client.get_object(
                Bucket=settings.s3_bucket_name,
                Key=file_path
            )
            return response['Body'].read()
        except ClientError as e:
            logger.error(f"S3 download error: {str(e)}")
            return None
    
    async def _delete_from_s3(self, file_path: str) -> bool:
        """Delete file from S3"""
        try:
            self.s3_client.delete_object(
                Bucket=settings.s3_bucket_name,
                Key=file_path
            )
            return True
        except ClientError as e:
            logger.error(f"S3 delete error: {str(e)}")
            return False
    
    async def _file_exists_s3(self, file_path: str) -> bool:
        """Check if file exists in S3"""
        try:
            self.s3_client.head_object(
                Bucket=settings.s3_bucket_name,
                Key=file_path
            )
            return True
        except ClientError:
            return False
    
    async def _get_file_size_s3(self, file_path: str) -> Optional[int]:
        """Get file size from S3"""
        try:
            response = self.s3_client.head_object(
                Bucket=settings.s3_bucket_name,
                Key=file_path
            )
            return response['ContentLength']
        except ClientError:
            return None
    
    # MinIO implementations
    async def _upload_to_minio(self, file_content: bytes, file_path: str) -> bool:
        """Upload file to MinIO"""
        try:
            self.minio_client.put_object(
                settings.s3_bucket_name,
                file_path,
                io.BytesIO(file_content),
                len(file_content)
            )
            logger.info(f"Successfully uploaded {file_path} to MinIO")
            return True
        except S3Error as e:
            logger.error(f"MinIO upload error: {str(e)}")
            return False
    
    async def _download_from_minio(self, file_path: str) -> Optional[bytes]:
        """Download file from MinIO"""
        try:
            response = self.minio_client.get_object(
                settings.s3_bucket_name,
                file_path
            )
            return response.read()
        except S3Error as e:
            logger.error(f"MinIO download error: {str(e)}")
            return None
    
    async def _delete_from_minio(self, file_path: str) -> bool:
        """Delete file from MinIO"""
        try:
            self.minio_client.remove_object(
                settings.s3_bucket_name,
                file_path
            )
            return True
        except S3Error as e:
            logger.error(f"MinIO delete error: {str(e)}")
            return False
    
    async def _file_exists_minio(self, file_path: str) -> bool:
        """Check if file exists in MinIO"""
        try:
            self.minio_client.stat_object(
                settings.s3_bucket_name,
                file_path
            )
            return True
        except S3Error:
            return False
    
    async def _get_file_size_minio(self, file_path: str) -> Optional[int]:
        """Get file size from MinIO"""
        try:
            stat = self.minio_client.stat_object(
                settings.s3_bucket_name,
                file_path
            )
            return stat.size
        except S3Error:
            return None
    
    # Local storage implementations
    async def _upload_to_local(self, file_content: bytes, file_path: str) -> bool:
        """Upload file to local storage"""
        try:
            full_path = Path(self.local_storage_path) / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(full_path, 'wb') as f:
                await f.write(file_content)
            
            logger.info(f"Successfully uploaded {file_path} to local storage")
            return True
        except Exception as e:
            logger.error(f"Local upload error: {str(e)}")
            return False
    
    async def _download_from_local(self, file_path: str) -> Optional[bytes]:
        """Download file from local storage"""
        try:
            full_path = Path(self.local_storage_path) / file_path
            
            if not full_path.exists():
                return None
            
            async with aiofiles.open(full_path, 'rb') as f:
                return await f.read()
        except Exception as e:
            logger.error(f"Local download error: {str(e)}")
            return None
    
    async def _delete_from_local(self, file_path: str) -> bool:
        """Delete file from local storage"""
        try:
            full_path = Path(self.local_storage_path) / file_path
            
            if full_path.exists():
                full_path.unlink()
                return True
            return False
        except Exception as e:
            logger.error(f"Local delete error: {str(e)}")
            return False
    
    async def _file_exists_local(self, file_path: str) -> bool:
        """Check if file exists in local storage"""
        try:
            full_path = Path(self.local_storage_path) / file_path
            return full_path.exists()
        except Exception:
            return False
    
    async def _get_file_size_local(self, file_path: str) -> Optional[int]:
        """Get file size from local storage"""
        try:
            full_path = Path(self.local_storage_path) / file_path
            
            if full_path.exists():
                return full_path.stat().st_size
            return None
        except Exception:
            return None