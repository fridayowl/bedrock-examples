import base64
import io
import json
import logging
import argparse
import boto3
from PIL import Image
from botocore.exceptions import ClientError
import random

class ImageError(Exception):
    "Custom exception for errors returned by Amazon Nova Canvas"
    def __init__(self, message):
        self.message = message

def generate_image(model_id, body):
    """
    Generate an image using Amazon Nova Canvas model.
    """
    logger = logging.getLogger(__name__)
    logger.info("Generating image with Amazon Nova Canvas model %s", model_id)

    bedrock = boto3.client(service_name='bedrock-runtime')

    response = bedrock.invoke_model(
        body=body,
        modelId=model_id,
        accept="application/json",
        contentType="application/json"
    )
    
    response_body = json.loads(response.get("body").read())

    base64_image = response_body.get("images")[0]
    base64_bytes = base64_image.encode('ascii')
    image_bytes = base64.b64decode(base64_bytes)

    finish_reason = response_body.get("error")
    if finish_reason is not None:
        raise ImageError(f"Image generation error. Error is {finish_reason}")

    logger.info("Successfully generated image")
    return image_bytes

def change_background(image_path, background_prompt):
    """
    Change image background using image conditioning.
    """
    try:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
        
        # Model ID for Nova Canvas
        model_id = 'amazon.nova-canvas-v1:0'

        # Read and prepare input image
        with Image.open(image_path) as img:
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize to supported dimensions if needed
            width = height = 1024  # or 512 based on your needs
            #img = img.resize((width, height))
            
            # Convert to bytes and encode
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            input_image = base64.b64encode(img_byte_arr).decode('utf8')
        
        background_prompt = "person in the photo with '" + background_prompt + "'"
        print (background_prompt)
        # Prepare request body
        body = json.dumps({
     
            "taskType": "OUTPAINTING",
             "outPaintingParams": {
                "text": background_prompt,
                "negativeText": "bad quality, low resolution, cartoon",
                "image": input_image,
                "maskPrompt": "person",
                "outPaintingMode": "PRECISE",
            },
            "imageGenerationConfig": {
                "numberOfImages": 1,
                #"height": height,
                #"width": width,
                "cfgScale": 8.0,
                "seed": random.randint(0, 100000)
            }
        })

        # Generate new image
        image_bytes = generate_image(model_id=model_id, body=body)
        
        # Save and show result
        output_image = Image.open(io.BytesIO(image_bytes))
        output_file = "output_background_changed.png"
        output_image.save(output_file)
        output_image.show()
        
        logging.info(f"Image saved as {output_file}")

    except FileNotFoundError:
        logging.error(f"Image file not found: {image_path}")
    except ClientError as err:
        logging.error(f"AWS service error: {err.response['Error']['Message']}")
    except ImageError as err:
        logging.error(err.message)
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Change image background using Amazon Nova Canvas Model")
    parser.add_argument("image_path", type=str, help="Path to the input image")
    parser.add_argument("background_prompt", type=str, 
                       help="Description of the desired background")
    
    args = parser.parse_args()
    change_background(args.image_path, args.background_prompt)

if __name__ == "__main__":
    main()
