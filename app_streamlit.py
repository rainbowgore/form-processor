import json
import streamlit as st
from extractor import extract_pipeline

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
    "",
    label_visibility="collapsed",
    type=["pdf", "jpg", "jpeg", "png"],
    help="Upload your National Insurance form (PDF or image file)"
)

if uploaded:
    if st.button("Run Extraction", type="primary"):
        with st.spinner("Processing..."):
            file_bytes = uploaded.read()
            model, report, meta = extract_pipeline(file_bytes)

        # Create two columns layout
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("Validation Report")
            
            # Display validation metrics in left column
            if "id_checksum_valid" in report:
                if report["id_checksum_valid"]:
                    st.success("✅ ID checksum valid")
                else:
                    st.error("❌ ID checksum invalid")
            
            # Other validation info in left column
            st.markdown('<p style="color: white; margin: 0 0 0.25rem 0;">might be worth checking the following:</p>', unsafe_allow_html=True)
            st.json(report)

            st.success(f"Completeness: {report['completeness_percent']}%")
        
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
                        value=json.dumps(model.__dict__, indent=2, ensure_ascii=False),
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
                    st.code(json.dumps(model.__dict__, indent=2, ensure_ascii=False), language="json")
            else:
                # Standard JSON display for non-JPG files
                st.code(json.dumps(model.__dict__, indent=2, ensure_ascii=False), language="json")
        
        with col2:
            # Keep this empty or add edit button here
            pass