import base64
import io
import json
import logging
import boto3
from PIL import Image
from botocore.exceptions import ClientError

def main():
    """
    Entrypoint for Amazon Titan Image Background Removal example.
    """
    try:
        logging.basicConfig(level=logging.INFO,
                            format="%(levelname)s: %(message)s")

        model_id = 'amazon.nova-canvas-v1:0'

        # Read image from file and encode it as a base64 string.
        try:
            with open("demo2.jpeg", "rb") as image_file:
                input_image = base64.b64encode(image_file.read()).decode('utf8')
        except FileNotFoundError:
            logger.error("Image file not found at the specified path.")
            return

        # Ensure the request body conforms to the expected format.
        body = json.dumps({
            "taskType": "BACKGROUND_REMOVAL",
            "backgroundRemovalParams": {
                "image": input_image
            }
        })

        image_bytes = remove_background(model_id=model_id, body=body)

        # Save the output image with transparent background
        output_image = Image.open(io.BytesIO(image_bytes))
        output_image.save("output_image.png", format="PNG")
        output_image.show()

    except ClientError as err:
        message = err.response["Error"]["Message"]
        logger.error("A client error occurred: %s", message)
        print("A client error occurred: " + format(message))
    except ImageError as err:
        logger.error(err.message)
        print(err.message)
    else:
        print(f"Finished background removal using Amazon Nova Canvas image generation model {model_id}.")

def remove_background(model_id, body):
    """
    Remove the background from an image using Amazon Nova Canvas image generation model.

    Args:
        model_id (str): The model ID to use.
        body (str): The request body to use.

    Returns:
        image_bytes (bytes): The processed image with the background removed.
    """
    logger.info("Removing background with Amazon Nova Canvas image generation model %s", model_id)

    try:
        bedrock = boto3.client(service_name='bedrock-runtime')
    except ClientError as err:
        logger.error("Failed to create Bedrock client: %s", err)
        raise

    accept = "application/json"
    content_type = "application/json"

    try:
        response = bedrock.invoke_model(
            body=body, modelId=model_id, accept=accept, contentType=content_type
        )
        response_body = json.loads(response.get("body").read())
    except KeyError as err:
        logger.error("Malformed API response: %s", err)
        raise ImageError("Malformed API response.")

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

class ImageError(Exception):
    """Custom exception for errors returned by Amazon Nova Canvas image generation model"""

    def __init__(self, message):
        self.message = message

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    main()
