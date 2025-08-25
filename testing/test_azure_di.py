import os
import time
import signal
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from dotenv import load_dotenv

load_dotenv()

DI_ENDPOINT = os.getenv("AZURE_DOC_INTEL_ENDPOINT", "")
DI_KEY = os.getenv("AZURE_DOC_INTEL_KEY", "")

print(f"Endpoint: {DI_ENDPOINT}")
print(f"Key: {'*' * 10 if DI_KEY else 'MISSING'}")

def timeout_handler(signum, frame):
    raise TimeoutError("API call timed out")

try:
    client = DocumentIntelligenceClient(DI_ENDPOINT, AzureKeyCredential(DI_KEY))
    print("Client created successfully")
    
    # Set a 30-second timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(30)
    
    print("Testing actual API call with timeout...")
    start_time = time.time()
    
    # Try a simple API call (list models or get info)
    try:
        # This is a minimal test - just try to connect
        response = client.get_info()
        print(f"SUCCESS: API responded in {time.time() - start_time:.1f}s")
        print(f"Response: {response}")
    except Exception as api_error:
        print(f"API ERROR after {time.time() - start_time:.1f}s: {api_error}")
    
    signal.alarm(0)  # Cancel timeout
    
except TimeoutError:
    print("TIMEOUT: API call took longer than 30 seconds")
except Exception as e:
    print(f"ERROR: {e}")