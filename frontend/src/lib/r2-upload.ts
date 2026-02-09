import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3';
import { Upload } from '@aws-sdk/lib-storage';
import { R2_CONFIG, generateUniqueFileName } from './r2-config';

// Initialize S3 client for R2
const s3Client = new S3Client({
  region: R2_CONFIG.region,
  endpoint: R2_CONFIG.endpoint,
  credentials: {
    accessKeyId: R2_CONFIG.accessKeyId,
    secretAccessKey: R2_CONFIG.secretAccessKey,
  },
});

// Upload image to R2
export const uploadImageToR2 = async (file: File): Promise<string> => {
  try {
    const fileName = generateUniqueFileName(file.name);
    
    const upload = new Upload({
      client: s3Client,
      params: {
        Bucket: R2_CONFIG.bucketName,
        Key: fileName,
        Body: file,
        ContentType: file.type,
      },
    });

    await upload.done();
    
    // Return public URL
    return `${R2_CONFIG.publicUrl}/${fileName}`;
  } catch (error) {
    console.error('Error uploading to R2:', error);
    throw new Error('Failed to upload image');
  }
};

// Delete image from R2
export const deleteImageFromR2 = async (imageUrl: string): Promise<void> => {
  try {
    // Extract filename from URL
    const fileName = imageUrl.split('/').pop();
    
    const command = new PutObjectCommand({
      Bucket: R2_CONFIG.bucketName,
      Key: `categories/${fileName}`,
    });

    await s3Client.send(command);
  } catch (error) {
    console.error('Error deleting from R2:', error);
  }
};
