"""
Processing state management for real-time progress tracking in Streamlit UI.

This module provides a state manager that handles progress tracking for the 
Processing tab, enabling real-time updates during document ingestion and reconciliation.
"""

from __future__ import annotations
import streamlit as st
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class ProcessingState:
    """State container for processing progress tracking."""
    is_processing: bool = False
    show_processing_tab: bool = False
    current_phase: str = ""  # "ingestion", "reconciliation", "complete"
    progress_messages: List[str] = field(default_factory=list)
    current_file: Optional[str] = None
    files_processed: int = 0
    total_files: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    def reset(self):
        """Reset all state to initial values."""
        self.is_processing = False
        self.show_processing_tab = False
        self.current_phase = ""
        self.progress_messages = []
        self.current_file = None
        self.files_processed = 0
        self.total_files = 0
        self.start_time = None
        self.end_time = None
    
    def start_processing(self):
        """Initialize processing state."""
        self.reset()
        self.is_processing = True
        self.show_processing_tab = True
        self.start_time = datetime.now()
        self.add_message("🚀 Starting document processing...")
    
    def finish_processing(self):
        """Finalize processing state."""
        self.is_processing = False
        self.current_phase = "complete"
        self.end_time = datetime.now()
        if self.start_time:
            duration = (self.end_time - self.start_time).total_seconds()
            self.add_message(f"🎉 Processing completed in {duration:.1f} seconds")
    
    def add_message(self, message: str):
        """Add a progress message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.progress_messages.append(f"[{timestamp}] {message}")
        
        # Keep only last 50 messages to prevent memory bloat
        if len(self.progress_messages) > 50:
            self.progress_messages = self.progress_messages[-50:]
    
    def update_progress(self, message: str, processed: int, total: int, current_file: Optional[str] = None):
        """Update progress tracking information."""
        self.files_processed = processed
        self.total_files = total
        self.current_file = current_file
        self.add_message(message)
    
    def get_progress_percentage(self) -> float:
        """Calculate progress as percentage."""
        if self.total_files == 0:
            return 0.0
        return (self.files_processed / self.total_files) * 100.0


def get_processing_state() -> ProcessingState:
    """Get or initialize the processing state from Streamlit session state."""
    if 'processing_state' not in st.session_state:
        st.session_state.processing_state = ProcessingState()
    return st.session_state.processing_state


def create_progress_callback(ui_containers=None):
    """Create a progress callback function that updates both session state and UI in real-time."""
    state = get_processing_state()
    
    def progress_callback(message: str, processed: int, total: int, current_file: Optional[str] = None):
        """Progress callback function for ingest and reconcile operations."""
        state.update_progress(message, processed, total, current_file)
        
        # Update UI in real-time if containers are provided
        if ui_containers:
            try:
                # Update progress bar
                if total > 0:
                    progress_value = processed / total
                    ui_containers['progress_bar'].progress(progress_value)
                
                # Update status text
                progress_pct = (processed / total * 100) if total > 0 else 0
                status_text = f"**Progress:** {progress_pct:.1f}% ({processed}/{total})"
                if current_file:
                    status_text += f"  \n**Current:** {current_file}"
                if state.current_phase:
                    status_text += f"  \n**Phase:** {state.current_phase.title()}"
                ui_containers['status'].markdown(status_text)
                
                # Simple log display (no nested scrollable container)
                if state.progress_messages and 'log' in ui_containers:
                    # Get recent messages for simple display
                    recent_messages = state.progress_messages[-10:]  # Show last 10 messages
                    
                    # Create simple text display
                    log_text = ""
                    for msg in recent_messages:
                        # Add simple formatting
                        if "✅" in msg:
                            log_text += f"🟢 {msg}\n"
                        elif "❌" in msg:
                            log_text += f"🔴 {msg}\n"
                        elif "🔍" in msg:
                            log_text += f"🔵 {msg}\n"
                        elif "🔄" in msg:
                            log_text += f"🟡 {msg}\n"
                        else:
                            log_text += f"⚪ {msg}\n"
                    
                    # Display as simple text (no additional scroll container)
                    ui_containers['log'].text(log_text)
                    
            except Exception as e:
                # Ignore UI update errors to prevent breaking the processing
                print(f"UI update error: {e}")
    
    return progress_callback


def render_processing_tab():
    """Render the Processing tab content with real-time progress."""
    state = get_processing_state()
    
    if not state.show_processing_tab:
        st.info("Processing tab will appear when you click 'Ingest & Reconcile'")
        return
    
    # Header with progress info
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        if state.is_processing:
            st.subheader("🔄 Processing Documents...")
        else:
            st.subheader("✅ Processing Complete")
    
    with col2:
        if state.total_files > 0:
            progress_pct = state.get_progress_percentage()
            st.metric("Progress", f"{progress_pct:.1f}%")
    
    with col3:
        if state.total_files > 0:
            st.metric("Files", f"{state.files_processed}/{state.total_files}")
    
    # Progress bar
    if state.total_files > 0:
        progress_value = state.files_processed / state.total_files
        st.progress(progress_value)
    
    # Current phase and file info
    if state.current_phase:
        st.caption(f"Phase: {state.current_phase.title()}")
    
    if state.current_file:
        st.caption(f"Current file: {state.current_file}")
    
    # Enhanced Processing Log Display
    st.subheader("📋 Processing Log")
    
    if state.progress_messages:
        # Create scrollable log with full messages - show more since container is larger
        log_messages = state.progress_messages[-100:]  # Show last 100 messages
        
        # Create HTML for a full-height scrollable div with unique ID
        import time
        tab_unique_id = f"processing-tab-log-{int(time.time() * 1000)}"
        log_html = f"""
        <div id="{tab_unique_id}" style="
            height: 80vh; 
            min-height: 600px;
            overflow-y: auto; 
            border: 1px solid #444; 
            border-radius: 8px; 
            padding: 15px; 
            background-color: #0e1117;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            line-height: 1.4;
            scrollbar-width: thin;
            scroll-behavior: smooth;
            position: relative;
        ">
        """
        
        for msg in log_messages:
            # Color code and format different message types
            if "✅ Processed" in msg:
                color = "#28a745"  # Green for success
                icon = "✅"
            elif "❌" in msg:
                color = "#dc3545"  # Red for errors
                icon = "❌"
            elif "🔍 Reconciling" in msg:
                color = "#17a2b8"  # Blue for reconciliation
                icon = "🔍"
            elif "🔄" in msg:
                color = "#ffc107"  # Yellow for processing
                icon = "🔄"
            elif "Skipping" in msg:
                color = "#6c757d"  # Gray for skipped
                icon = "⏭️"
            elif "complete" in msg.lower():
                color = "#28a745"  # Green for completion
                icon = "🎉"
            else:
                color = "#fafafa"  # Default white
                icon = "📝"
                
            # Format the message with proper spacing and full text
            clean_msg = msg.replace("[", "").replace("]", "")  # Remove timestamp brackets
            log_html += f'''
            <div style="
                color: {color}; 
                margin: 3px 0; 
                padding: 2px 0;
                word-wrap: break-word;
                white-space: pre-wrap;
            ">{clean_msg}</div>
            '''
        
        log_html += "</div>"
        
        # Smart auto-scroll that respects manual scrolling
        scroll_function = f"scrollTabToBottom_{tab_unique_id.replace('-', '_')}"
        log_html += f"""
        <script>
        (function() {{
            const logDiv = document.getElementById('{tab_unique_id}');
            if (!logDiv) return;
            
            let userIsScrolling = false;
            let lastScrollTop = 0;
            let autoScrollEnabled = true;
            
            // Function to check if user is near bottom (within 50px)
            function isNearBottom() {{
                return logDiv.scrollTop >= (logDiv.scrollHeight - logDiv.clientHeight - 50);
            }}
            
            // Function to scroll to bottom
            function {scroll_function}() {{
                if (autoScrollEnabled && !userIsScrolling) {{
                    logDiv.scrollTop = logDiv.scrollHeight;
                }}
            }}
            
            // Detect manual scrolling
            logDiv.addEventListener('scroll', function() {{
                const currentScrollTop = logDiv.scrollTop;
                
                // If user scrolled up from bottom, disable auto-scroll
                if (currentScrollTop < lastScrollTop && !isNearBottom()) {{
                    userIsScrolling = true;
                    autoScrollEnabled = false;
                    
                    // Show scroll-to-bottom indicator
                    showScrollButton();
                }}
                // If user scrolled back to near bottom, re-enable auto-scroll
                else if (isNearBottom()) {{
                    userIsScrolling = false;
                    autoScrollEnabled = true;
                    hideScrollButton();
                }}
                
                lastScrollTop = currentScrollTop;
                
                // Reset scrolling detection after a short delay
                setTimeout(() => {{
                    userIsScrolling = false;
                }}, 150);
            }});
            
            // Create scroll-to-bottom button
            function showScrollButton() {{
                let scrollBtn = document.getElementById('scroll-to-bottom-{tab_unique_id}');
                if (!scrollBtn) {{
                    scrollBtn = document.createElement('div');
                    scrollBtn.id = 'scroll-to-bottom-{tab_unique_id}';
                    scrollBtn.innerHTML = '⬇️ New messages';
                    scrollBtn.style.cssText = `
                        position: fixed;
                        bottom: 20px;
                        right: 20px;
                        background: #1f77b4;
                        color: white;
                        padding: 10px 15px;
                        border-radius: 20px;
                        cursor: pointer;
                        z-index: 1000;
                        font-size: 12px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.3);
                        animation: fadeIn 0.3s ease-in;
                    `;
                    
                    scrollBtn.addEventListener('click', function() {{
                        autoScrollEnabled = true;
                        userIsScrolling = false;
                        {scroll_function}();
                        hideScrollButton();
                    }});
                    
                    document.body.appendChild(scrollBtn);
                }}
                scrollBtn.style.display = 'block';
            }}
            
            function hideScrollButton() {{
                const scrollBtn = document.getElementById('scroll-to-bottom-{tab_unique_id}');
                if (scrollBtn) {{
                    scrollBtn.style.display = 'none';
                }}
            }}
            
            // Initial scroll attempts
            setTimeout({scroll_function}, 100);
            setTimeout({scroll_function}, 300);
            
            // Observer for new content - only auto-scroll if enabled
            const observer = new MutationObserver(() => {{
                if (autoScrollEnabled && isNearBottom()) {{
                    setTimeout({scroll_function}, 50);
                }}
            }});
            observer.observe(logDiv, {{ 
                childList: true, 
                subtree: true,
                characterData: true 
            }});
            
            // Clean up button when page changes
            window.addEventListener('beforeunload', function() {{
                hideScrollButton();
            }});
        }})();
        </script>
        """
        
        st.html(log_html)
    else:
        st.info("No processing messages yet.")
    
    # Close button (only show when processing is complete)
    if not state.is_processing and state.current_phase == "complete":
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🔒 Close Processing Tab", type="secondary", use_container_width=True):
                state.show_processing_tab = False
                st.rerun()


def create_realtime_processing_ui():
    """Create real-time processing UI elements that can be updated during processing."""
    state = get_processing_state()
    
    # Create placeholders for real-time updates
    header_placeholder = st.empty()
    progress_placeholder = st.empty()
    metrics_placeholder = st.empty()
    status_placeholder = st.empty()
    log_placeholder = st.empty()
    
    # Store placeholders in session state for access during processing
    if 'ui_placeholders' not in st.session_state:
        st.session_state.ui_placeholders = {}
    
    st.session_state.ui_placeholders.update({
        'header': header_placeholder,
        'progress': progress_placeholder, 
        'metrics': metrics_placeholder,
        'status': status_placeholder,
        'log': log_placeholder
    })
    
    return {
        'header': header_placeholder,
        'progress': progress_placeholder,
        'metrics': metrics_placeholder,
        'status': status_placeholder,
        'log': log_placeholder
    }


def update_realtime_ui():
    """Update the real-time UI elements with current processing state."""
    if 'ui_placeholders' not in st.session_state:
        return
        
    state = get_processing_state()
    placeholders = st.session_state.ui_placeholders
    
    # Update header
    if state.is_processing:
        placeholders['header'].subheader("🔄 Processing Documents...")
    else:
        placeholders['header'].subheader("✅ Processing Complete")
    
    # Update progress bar
    if state.total_files > 0:
        progress_value = state.files_processed / state.total_files
        placeholders['progress'].progress(progress_value)
    
    # Update metrics
    col1, col2, col3 = placeholders['metrics'].columns([1, 1, 1])
    with col1:
        if state.total_files > 0:
            progress_pct = state.get_progress_percentage()
            st.metric("Progress", f"{progress_pct:.1f}%")
    
    with col2:
        if state.total_files > 0:
            st.metric("Files", f"{state.files_processed}/{state.total_files}")
    
    with col3:
        if state.current_phase:
            st.metric("Phase", state.current_phase.title())
    
    # Update status
    status_info = []
    if state.current_file:
        status_info.append(f"**Current file:** {state.current_file}")
    if state.current_phase:
        status_info.append(f"**Phase:** {state.current_phase.title()}")
    
    if status_info:
        placeholders['status'].markdown("  \n".join(status_info))
    
    # Update log
    if state.progress_messages:
        log_text = "**📋 Processing Log:**\n\n"
        # Show last 15 messages
        for message in reversed(state.progress_messages[-15:]):
            log_text += f"```\n{message}\n```\n"
        placeholders['log'].markdown(log_text)


def get_tab_labels() -> List[str]:
    """Get tab labels, conditionally including Processing tab."""
    state = get_processing_state()
    base_tabs = ["Overview", "Exceptions", "Vendor Insights", "Audit Trail", "Backup Management"]
    
    if state.show_processing_tab:
        # Insert Processing tab as second tab (after Overview)
        return ["Overview", "🔄 Processing", "Exceptions", "Vendor Insights", "Audit Trail", "Backup Management"]
    else:
        return base_tabs


def get_tab_mapping() -> Dict[str, int]:
    """Get mapping of tab names to indices based on current state."""
    state = get_processing_state()
    
    if state.show_processing_tab:
        return {
            "overview": 0,
            "processing": 1,
            "exceptions": 2,
            "vendor_insights": 3,
            "audit_trail": 4,
            "backup_management": 5
        }
    else:
        return {
            "overview": 0,
            "exceptions": 1,
            "vendor_insights": 2,
            "audit_trail": 3,
            "backup_management": 4
        }
