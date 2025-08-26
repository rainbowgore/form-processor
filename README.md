# Form Processor - ביטוח לאומי Form Extractor

A Streamlit web application for extracting and processing data from Israeli National Insurance (ביטוח לאומי) forms using Azure Document Intelligence OCR and GPT-4.

## Features

- Supports multiple file formats: PDF, JPG, JPEG, PNG
- Extracts structured data from form images/documents
- Validates and normalizes extracted data
- Processes both Hebrew and English text
- Provides detailed processing pipeline status
- Generates standardized JSON output

## Key Components

- **OCR Processing**: Uses Azure Document Intelligence for accurate text extraction
- **Data Extraction**: Leverages GPT-4 for intelligent form field extraction
- **Validation Pipeline**: Includes comprehensive data validation and normalization
- **User Interface**: Clean Streamlit interface with real-time processing status

## Extracted Fields

The application extracts the following information from the forms:

- Personal Details:
  - First Name
  - Last Name
  - ID Number
  - Gender
  - Date of Birth
  - Address
  - Phone Numbers (landline and mobile)

- Accident Information:
  - Job Type
  - Date and Time of Injury
  - Accident Location and Address
  - Accident Description
  - Injured Body Part

- Form Details:
  - Signature
  - Form Filling Date
  - Form Receipt Date at Clinic
  - Medical Institution Information

## Dependencies

- Python packages listed in `requirements.txt`
- Azure Document Intelligence
- Azure OpenAI (GPT-4)
- Streamlit

## Configuration

The application requires the following environment variables/configuration:

- Azure Document Intelligence credentials:
  - `DI_ENDPOINT`
  - `DI_KEY`
  
- Azure OpenAI credentials:
  - `AOAI_ENDPOINT`
  - `AOAI_API_KEY`
  - `AOAI_DEPLOYMENT`
  - `AOAI_API_VERSION`

## Usage

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up the required environment variables

3. Run the Streamlit application:
   ```bash
   streamlit run app_streamlit.py
   ```

4. Upload a form (PDF/JPG/PNG) and click "Run Extraction"

5. View the extracted data in JSON format

## Processing Pipeline

1. File Upload: Accepts PDF or image files
2. OCR: Performs text extraction using Azure Document Intelligence
3. Data Extraction: Processes OCR text using GPT-4
4. Validation: Validates and normalizes extracted data
5. Output Generation: Produces structured JSON output

## Data Validation

The system includes comprehensive validation for:
- Israeli ID numbers (including checksum verification)
- Date formats and normalization
- Phone number formatting
- Gender field normalization
- Required field completeness checks
