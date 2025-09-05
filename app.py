
import os, json, sqlite3, hashlib
from pathlib import Path
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

from pipeline.db import connect
from pipeline.ingest import ingest_folder
from pipeline.reconcile import reconcile
from pipeline.insights import kpis, exceptions_table, vendor_summary, audit_for_invoice
from pipeline.sample_data import generate as generate_sample, generate_enhanced
from pipeline.reset_manager import ResetManager
from pipeline.processing_state import (
    get_processing_state, 
    create_progress_callback, 
    render_processing_tab, 
    get_tab_labels, 
    get_tab_mapping
)

load_dotenv()

st.set_page_config(page_title="EMA 3-Way Match Demo", layout="wide")

st.title("Enterprise Machine Assistant — Procurement 3‑Way Match Demo")
st.caption("Ingest → Classify → Extract → Reconcile → Insights")

DB_PATH = Path("ema_demo.sqlite")
DATA_RAW = Path("data_lake/raw")
CONFIG_PATH = Path("config.json")

with open(CONFIG_PATH) as f:
    CONFIG = json.load(f)

# Initialize reset manager
reset_manager = ResetManager(DB_PATH, DATA_RAW, CONFIG_PATH)

# Sidebar controls
st.sidebar.header("Controls")

# Data Generation
col1, col2 = st.sidebar.columns(2)

with col1:
    if st.button("Basic Sample Data", help="Generate 15 standard document sets"):
        generate_sample(DATA_RAW, n_sets=15)
        st.success("✅ Basic sample data generated!")

with col2:
    if st.button("Enhanced Random Data", help="Generate 30 random files with missing docs, variances & mixed formats"):
        try:
            files = generate_enhanced(DATA_RAW, n_sets=10)  # 10 sets should generate ~30 files
            st.success(f"🎲 Generated {len(files)} random files!")
            st.caption("Includes missing docs, price/qty variances, duplicates, and mixed formats (TXT/PDF/OCR)")
        except Exception as e:
            st.error(f"Generation failed: {e}")
            # Fallback to basic generation
            generate_sample(DATA_RAW, n_sets=10)
            st.info("Used basic generation as fallback")

# System Status
st.sidebar.header("System Status")
status = reset_manager.get_system_status()

# Show clearer status information
st.sidebar.metric("Raw Files", status["data_files_count"], help="Document files in data_lake/raw waiting to be processed")

if status["database_exists"]:
    # Check if database has actual data
    conn = connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM invoices")
        invoice_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM purchase_orders") 
        po_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM grns")
        grn_count = cursor.fetchone()[0]
        conn.close()
        
        total_records = invoice_count + po_count + grn_count
        st.sidebar.metric("Processed Records", total_records, help="Records extracted and stored in database")
    except:
        conn.close()
        st.sidebar.metric("Processed Records", "?", help="Database exists but structure unknown")
else:
    st.sidebar.metric("Processed Records", 0, help="No database found - run 'Ingest & Reconcile'")

st.sidebar.metric("Backups", status["backups_count"])

# Processing Controls
st.sidebar.header("Processing")
qty_tol = st.sidebar.number_input("Qty tolerance (units)", value=float(CONFIG["qty_tolerance_units"]), step=1.0)
price_tol = st.sidebar.number_input("Price tolerance (%)", value=float(CONFIG["price_tolerance_pct"]), step=0.5)
use_openai = os.getenv("USE_OPENAI", "false").lower() == "true"
st.sidebar.write(f"OpenAI parsing: {'ON' if use_openai else 'OFF'}")

# OCR Status
try:
    from pipeline.pdf_processor import OCR_AVAILABLE
    ocr_status = "ON" if OCR_AVAILABLE else "OFF"
    st.sidebar.write(f"OCR processing: {ocr_status}")
except (ImportError, NameError):
    st.sidebar.write("OCR processing: OFF")
    OCR_AVAILABLE = False

st.sidebar.write("Supported formats: TXT, PDF, JPG, PNG")
try:
    if OCR_AVAILABLE:
        st.sidebar.caption("📷 OCR-powered: handles scanned documents!")
except NameError:
    pass  # OCR_AVAILABLE not defined, skip the caption

if st.sidebar.button("Ingest & Reconcile", type="primary"):
    # Initialize processing state
    processing_state = get_processing_state()
    processing_state.start_processing()
    
    # Create real-time UI containers in the main area
    st.markdown("### 🔄 Processing Documents...")
    
    # Create UI containers for real-time updates
    progress_container = st.empty()
    status_container = st.empty()  
    log_container = st.empty()
    
    ui_containers = {
        'progress_bar': progress_container,
        'status': status_container,
        'log': log_container
    }
    
    # Create progress callback with UI containers
    progress_callback = create_progress_callback(ui_containers)
    
    try:
        conn = connect(DB_PATH)
        
        # Set ingestion phase
        processing_state.current_phase = "ingestion"
        status_container.markdown("**Phase:** Ingestion starting...")
        
        ing, skip, errors = ingest_folder(conn, DATA_RAW, progress_callback)
        
        # Set reconciliation phase  
        processing_state.current_phase = "reconciliation"
        status_container.markdown("**Phase:** Reconciliation starting...")
        
        reconcile(conn, qty_tol_units=qty_tol, price_tol_pct=price_tol, progress_callback=progress_callback)
        
        # Finish processing
        processing_state.finish_processing()
        
        # Show final status
        progress_container.success("✅ Processing Complete!")
        status_container.markdown(f"**✅ Completed:** {ing} files processed, {skip} skipped, {errors} errors")
        
        # Add dismiss button
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🔒 Dismiss Processing View", type="secondary", width='stretch'):
                progress_container.empty()
                status_container.empty()  
                log_container.empty()
                st.rerun()
        
        # Show summary in sidebar
        if errors > 0:
            st.sidebar.warning(f"Processed: {ing} files, Skipped: {skip}, Errors: {errors}")
        else:
            st.sidebar.success(f"✅ Processed: {ing} files, Skipped: {skip}")
            
        conn.close()
        
        # Don't auto-clear - let user dismiss manually
        # Refresh to show updated metrics and processing tab
        st.rerun()
        
    except Exception as e:
        processing_state.add_message(f"❌ Processing failed: {e}")
        processing_state.finish_processing()
        progress_container.error(f"❌ Processing failed: {e}")
        status_container.markdown(f"**Error:** {e}")
        st.sidebar.error(f"Processing failed: {e}")
        if 'conn' in locals():
            conn.close()

# Reset Options - moved to bottom in boxed section
st.sidebar.markdown("---")
with st.sidebar.container():
    st.markdown("### 🔄 Reset Options")
    
    reset_type = st.selectbox(
        "Reset Type",
        ["Full Reset", "Database Only", "Sample Data Only", "Config Only"],
        help="Choose what to reset"
    )
    
    create_backup = st.checkbox("Create backup before reset", value=True)
    
    if st.button("🔄 Reset System", type="secondary"):
        with st.spinner("Resetting system..."):
            try:
                if reset_type == "Full Reset":
                    results = reset_manager.full_reset(create_backup=create_backup)
                    if results["errors"]:
                        st.error(f"Reset completed with errors: {results['errors']}")
                    else:
                        st.success("Full system reset completed!")
                        if results["backup_created"]:
                            st.info(f"Backup created: {results['backup_created']}")
                
                elif reset_type == "Database Only":
                    tables, records = reset_manager.reset_database()
                    st.success(f"Database reset: {tables} tables, {records} records cleared")
                
                elif reset_type == "Sample Data Only":
                    files_removed = reset_manager.reset_sample_data(regenerate=True)
                    st.success(f"Sample data reset: {files_removed} files removed and regenerated")
                
                elif reset_type == "Config Only":
                    if reset_manager.reset_config():
                        st.success("Config reset to defaults")
                    else:
                        st.error("Failed to reset config")
                
                # Refresh the page to show updated state
                st.rerun()
                
            except Exception as e:
                st.error(f"Reset failed: {e}")

# Main tabs - dynamic based on processing state
tab_labels = get_tab_labels()
tab_mapping = get_tab_mapping()

if len(tab_labels) == 6:  # Processing tab is visible
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(tab_labels)
    tabs = [tab1, tab2, tab3, tab4, tab5, tab6]
else:  # No processing tab
    tab1, tab2, tab3, tab4, tab5 = st.tabs(tab_labels)
    tabs = [tab1, tab2, tab3, tab4, tab5]

# Overview Tab
with tabs[tab_mapping["overview"]]:
    if DB_PATH.exists():
        conn = connect(DB_PATH)
        metrics = kpis(conn)
        
        # Document Processing Overview
        st.subheader("📊 Document Processing Overview")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total Documents", metrics["total_documents"], help="All documents processed (POs, Invoices, GRNs)")
        
        with col2:
            st.metric("Total Invoices", metrics["total_invoices"], help="Invoices available for 3-way matching")
        
        with col3:
            st.metric("Matched", metrics["matched"], help="Invoices that passed 3-way match validation")
        
        with col4:
            st.metric("Match Rate %", f"{metrics['match_rate']:.1f}", help="Percentage of invoices that matched successfully")
        
        with col5:
            # OCR Processing Stats
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_docs,
                        SUM(CASE WHEN requires_ocr = 1 THEN 1 ELSE 0 END) as ocr_docs,
                        AVG(CASE WHEN requires_ocr = 1 THEN ocr_confidence ELSE NULL END) as avg_ocr_confidence
                    FROM documents
                """)
                ocr_stats = cursor.fetchone()
                if ocr_stats and ocr_stats[0] > 0:
                    ocr_count = ocr_stats[1] or 0
                    ocr_confidence = ocr_stats[2] or 0
                    st.metric("OCR Documents", f"{ocr_count}/{ocr_stats[0]}", 
                             help="Documents processed using OCR technology")
                    if ocr_count > 0:
                        st.caption(f"Avg OCR confidence: {ocr_confidence:.1f}%")
                else:
                    st.metric("OCR Documents", "0/0", help="No OCR processing detected")
            except Exception as e:
                st.metric("OCR Documents", "N/A", help="OCR stats unavailable")
        
        # Document Type Breakdown
        st.subheader("📋 Document Type Distribution")
        if metrics["doc_type_counts"]:
            doc_type_data = []
            for doc_type, count in metrics["doc_type_counts"].items():
                doc_type_data.append({
                    "Document Type": doc_type,
                    "Count": count,
                    "Percentage": f"{(count / metrics['total_documents'] * 100):.1f}%"
                })
            
            doc_df = pd.DataFrame(doc_type_data)
            
            # Create two columns for chart and table
            chart_col, table_col = st.columns([1, 1])
            
            with chart_col:
                # Create a simple bar chart
                chart_data = doc_df.set_index("Document Type")["Count"]
                st.bar_chart(chart_data, use_container_width=True)
            
            with table_col:
                st.dataframe(doc_df, width='stretch', hide_index=True)
        else:
            st.write("No document data available. Click 'Ingest & Reconcile' to process documents.")
        
        # Invoice Reconciliation Status
        st.subheader("🔍 Invoice Reconciliation Status")
        if metrics["by_status"]:
            status_data = []
            for status, count in metrics["by_status"].items():
                status_data.append({
                    "Status": status,
                    "Count": count,
                    "Percentage": f"{(count / metrics['total_invoices'] * 100):.1f}%" if metrics['total_invoices'] > 0 else "0%"
                })
            
            status_df = pd.DataFrame(status_data)
            st.dataframe(status_df, width='stretch', hide_index=True)
        else:
            st.write("No reconciliation data available. Click 'Ingest & Reconcile' to process documents.")
        
        # OCR Processing Breakdown
        st.subheader("🔍 OCR Processing Breakdown")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    processing_method,
                    COUNT(*) as count,
                    AVG(ocr_confidence) as avg_confidence,
                    file_type
                FROM documents 
                GROUP BY processing_method, file_type
                ORDER BY count DESC
            """)
            ocr_breakdown = cursor.fetchall()
            
            if ocr_breakdown:
                ocr_data = []
                for method, count, confidence, file_type in ocr_breakdown:
                    ocr_data.append({
                        "Processing Method": method or "unknown",
                        "File Type": file_type or "unknown", 
                        "Count": count,
                        "Avg Confidence": f"{confidence:.1f}%" if confidence else "N/A"
                    })
                
                ocr_df = pd.DataFrame(ocr_data)
                st.dataframe(ocr_df, width='stretch', hide_index=True)
            else:
                st.write("No processing data available.")
        except Exception as e:
            st.write("OCR breakdown unavailable.")
        
        conn.close()
    else:
        st.info("No database found. Click 'Ingest & Reconcile' to start processing documents.")

# Processing Tab (when visible)
if "processing" in tab_mapping:
    with tabs[tab_mapping["processing"]]:
        render_processing_tab()

# Exceptions Tab  
with tabs[tab_mapping["exceptions"]]:
    if DB_PATH.exists():
        conn = connect(DB_PATH)
        df = exceptions_table(conn)
        if not df.empty:
            st.write("Filter by status:")
            statuses = st.multiselect("Status", sorted(df["status"].unique()), default=list(sorted(df["status"].unique())))
            st.dataframe(df[df["status"].isin(statuses)], width='stretch')
        else:
            st.info("No exceptions found. Click 'Ingest & Reconcile' to process documents.")
        conn.close()
    else:
        st.info("No database found. Click 'Ingest & Reconcile' to start processing documents.")

# Vendor Insights Tab
with tabs[tab_mapping["vendor_insights"]]:
    if DB_PATH.exists():
        conn = connect(DB_PATH)
        vs = vendor_summary(conn)
        if not vs.empty:
            st.dataframe(vs, width='stretch')
        else:
            st.info("No vendor data found. Click 'Ingest & Reconcile' to process documents.")
        conn.close()
    else:
        st.info("No database found. Click 'Ingest & Reconcile' to start processing documents.")

# Audit Trail Tab
with tabs[tab_mapping["audit_trail"]]:
    invoice_id = st.text_input("Invoice Number to audit (e.g., INV-1000-1)")
    if invoice_id:
        if DB_PATH.exists():
            conn = connect(DB_PATH)
            audit = audit_for_invoice(conn, invoice_id)
            conn.close()
            if audit:
                st.write(f"**Source file**: `{audit['source_path']}`")
                st.json(audit["parsed_json"])
            else:
                st.warning("No audit data found for that invoice.")
        else:
            st.info("No database found. Click 'Ingest & Reconcile' to start processing documents.")

# Backup Management Tab  
with tabs[tab_mapping["backup_management"]]:
    st.header("Backup Management")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Available Backups")
        backups = reset_manager.list_backups()
        
        if backups:
            backup_data = []
            for backup in backups:
                backup_data.append({
                    "Name": backup["name"],
                    "Created": backup["created_at"][:19].replace("T", " "),
                    "Database": "✅" if backup["db_exists"] else "❌",
                    "Files": backup["data_files_count"],
                    "Size": f"{Path(backup['path']).stat().st_size / 1024:.1f} KB"
                })
            
            df_backups = pd.DataFrame(backup_data)
            st.dataframe(df_backups, width='stretch')
            
            # Backup actions
            selected_backup = st.selectbox("Select backup for action:", [b["name"] for b in backups])
            
            col_restore, col_delete = st.columns(2)
            with col_restore:
                if st.button("🔄 Restore Backup", type="primary"):
                    with st.spinner("Restoring backup..."):
                        if reset_manager.restore_backup(selected_backup):
                            st.success(f"Restored backup: {selected_backup}")
                            st.rerun()
                        else:
                            st.error("Failed to restore backup")
            
            with col_delete:
                if st.button("🗑️ Delete Backup", type="secondary"):
                    if reset_manager.delete_backup(selected_backup):
                        st.success(f"Deleted backup: {selected_backup}")
                        st.rerun()
                    else:
                        st.error("Failed to delete backup")
        
        else:
            st.info("No backups available. Create a backup using the reset options in the sidebar.")
    
    with col2:
        st.subheader("Create Manual Backup")
        backup_name = st.text_input("Backup name (optional)", placeholder="e.g., demo_state_v1")
        
        if st.button("💾 Create Backup", type="primary"):
            with st.spinner("Creating backup..."):
                try:
                    backup_path = reset_manager.create_backup(backup_name if backup_name else None)
                    st.success(f"Backup created: {backup_path}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to create backup: {e}")
        
        st.subheader("System Information")
        status = reset_manager.get_system_status()
        
        st.metric("Database Status", "✅ Exists" if status["database_exists"] else "❌ Missing")
        st.metric("Database Size", f"{status['database_size'] / 1024:.1f} KB" if status["database_size"] > 0 else "0 KB")
        st.metric("Data Files", status["data_files_count"])
        st.metric("Total Backups", status["backups_count"])
        
        if status["last_modified"]:
            st.caption(f"Last modified: {status['last_modified'][:19].replace('T', ' ')}")

