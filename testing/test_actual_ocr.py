import os
import base64
import time
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from dotenv import load_dotenv

load_dotenv()

DI_ENDPOINT = os.getenv("AZURE_DOC_INTEL_ENDPOINT", "")
DI_KEY = os.getenv("AZURE_DOC_INTEL_KEY", "")

print(f"Testing actual OCR call that's hanging...")

# Create a tiny test image (1x1 pixel PNG in base64)
tiny_png_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

try:
    client = DocumentIntelligenceClient(DI_ENDPOINT, AzureKeyCredential(DI_KEY))
    print("Client created successfully")
    
    print("Testing with tiny PNG...")
    start_time = time.time()
    
    # Try the exact same call that's hanging
    poller = client.begin_analyze_document(
        model_id="prebuilt-layout",
        body={"base64Source": tiny_png_b64},
        pages="1",
        output_content_format="markdown",
        string_index_type="unicodeCodePoint",
        locale=None
    )
    
    print(f"Poller created in {time.time() - start_time:.1f}s")
    print("Waiting for result...")
    
    wait_start = time.time()
    result = poller.result()
    wait_time = time.time() - wait_start
    
    print(f"SUCCESS: OCR completed in {wait_time:.1f}s")
    print(f"Content length: {len(result.content or '')}")
    
except Exception as e:
    elapsed = time.time() - start_time
    print(f"ERROR after {elapsed:.1f}s: {e}")
