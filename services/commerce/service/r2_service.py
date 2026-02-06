"""Cloudflare R2 storage service for image uploads."""
import boto3
import uuid
from typing import Optional, BinaryIO
from botocore.config import Config
from fastapi import UploadFile, HTTPException, status

from core.config import settings


class R2StorageService:
    """Service for managing file uploads to Cloudflare R2."""
    
    def __init__(self):
        """Initialize R2 client."""
        self._client = None
    
    @property
    def client(self):
        """Lazy-load S3 client for R2."""
        if self._client is None:
            if not settings.R2_ACCESS_KEY_ID or not settings.R2_SECRET_ACCESS_KEY:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="R2 storage is not configured"
                )
            
            self._client = boto3.client(
                's3',
                endpoint_url=f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
                aws_access_key_id=settings.R2_ACCESS_KEY_ID,
                aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
                region_name=settings.R2_REGION,
                config=Config(signature_version='s3v4')
            )
        return self._client
    
    def _generate_unique_filename(self, original_filename: str, folder: str = "products") -> str:
        """Generate a unique filename."""
        ext = original_filename.split('.')[-1] if '.' in original_filename else 'jpg'
        unique_id = uuid.uuid4().hex[:12]
        return f"{folder}/{unique_id}.{ext}"
    
    async def upload_image(
        self, 
        file: UploadFile, 
        folder: str = "products"
    ) -> str:
        """
        Upload an image to R2 storage.
        
        Args:
            file: The uploaded file
            folder: Subfolder in bucket (products, categories, etc.)
            
        Returns:
            The public URL of the uploaded image
        """
        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
            )
        
        # Generate unique filename
        key = self._generate_unique_filename(file.filename, folder)
        
        try:
            # Read file content
            content = await file.read()
            
            # Upload to R2
            self.client.put_object(
                Bucket=settings.R2_BUCKET_NAME,
                Key=key,
                Body=content,
                ContentType=file.content_type
            )
            
            # Return public URL
            if settings.R2_PUBLIC_URL:
                return f"{settings.R2_PUBLIC_URL.rstrip('/')}/{key}"
            else:
                return f"https://{settings.R2_BUCKET_NAME}.{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com/{key}"
                
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload image: {str(e)}"
            )
    
    async def delete_image(self, image_url: str) -> bool:
        """
        Delete an image from R2 storage.
        
        Args:
            image_url: The full URL of the image to delete
            
        Returns:
            True if deleted successfully
        """
        try:
            # Extract key from URL
            if settings.R2_PUBLIC_URL and image_url.startswith(settings.R2_PUBLIC_URL):
                key = image_url.replace(settings.R2_PUBLIC_URL.rstrip('/') + '/', '')
            else:
                # Extract from default URL format
                key = '/'.join(image_url.split('/')[-2:])
            
            self.client.delete_object(
                Bucket=settings.R2_BUCKET_NAME,
                Key=key
            )
            return True
            
        except Exception as e:
            print(f"Warning: Failed to delete image {image_url}: {str(e)}")
            return False
    
    def generate_presigned_url(
        self, 
        filename: str, 
        folder: str = "products",
        expires_in: int = 3600
    ) -> dict:
        """
        Generate a presigned URL for direct client-side upload.
        
        Args:
            filename: Original filename
            folder: Subfolder in bucket
            expires_in: URL expiration time in seconds
            
        Returns:
            Dict with upload_url and final_url
        """
        key = self._generate_unique_filename(filename, folder)
        
        try:
            presigned_url = self.client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': settings.R2_BUCKET_NAME,
                    'Key': key
                },
                ExpiresIn=expires_in
            )
            
            if settings.R2_PUBLIC_URL:
                final_url = f"{settings.R2_PUBLIC_URL.rstrip('/')}/{key}"
            else:
                final_url = f"https://{settings.R2_BUCKET_NAME}.{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com/{key}"
            
            return {
                "upload_url": presigned_url,
                "final_url": final_url,
                "key": key
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate presigned URL: {str(e)}"
            )


# Singleton instance
r2_service = R2StorageService()
