import base64
import io
import json
import logging
import sys
import boto3
from PIL import Image
from botocore.exceptions import ClientError
from urllib.parse import urlparse

def main(input_s3_url, output_s3_url):
    """
    Entrypoint for Amazon Titan Image Background Removal example.
    
    Args:
        input_s3_url (str): S3 URL of the input image (s3://bucket-name/key)
        output_s3_url (str): S3 URL to save the processed image (s3://bucket-name/key)
    """
    try:
        logging.basicConfig(level=logging.INFO,
                            format="%(levelname)s: %(message)s")
        
        model_id = 'amazon.nova-canvas-v1:0'
        
        logger.info(f"Processing image from {input_s3_url} to {output_s3_url}")
        
        # Read image from S3 and encode it as a base64 string
        input_image = read_image_from_s3(input_s3_url)
        
        # Ensure the request body conforms to the expected format
        body = json.dumps({
            "taskType": "BACKGROUND_REMOVAL",
            "backgroundRemovalParams": {
                "image": input_image
            }
        })
        
        # Process the image to remove background
        image_bytes = remove_background(model_id=model_id, body=body)
        
        # Save the output image to S3
        save_image_to_s3(image_bytes, output_s3_url)
        
    except ClientError as err:
        message = err.response["Error"]["Message"]
        logger.error("A client error occurred: %s", message)
        print("A client error occurred: " + format(message))
        sys.exit(1)
    except ImageError as err:
        logger.error(err.message)
        print(err.message)
        sys.exit(1)
    except Exception as err:
        logger.error(f"An unexpected error occurred: {str(err)}")
        print(f"An unexpected error occurred: {str(err)}")
        sys.exit(1)
    else:
        print(f"Finished background removal using Amazon Nova Canvas image generation model {model_id}.")
        print(f"Output image saved to {output_s3_url}")
        return 0

def parse_s3_url(s3_url):
    """
    Parse an S3 URL into bucket name and object key.
    
    Args:
        s3_url (str): The S3 URL in the format s3://bucket-name/key
        
    Returns:
        tuple: (bucket_name, object_key)
    """
    parsed_url = urlparse(s3_url)
    if parsed_url.scheme != 's3':
        raise ValueError(f"Invalid S3 URL scheme: {s3_url}. Must start with s3://")
    
    bucket = parsed_url.netloc
    key = parsed_url.path.lstrip('/')
    
    if not bucket or not key:
        raise ValueError(f"Invalid S3 URL format: {s3_url}. Must be s3://bucket-name/key")
    
    return bucket, key

def read_image_from_s3(s3_url):
    """
    Read an image from an S3 URL and encode it as a base64 string.
    
    Args:
        s3_url (str): The S3 URL of the image
        
    Returns:
        str: Base64-encoded image
    """
    logger.info(f"Reading image from S3: {s3_url}")
    
    try:
        bucket, key = parse_s3_url(s3_url)
        
        # Create S3 client
        s3_client = boto3.client('s3')
        
        # Get the object from S3
        response = s3_client.get_object(Bucket=bucket, Key=key)
        image_content = response['Body'].read()
        
        # Encode as base64
        base64_image = base64.b64encode(image_content).decode('utf-8')
        
        logger.info(f"Successfully read image from S3 (size: {len(image_content)} bytes)")
        return base64_image
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        if error_code == 'NoSuchKey':
            raise ImageError(f"Image not found at {s3_url}")
        elif error_code == 'AccessDenied':
            raise ImageError(f"Access denied to image at {s3_url}. Check your AWS permissions.")
        else:
            raise ImageError(f"S3 error: {str(e)}")
    except Exception as e:
        raise ImageError(f"Error reading image from S3: {str(e)}")

def save_image_to_s3(image_bytes, s3_url):
    """
    Save an image to an S3 URL.
    
    Args:
        image_bytes (bytes): The image bytes to save
        s3_url (str): The S3 URL to save the image to
    """
    logger.info(f"Saving image to S3: {s3_url}")
    
    try:
        bucket, key = parse_s3_url(s3_url)
        
        # Create S3 client
        s3_client = boto3.client('s3')
        
        # Convert the image to PNG with transparency
        img = Image.open(io.BytesIO(image_bytes))
        
        # Save to a bytes buffer
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        # Upload to S3
        s3_client.upload_fileobj(
            buffer, 
            bucket, 
            key,
            ExtraArgs={'ContentType': 'image/png'}
        )
        
        logger.info(f"Successfully saved image to S3")
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        if error_code == 'AccessDenied':
            raise ImageError(f"Access denied when saving to {s3_url}. Check your AWS permissions.")
        else:
            raise ImageError(f"S3 error when saving: {str(e)}")
    except Exception as e:
        raise ImageError(f"Error saving image to S3: {str(e)}")

def remove_background(model_id, body):
    """
    Remove the background from an image using Amazon Nova Canvas image generation model.
    
    Args:
        model_id (str): The model ID to use
        body (str): The request body to use
        
    Returns:
        image_bytes (bytes): The processed image with the background removed
    """
    logger.info("Removing background with Amazon Nova Canvas image generation model %s", model_id)
    
    try:
        bedrock = boto3.client(service_name='bedrock-runtime')
    except ClientError as err:
        logger.error("Failed to create Bedrock client: %s", err)
        raise ImageError(f"Failed to create Bedrock client: {str(err)}. Make sure AWS CLI is configured correctly.")
    
    accept = "application/json"
    content_type = "application/json"
    
    try:
        response = bedrock.invoke_model(
            body=body, modelId=model_id, accept=accept, contentType=content_type
        )
        response_body = json.loads(response.get("body").read())
    except ClientError as err:
        if 'AccessDeniedException' in str(err):
            raise ImageError("Access denied to Bedrock model. Check your AWS permissions.")
        else:
            raise ImageError(f"Bedrock API error: {str(err)}")
    except KeyError as err:
        logger.error("Malformed API response: %s", err)
        raise ImageError("Malformed API response from Bedrock service.")
    except Exception as err:
        raise ImageError(f"Error invoking Bedrock model: {str(err)}")
    
    try:
        base64_image = response_body.get("images")[0]
        if not base64_image:
            raise ImageError("No processed image returned in the response.")
        
        base64_bytes = base64_image.encode('ascii')
        image_bytes = base64.b64decode(base64_bytes)
        
        finish_reason = response_body.get("error")
        if finish_reason is not None:
            raise ImageError(f"Background removal error. Error is {finish_reason}")
        
        logger.info("Successfully removed background with Amazon Nova Canvas image generation model %s", model_id)
        return image_bytes
    except (KeyError, IndexError) as e:
        raise ImageError(f"Error parsing Bedrock response: {str(e)}")

class ImageError(Exception):
    """Custom exception for errors returned by Amazon Nova Canvas image generation model"""
    def __init__(self, message):
        self.message = message

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    
    # Check command-line arguments
    if len(sys.argv) != 3:
        print("Usage: python bg_remove.py s3://input-bucket/input-image.jpg s3://output-bucket/output-image.png")
        sys.exit(1)
    
    # Get the S3 paths from command-line arguments
    input_s3_url = sys.argv[1]
    output_s3_url = sys.argv[2]
    
    # Call the main function
    exit_code = main(input_s3_url, output_s3_url)
    sys.exit(exit_code)
