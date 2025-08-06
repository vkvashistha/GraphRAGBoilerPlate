"""
OpenAI Vision OCR service implementation
"""

import os
import time
from typing import Any, Union
import sys
from pathlib import Path

# Add dotenv for loading environment variables
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

from loguru import logger

# Check if OpenAI is available
try:
    import openai
    from openai import OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available. Install with: pip install openai")

    
# Try to load environment variables from .env file
if DOTENV_AVAILABLE:
    # Find the project root directory (where .env is located)
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent  # Go up one level to project root
    env_path = project_root / ".env"
    
    if env_path.exists():
        logger.info(f"Loading environment variables from {env_path}")
        load_dotenv(dotenv_path=env_path)
    else:
        logger.warning(f".env file not found at {env_path}")
else:
    logger.warning("python-dotenv not installed. Install with: pip install python-dotenv")

# Set default values if environment variables are not set
api_key = os.getenv("OPENAI_API_KEY", "your-api-key-here")
model = os.getenv("OPENAI_MODEL", "gpt-4-vision-preview")

logger.info(f"Using model: {model}")

def extract_text():
    """
    Extract text from a PDF file using OpenAI Vision API.
    
    Returns:
        str: Extracted text from the document
        dict: Metadata about the extraction process
    """
    extracted_text = ""
    metadata = {"service": "openai_vision"}
    start_time = time.time()  # Move start_time outside try block
    
    try:
        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI Vision not available")
            return "", metadata
            
        # Initialize OpenAI client
        client = openai.OpenAI(api_key=api_key)
        logger.info("Extracting text using OpenAI Vision...")

        if not OPENAI_AVAILABLE or not client:
            logger.warning("OpenAI Vision not available or not properly initialized")
            return "", metadata

        # Process content - ensure we have a file path
        file_path = os.path.join(os.path.dirname(__file__), "Dell Pro Max 14 Premium owners manual.pdf")
        logger.info(f"Looking for PDF file at: {file_path}")
            
        # Verify the file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Get optional parameters
        temperature = 0

        # Get custom prompt from kwargs if provided
        custom_prompt = None
        logger.debug(f"Custom prompt: {custom_prompt}")

        # Construct the final prompt
        if custom_prompt:
            # If custom prompt is provided, combine it with OCR instructions
            prompt_text = f"Extract all text from this document and then follow these specific instructions:\n\n{custom_prompt}"
        else:
            # Default OCR prompt
            prompt_text = "Extract all text from this document. Return only the extracted text, nothing else."

        # Determine file type to use appropriate API method
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # For PDF files, use the responses API
        if file_ext == ".pdf":
            logger.debug(f"PDF File path: {file_path}")

            # Create file for PDF
            file = client.files.create(
                file=open(file_path, "rb"),
                purpose="user_data"
            )
            logger.debug(f"PDF file created: {file.id}")
            logger.debug(f"File id: {file.id}")
            
            # Use responses API for PDFs
            response = client.responses.create(
                model=model,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_file",
                                "file_id": file.id,
                            },
                            {
                                "type": "input_text",
                                "text": prompt_text,
                            },
                        ],
                    },
                ],
                temperature=temperature,
            )
            
            # Extract text from response
            extracted_text = response.output_text.strip()

        # Add additional metadata
        metadata.update(
            {
                "model": response.model,
                "id": response.id,
            }
        )

        processing_time = time.time() - start_time

        logger.info(f"OpenAI Vision extraction completed in {processing_time:.2f} seconds")
        logger.info(f"Extracted text length: {len(extracted_text)} characters")
        logger.debug(f"Metadata: {metadata}")
        
        return extracted_text, metadata

    except Exception as e:
        logger.error(f"OpenAI Vision extraction failed: {e}")
        processing_time = time.time() - start_time
        metadata.update({"error": str(e), "processing_time": processing_time})
        return "", metadata  # Return empty string and metadata with error


def main():
    """
    Main function to run the text extraction and save results to a file.
    """
    print("Starting text extraction from PDF...")
    
    # Check if API key is set
    if api_key == "your-api-key-here":
        print("\nError: OpenAI API key is not set. Please set the OPENAI_API_KEY environment variable.")
        print("You can set it temporarily with: $env:OPENAI_API_KEY = 'your-api-key-here'")
        print("Or install python-dotenv and create a .env file in the project root with OPENAI_API_KEY='your-key-here'")
        return
        
    print(f"Using API key: {api_key[:8]}...{api_key[-4:]}")
    print(f"Using model: {model}")
    
    # Extract text from PDF
    extracted_text, metadata = extract_text()
    
    if extracted_text:
        # Create output filename based on current timestamp
        output_filename = f"extracted_text_{int(time.time())}.txt"
        
        # Save extracted text to file
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(extracted_text)
        
        print(f"Extraction successful!")
        print(f"Text saved to: {output_filename}")
        print(f"Extracted {len(extracted_text)} characters")
        print(f"Processing time: {metadata.get('processing_time', 'N/A')} seconds")
    else:
        print("Extraction failed or no text was extracted.")
        print(f"Error: {metadata.get('error', 'Unknown error')}")


if __name__ == "__main__":
    # Install required packages if not already installed
    if not DOTENV_AVAILABLE:
        print("Installing python-dotenv...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "python-dotenv"])
        print("python-dotenv installed. Please run the script again.")
        sys.exit(0)
    
    main()