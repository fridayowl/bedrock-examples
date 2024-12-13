import base64
import random
import time

import boto3
from PIL import Image

S3_DESTINATION_BUCKET = "YOUR-S3-BUCKET-NAME"
AWS_REGION = "us-east-1"
MODEL_ID = "amazon.nova-reel-v1:0"
SLEEP_TIME = 30

# Initialize Bedrock client
bedrock_runtime = boto3.client("bedrock-runtime", region_name=AWS_REGION)

# Load the reference image and resize to 1280x720
input_image_path = "vasai_village.jpeg"
output_image_path = "vasai_village_resized.png"

# Resize the image
with Image.open(input_image_path) as img:
    resized_img = img.resize((1280, 720), Image.Resampling.LANCZOS)
    resized_img.save(output_image_path, format="JPEG")

# Encode the resized image to Base64
with open(output_image_path, "rb") as f:
    input_image_bytes = f.read()
    input_image_base64 = base64.b64encode(input_image_bytes).decode("utf-8")

video_prompt = "drone view flying over an ancestral village fronted by an old fort. 4k, photorealistic, shallow depth of field."

# Define video generation parameters
model_input = {
    "taskType": "TEXT_VIDEO",
    "textToVideoParams": {
        "text": video_prompt,
        "images": [{ "format": "png", "source": { "bytes": input_image_base64 } }]
    },
    "videoGenerationConfig": {
        "durationSeconds": 6,
        "fps": 24,
        "dimension": "1280x720",
        "seed": random.randint(0, 2147483648)
    }
}

# Start the video generation task
invocation = bedrock_runtime.start_async_invoke(
    modelId=MODEL_ID,
    modelInput=model_input,
    outputDataConfig={"s3OutputDataConfig": {"s3Uri": f"s3://{S3_DESTINATION_BUCKET}/videos/"}}
)

invocation_arn = invocation["invocationArn"]
s3_prefix = invocation_arn.split('/')[-1]
s3_location = f"s3://{S3_DESTINATION_BUCKET}/videos/{s3_prefix}"

print(f"\nS3 URI: {s3_location}")

# Monitor the task progress
while True:
    response = bedrock_runtime.get_async_invoke(
        invocationArn=invocation_arn
    )
    status = response["status"]
    print(f"Status: {status}")
    if status != "InProgress":
        break
    time.sleep(SLEEP_TIME)

if status == "Completed":
    print(f"\nVideo is ready at {s3_location}/output.mp4")
else:
    print(f"\nVideo generation status: {status}")
