# Amazon Titan Image / Nova Canvas Background Removal Example

This repository contains an example of using the Amazon Titan V2 / Nova Canvas Image Generator to remove image backgrounds programmatically. By leveraging the Bedrock service, you can perform high-quality background removal at a fraction of the cost of typical image editing apps.

## Features

- **Low-Cost Processing:** Remove image backgrounds for just a few cents using Amazon Bedrock.
- **High Accuracy:** Utilizes the Titan Image V2 / Nova Canvas for professional-grade results.
- **Python Automation:** Includes a Python script for easy integration into your workflows.

## Requirements

- AWS account with permissions to use Amazon Bedrock.
- Python 3.8 or later.
- Required Python libraries (see `requirements.txt`).

## Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/awsdataarchitect/bedrock-examples.git
   cd bedrock-examples
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
3. **Configure AWS credentials:** Ensure your AWS credentials are set up in ~/.aws/credentials or use environment variables.

4. **Run the script:** Replace "demo.jpeg" in the script with your image file path and execute:

Amazon Titan Model Example
   ```bash
   python bedrock_titan_image_bg_remove.py
   ```
Amazon Nova Canvas Model Example
   ```bash
   python bedrock_nova_image_bg_remove.py
   ```
Output: The script generates an output_image.png with a transparent background.

Before: 


![Alt text](./demo2.jpeg?raw=true "Input Image)")

After:

![Alt text](./output_image.png?raw=true "Output Image after BG Removal)")

## Cost Comparison

Compared to apps charging $10-$20 per image, this solution costs just a few cents per operation using Amazon Bedrock's Titan/Nova Canvas model.

## Contributing

Feel free to submit issues, suggest features, or open pull requests.

## License

This project is licensed under the MIT License.