import os
import boto3
from botocore.exceptions import NoCredentialsError, ClientError

# Configuration
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY")
R2_SECRET_KEY = os.getenv("R2_SECRET_KEY")
R2_BUCKET = os.getenv("R2_BUCKET", "paisa-invoices")

def get_s3_client():
    if not all([R2_ACCOUNT_ID, R2_ACCESS_KEY, R2_SECRET_KEY]):
        return None
        
    endpoint_url = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
    
    return boto3.client(
        's3',
        endpoint_url=endpoint_url,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
        region_name='auto'  # R2 requires region to be 'auto'
    )

async def upload_to_r2(file_bytes: bytes, filename: str) -> str:
    """
    Uploads file bytes to Cloudflare R2 and returns the public URL or error.
    """
    s3_client = get_s3_client()
    if not s3_client:
        print("R2 credentials not found, skipping upload")
        return ""
        
    try:
        # Assuming you want to organize by date or just root
        import datetime
        date_str = datetime.datetime.now().strftime("%Y-%m")
        object_key = f"invoices/{date_str}/{filename}"
        
        s3_client.put_object(
            Bucket=R2_BUCKET,
            Key=object_key,
            Body=file_bytes
        )
        
        # Depending on if bucket is public or you need pre-signed URL
        # URL format: https://<custom-domain>/<object-key> if public
        # Using a fallback pre-signed URL for this example
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': R2_BUCKET, 'Key': object_key},
            ExpiresIn=3600 * 24 * 7 # 7 days
        )
        return url
    except Exception as e:
        print(f"Failed to upload to R2: {e}")
        return ""
