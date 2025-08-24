import json
import streamlit as st
import time
import traceback
from extractor import extract_pipeline
from config import (
    DI_ENDPOINT, DI_KEY,
    AOAI_ENDPOINT, AOAI_API_KEY,
)

st.set_page_config(page_title="Form Extractor", page_icon="🧾", layout="centered")

st.title("ביטוח לאומי - Field Extractor")

# Hide uploader hint line: "Limit 200MB per file • PDF, JPG, JPEG, PNG"
st.markdown(
    """
    <style>
    div[data-testid="stFileUploaderDropzoneInstructions"] > div:nth-child(2) { display: none !important; }
    div[data-testid="stFileUploaderInstructions"] > div:nth-child(2) { display: none !important; }

    /* Replace first instruction line with custom text */
    div[data-testid="stFileUploaderDropzoneInstructions"] > div:nth-child(1) { 
        visibility: hidden; 
        position: relative;
    }
    div[data-testid="stFileUploaderDropzoneInstructions"] > div:nth-child(1)::after { 
        content: "Upload ביטוח לאומי Form";
        visibility: visible; 
        position: absolute; 
        left: 0; 
        right: 0; 
        text-align: left; 
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("""
Upload a **PDF/JPG** of the National Insurance (ביטוח לאומי) form.
The app will run Azure Document Intelligence OCR and GPT-4o to produce the required JSON.
""")

uploaded = st.file_uploader(
    "Upload a PDF/JPG/PNG",
    type=["pdf", "jpg", "jpeg", "png"],
    label_visibility="visible",
    help="Upload your National Insurance form (PDF or image file)"
)

if uploaded:
    if st.button("Run Extraction", type="primary"):
        file_bytes = uploaded.read()
        
        # Create status container
        st.subheader("Processing Pipeline")
        
        # Initialize status placeholders
        step1_status = st.empty()
        step2_status = st.empty()
        step3_status = st.empty()
        step4_status = st.empty()
        step5_status = st.empty()
        completion_status = st.empty()
        
        try:
            # Show secrets presence (booleans only)
            st.caption(f"DI endpoint: {bool(DI_ENDPOINT)} | key present: {bool(DI_KEY)}")
            st.caption(f"AOAI endpoint: {bool(AOAI_ENDPOINT)} | key present: {bool(AOAI_API_KEY)}")
            # Step 1: File Detection
            step1_status.info("🔍 **Step 1:** Detecting file type and preparing...")
            time.sleep(0.3)  # Brief pause for UX
            
            # Step 2: OCR Processing  
            step1_status.success("✅ **Step 1:** File type detected")
            step2_status.info("📄 **Step 2:** Running OCR (Azure Document Intelligence)...")
            time.sleep(0.3)
            
            # Step 3: LLM Extraction
            step2_status.warning("⏳ **Step 2:** OCR processing in progress...")
            step3_status.info("🤖 **Step 3:** Preparing data extraction with GPT-4o...")
            time.sleep(0.3)
            
            # Step 4: Validation
            step3_status.warning("⏳ **Step 3:** LLM extraction in progress...")
            step4_status.info("✅ **Step 4:** Preparing validation and normalization...")
            time.sleep(0.3)
            
            # Step 5: Fallback Processing
            step4_status.warning("⏳ **Step 4:** Validation in progress...")
            step5_status.info("🔧 **Step 5:** Preparing fallback extraction...")
            
            # Execute the actual pipeline (this is where the real work happens)
            st.write("Calling Azure Document Intelligence…")
            model, report, meta = extract_pipeline(file_bytes)
            st.write("DI returned ", meta.get('ocr_characters', 0), " chars")
            
            # Update all status to completion
            step2_status.success("✅ **Step 2:** OCR completed successfully")
            step3_status.success("✅ **Step 3:** Data extraction completed")
            step4_status.success("✅ **Step 4:** Validation completed")
            step5_status.success("✅ **Step 5:** Pipeline completed successfully")
            
            # Show completion message with stats
            file_type = meta.get('file_type', 'unknown')
            ocr_chars = meta.get('ocr_characters', 0)
            completion_status.success(f"🎉 **Processing Complete!** Processed {file_type.upper()} file with {ocr_chars:,} OCR characters.")
            
            # Add some spacing before results
            st.markdown("---")
            
        except Exception as e:
            # Show error with more detail
            error_details = str(e)
            
            # Try to identify which step failed based on error content
            if "AZURE_DOC_INTEL" in error_details or "OCR" in error_details or "DocumentIntelligence" in error_details:
                step2_status.error(f"❌ **Step 2 Failed:** OCR Error - {error_details}")
                step3_status.empty()
                step4_status.empty()
                step5_status.empty()
            elif "AZURE_OPENAI" in error_details or "LLM" in error_details or "OpenAI" in error_details:
                step2_status.success("✅ **Step 2:** OCR completed successfully")
                step3_status.error(f"❌ **Step 3 Failed:** LLM Error - {error_details}")
                step4_status.empty()
                step5_status.empty()
            elif "validation" in error_details.lower() or "normalize" in error_details.lower():
                step2_status.success("✅ **Step 2:** OCR completed successfully")
                step3_status.success("✅ **Step 3:** Data extraction completed")
                step4_status.error(f"❌ **Step 4 Failed:** Validation Error - {error_details}")
                step5_status.empty()
            else:
                step2_status.success("✅ **Step 2:** OCR completed successfully")
                step3_status.success("✅ **Step 3:** Data extraction completed")
                step4_status.success("✅ **Step 4:** Validation completed")
                step5_status.error(f"❌ **Step 5 Failed:** Pipeline Error - {error_details}")
            
            completion_status.error(f"🚨 **Pipeline Failed:** {error_details}")
            
            # Show debug info in expander
            with st.expander("🔍 Debug Information"):
                st.code(traceback.format_exc())
            
            st.stop()

        # Show Extracted JSON first
        st.subheader("Extracted JSON")
        
        # Create columns for the JSON section only
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Show warnings above JSON in the main area
            warnings_displayed = False
            
            # ID Warning
            if "id_warning" in report:
                st.warning(f"⚠️ ID Warning: {report['id_warning']}")
                warnings_displayed = True
            
            # Phone corrections
            if "phone_corrections" in report and report["phone_corrections"]:
                for correction in report["phone_corrections"]:
                    st.info(f"📱 {correction}")
                    warnings_displayed = True
            
            # Add spacing if warnings were shown
            if warnings_displayed:
                st.write("")
            
            # Editable JSON interface (existing code)
            if "validation_type" in report and report["validation_type"] == "JPG_SPECIFIC":
                # Toggle between view and edit mode
                if "edit_mode" not in st.session_state:
                    st.session_state.edit_mode = False
                
                edit_col1, edit_col2 = st.columns([10, 1])
                
                with edit_col2:
                    if st.button("✏️", help="Edit JSON", key="edit_btn"):
                        st.session_state.edit_mode = not st.session_state.edit_mode
                
                if st.session_state.edit_mode:
                    # Editable JSON
                    edited_json = st.text_area(
                        "Edit JSON:",
                        value=json.dumps(model.model_dump(), indent=2, ensure_ascii=False),
                        height=400,
                        key="json_editor"
                    )
                    
                    col_save, col_cancel = st.columns([1, 1])
                    with col_save:
                        if st.button("💾 Save", key="save_btn"):
                            try:
                                updated_data = json.loads(edited_json)
                                # Update the model with edited data
                                for key, value in updated_data.items():
                                    if hasattr(model, key):
                                        setattr(model, key, value)
                                st.success("✅ JSON updated successfully!")
                                st.session_state.edit_mode = False
                                st.rerun()
                            except json.JSONDecodeError:
                                st.error("❌ Invalid JSON format")
                    
                    with col_cancel:
                        if st.button("❌ Cancel", key="cancel_btn"):
                            st.session_state.edit_mode = False
                            st.rerun()
                else:
                    # Read-only JSON display
                    st.code(json.dumps(model.model_dump(), indent=2, ensure_ascii=False), language="json")
            else:
                # Standard JSON display for non-JPG files
                st.code(json.dumps(model.model_dump(), indent=2, ensure_ascii=False), language="json")
        
        with col2:
            # Keep this empty or add edit button here
            pass

        # Add separator before validation report
        st.markdown("---")
        
        # Validation Report at the bottom
        st.subheader("Validation Report")
        
        # Show completeness first
        st.success(f"Completeness: {report['completeness_percent']}%")
        
        # Then show detailed validation info below
        st.markdown('<p style="color: white; margin: 0 0 0.25rem 0;">might be worth checking the following:</p>', unsafe_allow_html=True)
        st.json(report)