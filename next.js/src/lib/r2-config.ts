// Cloudflare R2 Configuration
export const R2_CONFIG = {
  accountId: process.env.CLOUDFLARE_ACCOUNT_ID!,
  accessKeyId: process.env.R2_ACCESS_KEY_ID!,
  secretAccessKey: process.env.R2_SECRET_ACCESS_KEY!,
  bucketName: process.env.R2_BUCKET_NAME!,
  region: 'auto',
  endpoint: `https://${process.env.CLOUDFLARE_ACCOUNT_ID}.r2.cloudflarestorage.com`,
  publicUrl: `https://pub-${process.env.CLOUDFLARE_ACCOUNT_ID}.r2.dev`
};

// Generate unique filenames
export const generateUniqueFileName = (originalName: string) => {
  const timestamp = Date.now();
  const randomString = Math.random().toString(36).substring(2, 8);
  const extension = originalName.split('.').pop();
  return `categories/${timestamp}-${randomString}.${extension}`;
};
