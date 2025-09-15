import smtplib
import pandas as pd
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from string import Template
import ssl
import os
import time
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
import json

# UI Libraries
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import tkinter as tk

# Set modern appearance
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class EmailConfig:
    """Email configuration management"""
    def __init__(self):
        self.sender_email = ""
        self.password = ""
        self.your_name = ""
        self.your_designation = ""
        self.smtp_server = ""
        self.smtp_port = 587


class ConnectionPool:
    """SMTP Connection Pool for enterprise-level performance"""
    def __init__(self, config, pool_size=5):
        self.config = config
        self.pool_size = pool_size
        self.connections = Queue(maxsize=pool_size)
        self.lock = threading.Lock()
        self._initialize_pool()
    
    def _initialize_pool(self):
        for _ in range(self.pool_size):
            try:
                context = ssl.create_default_context()
                server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
                server.starttls(context=context)
                server.login(self.config.sender_email, self.config.password)
                self.connections.put(server)
            except Exception as e:
                print(f"Connection pool initialization error: {e}")
                break
    
    def get_connection(self):
        try:
            return self.connections.get(timeout=30)
        except:
            context = ssl.create_default_context()
            server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
            server.starttls(context=context)
            server.login(self.config.sender_email, self.config.password)
            return server
    
    def return_connection(self, connection):
        try:
            connection.noop()
            self.connections.put_nowait(connection)
        except:
            try:
                context = ssl.create_default_context()
                server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
                server.starttls(context=context)
                server.login(self.config.sender_email, self.config.password)
                self.connections.put_nowait(server)
            except:
                pass
    
    def close_all(self):
        while not self.connections.empty():
            try:
                conn = self.connections.get_nowait()
                conn.quit()
            except:
                pass


class EnterpriseBulkEmailSystem:
    def __init__(self):
        self.config = EmailConfig()
        self.data_file = ""
        self.attachment_file = ""
        self.connection_pool = None
        
        # Performance settings
        self.max_workers = 8
        self.batch_size = 50
        self.email_delay = 0.1
        
        # Statistics
        self.total_emails = 0
        self.sent_emails = 0
        self.failed_emails = 0
        self.start_time = None
        
        # UI State
        self.current_view = "dashboard"
        
        # Email providers
        self.email_providers = {
            "Gmail": {"server": "smtp.gmail.com", "port": 587},
            "Office 365": {"server": "smtp.office365.com", "port": 587},
            "Outlook.com": {"server": "smtp-mail.outlook.com", "port": 587},
            "Yahoo": {"server": "smtp.mail.yahoo.com", "port": 587},
            "Custom SMTP": {"server": "", "port": 587}
        }
        
        # Corporate color scheme
        self.colors = {
            "primary": "#1E293B",      # Dark slate
            "secondary": "#334155",    # Slate
            "accent": "#3B82F6",       # Blue
            "success": "#10B981",      # Green
            "warning": "#F59E0B",      # Orange  
            "error": "#EF4444",        # Red
            "bg_primary": "#FFFFFF",   # White
            "bg_secondary": "#F8FAFC", # Light gray
            "bg_tertiary": "#E2E8F0",  # Medium gray
            "text_primary": "#0F172A", # Almost black
            "text_secondary": "#64748B", # Gray
            "text_muted": "#94A3B8",   # Light gray
            "border": "#E2E8F0"        # Border gray
        }
        
        self.fonts = {
            "logo": ("Inter", 28, "bold"),
            "title": ("Inter", 24, "bold"),
            "heading": ("Inter", 18, "bold"),  
            "subheading": ("Inter", 16, "normal"),
            "body": ("Inter", 14, "normal"),
            "body_bold": ("Inter", 14, "bold"),
            "caption": ("Inter", 12, "normal"),
            "small": ("Inter", 11, "normal")
        }
        
        # Cache for performance
        self.audit_table_cache = {}
        self.attachment_data = None
        self.attachment_name = None
        
        # Email template
        self.EMAIL_TEMPLATE = Template("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            line-height: 1.6; 
            margin: 0; 
            padding: 30px;
            background-color: #f8f9fa;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header { 
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
            color: white;
            padding: 30px;
            margin-bottom: 0;
        }
        .content { 
            padding: 30px;
            color: #1f2937;
        }
        .notice-title { 
            color: #dc2626; 
            font-weight: bold; 
            font-size: 18px;
            background: #fef2f2;
            padding: 15px;
            border-left: 4px solid #dc2626;
            margin: 20px 0;
        }
        .signature { 
            background: #f8fafc;
            padding: 25px 30px;
            border-top: 1px solid #e5e7eb;
            margin-top: 0;
        }
        .instructions {
            background: #eff6ff;
            border: 1px solid #bfdbfe;
            border-radius: 6px;
            padding: 20px;
            margin: 20px 0;
        }
        .instructions h4 {
            color: #1e40af;
            margin-top: 0;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 25px 0;
            background: white;
            border-radius: 6px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        th {
            background: #1e293b;
            color: white;
            font-weight: 600;
            padding: 15px 12px;
            text-align: left;
            font-size: 14px;
        }
        td {
            padding: 12px;
            border-bottom: 1px solid #e5e7eb;
            vertical-align: top;
            font-size: 13px;
        }
        tr:hover {
            background: #f8fafc;
        }
        .vendor-column {
            background: #fef3c7 !important;
            font-weight: bold;
            color: #92400e;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2 style="margin: 0; font-size: 24px;">Axis Bank Ltd.</h2>
            <p style="margin: 10px 0 0 0; opacity: 0.9;">External Audit Show Cause Notice</p>
        </div>

        <div class="content">
            <p><strong>Date:</strong> $date</p>
            <p><strong>To:</strong><br>
            <strong>$agency_name</strong><br>
            $agency_address</p>

            <div class="notice-title">
                Subject: $agency_name $agency_location - Show Cause Notice for External Audit Observations: Dated $audit_date
            </div>

            <p><strong>Dear Associate - $agency_person_name,</strong></p>

            <p>We are issuing this notice in your capacity as an empaneled vendor/agency of <strong>Axis Bank Ltd</strong>. This communication serves as a <strong>Show Cause Notice</strong> under the applicable contractual and legal obligations, including but not limited to the terms of engagement executed between your agency and Axis Bank.</p>

            <p>It has come to our attention, pursuant to external audit conducted at your agency (<strong>$agency_location</strong>) on dated <strong>$audit_date</strong>, that we have identified the following observations:</p>

            $audit_table

            <div class="instructions">
                <h4>Instructions for Response:</h4>
                <ul style="margin: 10px 0; padding-left: 20px;">
                    <li>Fill the "Vendor Justifications and Documentations" column for each observation</li>
                    <li>Provide supporting documents as evidence</li>
                    <li>Submit corrective action plan with timelines</li>
                    <li>Send response via email with all supporting documents</li>
                </ul>
                <p style="color: #dc2626; font-weight: bold; margin: 15px 0 5px 0;">
                    ⏰ Response required within 7 working days from the date of this notice.
                </p>
            </div>
        </div>

        <div class="signature">
            <p><strong>Regards,</strong><br>
            <strong>$your_name</strong><br>
            $your_designation<br>
            <strong>Axis Bank Ltd.</strong></p>

            <p style="margin-top: 20px;"><strong>CC to:</strong> $cc_to</p>
            <p><strong>Annexures:</strong> As attached</p>
        </div>
    </div>
</body>
</html>""")

    def create_main_window(self):
        """Create the main application window with corporate design"""
        self.root = ctk.CTk()
        self.root.title("Axis Bank - Enterprise Email System")
        self.root.geometry("1400x900")
        self.root.configure(fg_color=self.colors["bg_secondary"])
        
        # Configure grid
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        
        # Create sidebar and main content area
        self.create_sidebar()
        self.create_main_content_area()
        
        # Initialize with dashboard view
        self.show_dashboard()
        
    def create_sidebar(self):
        """Create the navigation sidebar"""
        self.sidebar = ctk.CTkFrame(self.root, width=280, fg_color=self.colors["primary"])
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.sidebar.grid_propagate(False)
        
        # Logo and title
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=100)
        logo_frame.pack(fill="x", padx=20, pady=(30, 40))
        logo_frame.pack_propagate(False)
        
        # Company logo placeholder
        logo_label = ctk.CTkLabel(
            logo_frame, 
            text="🏦",
            font=("Inter", 32),
            text_color="white"
        )
        logo_label.pack(pady=(10, 5))
        
        title_label = ctk.CTkLabel(
            logo_frame,
            text="Enterprise Mailer",
            font=self.fonts["logo"],
            text_color="white"
        )
        title_label.pack()
        
        subtitle_label = ctk.CTkLabel(
            logo_frame,
            text="Axis Bank Ltd.",
            font=self.fonts["caption"],
            text_color="#94A3B8"
        )
        subtitle_label.pack(pady=(5, 0))
        
        # Navigation menu
        self.create_nav_button("📊 Dashboard", "dashboard", True)
        self.create_nav_button("⚙️ Configuration", "config")
        self.create_nav_button("📁 File Management", "files")
        self.create_nav_button("🚀 Send Emails", "send")
        self.create_nav_button("📈 Analytics", "analytics")
        
        # Status indicator at bottom
        self.create_status_indicator()
        
    def create_nav_button(self, text, view_name, active=False):
        """Create a navigation button"""
        bg_color = self.colors["accent"] if active else "transparent"
        hover_color = self.colors["accent"] if not active else self.colors["secondary"]
        
        btn = ctk.CTkButton(
            self.sidebar,
            text=text,
            font=self.fonts["body_bold"],
            fg_color=bg_color,
            hover_color=hover_color,
            text_color="white",
            anchor="w",
            height=50,
            command=lambda: self.navigate_to(view_name)
        )
        btn.pack(fill="x", padx=15, pady=2)
        
        # Store reference for later updates
        if not hasattr(self, 'nav_buttons'):
            self.nav_buttons = {}
        self.nav_buttons[view_name] = btn
        
    def create_status_indicator(self):
        """Create status indicator at bottom of sidebar"""
        status_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        status_frame.pack(side="bottom", fill="x", padx=15, pady=20)
        
        self.connection_status = ctk.CTkLabel(
            status_frame,
            text="🔴 Disconnected",
            font=self.fonts["small"],
            text_color="#94A3B8"
        )
        self.connection_status.pack(pady=5)
        
        self.system_status = ctk.CTkLabel(
            status_frame,
            text="System Ready",
            font=self.fonts["small"], 
            text_color="#94A3B8"
        )
        self.system_status.pack()
        
    def create_main_content_area(self):
        """Create the main content area"""
        self.main_content = ctk.CTkFrame(self.root, fg_color=self.colors["bg_secondary"])
        self.main_content.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        
    def navigate_to(self, view_name):
        """Handle navigation between views"""
        # Update button states
        for btn_name, btn in self.nav_buttons.items():
            if btn_name == view_name:
                btn.configure(fg_color=self.colors["accent"])
            else:
                btn.configure(fg_color="transparent")
        
        # Clear main content
        for widget in self.main_content.winfo_children():
            widget.destroy()
            
        # Show appropriate view
        if view_name == "dashboard":
            self.show_dashboard()
        elif view_name == "config":
            self.show_configuration()
        elif view_name == "files":
            self.show_file_management()
        elif view_name == "send":
            self.show_send_interface()
        elif view_name == "analytics":
            self.show_analytics()
            
        self.current_view = view_name
    
    def show_dashboard(self):
        """Show the dashboard view"""
        # Header
        header = self.create_section_header("Dashboard", "System overview and quick stats")
        
        # Stats cards
        stats_frame = ctk.CTkFrame(self.main_content, fg_color="transparent")
        stats_frame.pack(fill="x", padx=30, pady=(0, 20))
        stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        self.create_stat_card(stats_frame, "Total Sent", "0", self.colors["success"], 0)
        self.create_stat_card(stats_frame, "Failed", "0", self.colors["error"], 1)  
        self.create_stat_card(stats_frame, "Success Rate", "0%", self.colors["accent"], 2)
        self.create_stat_card(stats_frame, "Speed", "0/min", self.colors["warning"], 3)
        
        # Quick actions
        actions_frame = ctk.CTkFrame(self.main_content, fg_color=self.colors["bg_primary"])
        actions_frame.pack(fill="x", padx=30, pady=(0, 20))
        
        actions_header = ctk.CTkLabel(
            actions_frame,
            text="Quick Actions",
            font=self.fonts["heading"],
            text_color=self.colors["text_primary"]
        )
        actions_header.pack(anchor="w", padx=25, pady=(25, 15))
        
        actions_grid = ctk.CTkFrame(actions_frame, fg_color="transparent")
        actions_grid.pack(fill="x", padx=25, pady=(0, 25))
        actions_grid.grid_columnconfigure((0, 1, 2), weight=1)
        
        self.create_action_button(actions_grid, "⚙️ Setup Email", "Configure SMTP settings", lambda: self.navigate_to("config"), 0)
        self.create_action_button(actions_grid, "📁 Load Data", "Import email data file", lambda: self.navigate_to("files"), 1)
        self.create_action_button(actions_grid, "🚀 Send Emails", "Start bulk email process", lambda: self.navigate_to("send"), 2)
        
        # System info
        self.create_system_info()
        
    def create_stat_card(self, parent, title, value, color, col):
        """Create a statistics card"""
        card = ctk.CTkFrame(parent, fg_color=self.colors["bg_primary"])
        card.grid(row=0, column=col, sticky="ew", padx=10, pady=5)
        
        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=self.fonts["caption"],
            text_color=self.colors["text_secondary"]
        )
        title_label.pack(pady=(20, 5))
        
        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=self.fonts["title"],
            text_color=color
        )
        value_label.pack(pady=(0, 20))
        
        # Store reference for updates
        if not hasattr(self, 'stat_cards'):
            self.stat_cards = {}
        self.stat_cards[title.lower().replace(' ', '_')] = value_label
        
    def create_action_button(self, parent, title, description, command, col):
        """Create an action button"""
        card = ctk.CTkFrame(parent, fg_color=self.colors["bg_secondary"])
        card.grid(row=0, column=col, sticky="ew", padx=10, pady=5)
        
        btn = ctk.CTkButton(
            card,
            text=title,
            font=self.fonts["body_bold"],
            fg_color=self.colors["accent"],
            hover_color=self.colors["secondary"],
            height=40,
            command=command
        )
        btn.pack(padx=20, pady=(20, 10))
        
        desc_label = ctk.CTkLabel(
            card,
            text=description,
            font=self.fonts["small"],
            text_color=self.colors["text_secondary"],
            wraplength=150
        )
        desc_label.pack(pady=(0, 20))
        
    def create_system_info(self):
        """Create system information section"""
        info_frame = ctk.CTkFrame(self.main_content, fg_color=self.colors["bg_primary"])
        info_frame.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        
        info_header = ctk.CTkLabel(
            info_frame,
            text="System Information",
            font=self.fonts["heading"], 
            text_color=self.colors["text_primary"]
        )
        info_header.pack(anchor="w", padx=25, pady=(25, 15))
        
        # Create scrollable text area for logs
        self.log_text = ctk.CTkTextbox(
            info_frame,
            fg_color=self.colors["bg_secondary"],
            text_color=self.colors["text_secondary"],
            font=self.fonts["small"],
            wrap="word"
        )
        self.log_text.pack(fill="both", expand=True, padx=25, pady=(0, 25))
        
        # Add welcome message
        self.log("🏦 Axis Bank Enterprise Email System initialized")
        self.log("📊 Ready for high-volume email processing")
        self.log("⚡ Advanced features: Connection pooling, parallel processing, real-time monitoring")
        
    def show_configuration(self):
        """Show email configuration interface"""
        header = self.create_section_header("Email Configuration", "Configure SMTP settings and connection parameters")
        
        # Configuration form
        config_frame = ctk.CTkFrame(self.main_content, fg_color=self.colors["bg_primary"])
        config_frame.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        
        form_container = ctk.CTkScrollableFrame(config_frame, fg_color="transparent")
        form_container.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Email Provider
        self.create_form_field(form_container, "Email Provider", "dropdown", self.email_providers.keys())
        
        # SMTP Settings
        smtp_section = self.create_form_section(form_container, "SMTP Settings")
        self.create_form_field(smtp_section, "SMTP Server", "entry", placeholder="smtp.gmail.com")
        self.create_form_field(smtp_section, "SMTP Port", "entry", placeholder="587")
        
        # Account Details  
        account_section = self.create_form_section(form_container, "Account Details")
        self.create_form_field(account_section, "Sender Email", "entry", placeholder="your.email@company.com")
        self.create_form_field(account_section, "App Password", "password", placeholder="App-specific password")
        self.create_form_field(account_section, "Your Name", "entry", placeholder="Your Full Name")
        self.create_form_field(account_section, "Your Designation", "entry", placeholder="Your Job Title")
        
        # Performance Settings
        perf_section = self.create_form_section(form_container, "Performance Settings")
        self.create_form_field(perf_section, "Connection Pool Size", "slider", (1, 10, 5))
        self.create_form_field(perf_section, "Worker Threads", "slider", (1, 20, 8))
        self.create_form_field(perf_section, "Batch Size", "slider", (10, 100, 50))
        
        # Action buttons
        self.create_config_buttons(config_frame)
        
    def create_form_section(self, parent, title):
        """Create a form section with title"""
        section_frame = ctk.CTkFrame(parent, fg_color="transparent")
        section_frame.pack(fill="x", pady=(20, 10))
        
        title_label = ctk.CTkLabel(
            section_frame,
            text=title,
            font=self.fonts["subheading"],
            text_color=self.colors["text_primary"]
        )
        title_label.pack(anchor="w", pady=(0, 15))
        
        return section_frame
        
    def create_form_field(self, parent, label, field_type, options=None, placeholder=""):
        """Create a form field"""
        field_frame = ctk.CTkFrame(parent, fg_color="transparent")
        field_frame.pack(fill="x", pady=8)
        field_frame.grid_columnconfigure(1, weight=1)
        
        label_widget = ctk.CTkLabel(
            field_frame,
            text=label,
            font=self.fonts["body"],
            text_color=self.colors["text_primary"],
            width=200
        )
        label_widget.grid(row=0, column=0, sticky="w", padx=(0, 20))
        
        if field_type == "entry":
            widget = ctk.CTkEntry(
                field_frame,
                placeholder_text=placeholder,
                font=self.fonts["body"],
                height=40
            )
        elif field_type == "password":
            widget = ctk.CTkEntry(
                field_frame,
                placeholder_text=placeholder,
                font=self.fonts["body"],
                show="*",
                height=40
            )
        elif field_type == "dropdown":
            widget = ctk.CTkComboBox(
                field_frame,
                values=list(options),
                font=self.fonts["body"],
                height=40,
                state="readonly"
            )
        elif field_type == "slider":
            min_val, max_val, default_val = options
            widget = ctk.CTkSlider(
                field_frame,
                from_=min_val,
                to=max_val,
                number_of_steps=max_val-min_val
            )
            widget.set(default_val)
            
        widget.grid(row=0, column=1, sticky="ew")
        
        # Store reference
        if not hasattr(self, 'form_fields'):
            self.form_fields = {}
        self.form_fields[label.lower().replace(' ', '_')] = widget
        
    def create_config_buttons(self, parent):
        """Create configuration action buttons"""
        button_frame = ctk.CTkFrame(parent, fg_color="transparent", height=80)
        button_frame.pack(fill="x", padx=30, pady=(0, 30))
        button_frame.pack_propagate(False)
        
        # Test connection button
        test_btn = ctk.CTkButton(
            button_frame,
            text="🔍 Test Connection",
            font=self.fonts["body_bold"],
            fg_color=self.colors["warning"],
            hover_color="#D97706",
            height=45,
            command=self.test_smtp_connection
        )
        test_btn.pack(side="right", padx=(10, 0), pady=15)
        
        # Save button
        save_btn = ctk.CTkButton(
            button_frame,
            text="💾 Save Configuration",
            font=self.fonts["body_bold"],
            fg_color=self.colors["success"],
            hover_color="#059669",
            height=45,
            command=self.save_configuration
        )
        save_btn.pack(side="right", pady=15)
        
    def show_file_management(self):
        """Show file management interface"""
        header = self.create_section_header("File Management", "Upload and manage your data files")
        
        # File upload area
        upload_frame = ctk.CTkFrame(self.main_content, fg_color=self.colors["bg_primary"])
        upload_frame.pack(fill="x", padx=30, pady=(0, 20))
        
        # Data file section
        self.create_file_upload_section(upload_frame, "Data File", "Excel or CSV file containing email data", "data")
        
        # Attachment section
        self.create_file_upload_section(upload_frame, "Attachment", "Optional file to attach to all emails", "attachment")
        
        # File preview and validation
        preview_frame = ctk.CTkFrame(self.main_content, fg_color=self.colors["bg_primary"])
        preview_frame.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        
        preview_header = ctk.CTkLabel(
            preview_frame,
            text="File Preview & Validation",
            font=self.fonts["heading"],
            text_color=self.colors["text_primary"]
        )
        preview_header.pack(anchor="w", padx=25, pady=(25, 15))
        
        # Validation results
        self.validation_text = ctk.CTkTextbox(
            preview_frame,
            fg_color=self.colors["bg_secondary"],
            text_color=self.colors["text_secondary"],
            font=self.fonts["small"]
        )
        self.validation_text.pack(fill="both", expand=True, padx=25, pady=(0, 25))
        
        # Action buttons
        self.create_file_buttons(preview_frame)
        
    def create_file_upload_section(self, parent, title, description, file_type):
        """Create file upload section"""
        section_frame = ctk.CTkFrame(parent, fg_color="transparent")
        section_frame.pack(fill="x", padx=25, pady=15)
        
        # Header
        header_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(10, 5))
        
        title_label = ctk.CTkLabel(
            header_frame,
            text=title,
            font=self.fonts["subheading"],
            text_color=self.colors["text_primary"]
        )
        title_label.pack(side="left")
        
        # Upload button
        upload_btn = ctk.CTkButton(
            header_frame,
            text=f"📁 Browse {title}",
            font=self.fonts["body"],
            fg_color=self.colors["accent"],
            hover_color=self.colors["secondary"],
            command=lambda: self.browse_file(file_type)
        )
        upload_btn.pack(side="right")
        
        # Description
        desc_label = ctk.CTkLabel(
            section_frame,
            text=description,
            font=self.fonts["caption"],
            text_color=self.colors["text_secondary"]
        )
        desc_label.pack(anchor="w", pady=(0, 5))
        
        # File info display
        file_info_frame = ctk.CTkFrame(section_frame, fg_color=self.colors["bg_secondary"], height=60)
        file_info_frame.pack(fill="x", pady=5)
        file_info_frame.pack_propagate(False)
        
        # Store reference for updates
        if not hasattr(self, 'file_info_labels'):
            self.file_info_labels = {}
        
        info_label = ctk.CTkLabel(
            file_info_frame,
            text="No file selected",
            font=self.fonts["body"],
            text_color=self.colors["text_muted"]
        )
        info_label.pack(pady=15)
        self.file_info_labels[file_type] = info_label
        
    def create_file_buttons(self, parent):
        """Create file management action buttons"""
        button_frame = ctk.CTkFrame(parent, fg_color="transparent", height=80)
        button_frame.pack(fill="x", padx=25, pady=(0, 25))
        button_frame.pack_propagate(False)
        
        # Preview button
        preview_btn = ctk.CTkButton(
            button_frame,
            text="👁️ Preview Template",
            font=self.fonts["body_bold"],
            fg_color=self.colors["accent"],
            hover_color=self.colors["secondary"],
            height=45,
            command=self.preview_email_template
        )
        preview_btn.pack(side="left", pady=15)
        
        # Validate button
        validate_btn = ctk.CTkButton(
            button_frame,
            text="✅ Validate Data",
            font=self.fonts["body_bold"],
            fg_color=self.colors["success"],
            hover_color="#059669",
            height=45,
            command=self.validate_data_file
        )
        validate_btn.pack(side="right", padx=(10, 0), pady=15)
        
    def show_send_interface(self):
        """Show email sending interface"""
        header = self.create_section_header("Send Emails", "Execute bulk email campaigns with real-time monitoring")
        
        # Pre-send checks
        checks_frame = ctk.CTkFrame(self.main_content, fg_color=self.colors["bg_primary"])
        checks_frame.pack(fill="x", padx=30, pady=(0, 20))
        
        checks_header = ctk.CTkLabel(
            checks_frame,
            text="Pre-Send Verification",
            font=self.fonts["heading"],
            text_color=self.colors["text_primary"]
        )
        checks_header.pack(anchor="w", padx=25, pady=(25, 15))
        
        # Status checks
        checks_grid = ctk.CTkFrame(checks_frame, fg_color="transparent")
        checks_grid.pack(fill="x", padx=25, pady=(0, 25))
        checks_grid.grid_columnconfigure((0, 1, 2), weight=1)
        
        self.create_status_check(checks_grid, "SMTP Config", "Not configured", False, 0)
        self.create_status_check(checks_grid, "Data File", "Not loaded", False, 1)
        self.create_status_check(checks_grid, "Connection", "Not tested", False, 2)
        
        # Send options
        options_frame = ctk.CTkFrame(self.main_content, fg_color=self.colors["bg_primary"])
        options_frame.pack(fill="x", padx=30, pady=(0, 20))
        
        options_header = ctk.CTkLabel(
            options_frame,
            text="Send Options",
            font=self.fonts["heading"],
            text_color=self.colors["text_primary"]
        )
        options_header.pack(anchor="w", padx=25, pady=(25, 15))
        
        options_grid = ctk.CTkFrame(options_frame, fg_color="transparent")
        options_grid.pack(fill="x", padx=25, pady=(0, 25))
        options_grid.grid_columnconfigure((0, 1), weight=1)
        
        # Test email option
        self.test_email_var = ctk.BooleanVar(value=True)
        test_check = ctk.CTkCheckBox(
            options_grid,
            text="Send test email to sender first",
            font=self.fonts["body"],
            text_color=self.colors["text_primary"],
            variable=self.test_email_var
        )
        test_check.grid(row=0, column=0, sticky="w", pady=5)
        
        # Priority sending
        self.priority_var = ctk.BooleanVar()
        priority_check = ctk.CTkCheckBox(
            options_grid,
            text="High priority sending",
            font=self.fonts["body"],
            text_color=self.colors["text_primary"],
            variable=self.priority_var
        )
        priority_check.grid(row=0, column=1, sticky="w", pady=5)
        
        # Send buttons
        send_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        send_frame.pack(fill="x", padx=25, pady=(15, 25))
        send_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        test_btn = ctk.CTkButton(
            send_frame,
            text="🧪 Test Batch (5 emails)",
            font=self.fonts["body_bold"],
            fg_color=self.colors["warning"],
            hover_color="#D97706",
            height=50,
            command=self.send_test_batch
        )
        test_btn.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        partial_btn = ctk.CTkButton(
            send_frame,
            text="📤 Send Batch (100 emails)",
            font=self.fonts["body_bold"],
            fg_color=self.colors["accent"],
            hover_color=self.colors["secondary"],
            height=50,
            command=self.send_partial_batch
        )
        partial_btn.grid(row=0, column=1, sticky="ew", padx=5)
        
        full_btn = ctk.CTkButton(
            send_frame,
            text="🚀 Send All Emails",
            font=self.fonts["body_bold"],
            fg_color=self.colors["success"],
            hover_color="#059669",
            height=50,
            command=self.send_all_emails
        )
        full_btn.grid(row=0, column=2, sticky="ew", padx=(10, 0))
        
        # Progress monitoring
        self.create_progress_monitor()
        
    def create_status_check(self, parent, title, status, is_ok, col):
        """Create a status check indicator"""
        card = ctk.CTkFrame(parent, fg_color=self.colors["bg_secondary"])
        card.grid(row=0, column=col, sticky="ew", padx=10, pady=5)
        
        status_icon = "✅" if is_ok else "❌"
        status_color = self.colors["success"] if is_ok else self.colors["error"]
        
        icon_label = ctk.CTkLabel(
            card,
            text=status_icon,
            font=("Inter", 24),
        )
        icon_label.pack(pady=(15, 5))
        
        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=self.fonts["body_bold"],
            text_color=self.colors["text_primary"]
        )
        title_label.pack()
        
        status_label = ctk.CTkLabel(
            card,
            text=status,
            font=self.fonts["caption"],
            text_color=status_color
        )
        status_label.pack(pady=(5, 15))
        
        # Store reference for updates
        if not hasattr(self, 'status_checks'):
            self.status_checks = {}
        self.status_checks[title.lower().replace(' ', '_')] = {
            'icon': icon_label,
            'status': status_label
        }
        
    def create_progress_monitor(self):
        """Create progress monitoring section"""
        progress_frame = ctk.CTkFrame(self.main_content, fg_color=self.colors["bg_primary"])
        progress_frame.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        
        progress_header = ctk.CTkLabel(
            progress_frame,
            text="Progress Monitor",
            font=self.fonts["heading"],
            text_color=self.colors["text_primary"]
        )
        progress_header.pack(anchor="w", padx=25, pady=(25, 15))
        
        # Progress bars and stats
        stats_frame = ctk.CTkFrame(progress_frame, fg_color="transparent")
        stats_frame.pack(fill="x", padx=25, pady=(0, 15))
        stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        # Live statistics
        self.create_live_stat(stats_frame, "Processed", "0", self.colors["accent"], 0)
        self.create_live_stat(stats_frame, "Successful", "0", self.colors["success"], 1)
        self.create_live_stat(stats_frame, "Failed", "0", self.colors["error"], 2)
        self.create_live_stat(stats_frame, "Rate", "0/min", self.colors["warning"], 3)
        
        # Progress bar
        progress_container = ctk.CTkFrame(progress_frame, fg_color="transparent")
        progress_container.pack(fill="x", padx=25, pady=15)
        
        self.progress_label = ctk.CTkLabel(
            progress_container,
            text="Ready to start...",
            font=self.fonts["body"],
            text_color=self.colors["text_secondary"]
        )
        self.progress_label.pack(anchor="w", pady=(0, 10))
        
        self.progress_bar = ctk.CTkProgressBar(
            progress_container,
            progress_color=self.colors["success"],
            height=20
        )
        self.progress_bar.pack(fill="x", pady=(0, 15))
        self.progress_bar.set(0)
        
        # Real-time log
        log_container = ctk.CTkFrame(progress_frame, fg_color="transparent")
        log_container.pack(fill="both", expand=True, padx=25, pady=(0, 25))
        
        log_header = ctk.CTkFrame(log_container, fg_color="transparent", height=40)
        log_header.pack(fill="x")
        log_header.pack_propagate(False)
        
        log_title = ctk.CTkLabel(
            log_header,
            text="Real-time Log",
            font=self.fonts["body_bold"],
            text_color=self.colors["text_primary"]
        )
        log_title.pack(side="left", pady=10)
        
        # Clear log button
        clear_btn = ctk.CTkButton(
            log_header,
            text="🗑️ Clear",
            font=self.fonts["caption"],
            fg_color=self.colors["text_muted"],
            hover_color=self.colors["text_secondary"],
            width=80,
            height=30,
            command=self.clear_log
        )
        clear_btn.pack(side="right", pady=5)
        
        self.realtime_log = ctk.CTkTextbox(
            log_container,
            fg_color=self.colors["bg_secondary"],
            text_color=self.colors["text_secondary"],
            font=self.fonts["small"]
        )
        self.realtime_log.pack(fill="both", expand=True)
        
    def create_live_stat(self, parent, title, value, color, col):
        """Create a live updating statistic"""
        card = ctk.CTkFrame(parent, fg_color=self.colors["bg_secondary"])
        card.grid(row=0, column=col, sticky="ew", padx=5)
        
        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=self.fonts["caption"],
            text_color=self.colors["text_secondary"]
        )
        title_label.pack(pady=(15, 5))
        
        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=self.fonts["subheading"],
            text_color=color
        )
        value_label.pack(pady=(0, 15))
        
        # Store reference for updates
        if not hasattr(self, 'live_stats'):
            self.live_stats = {}
        self.live_stats[title.lower()] = value_label
        
    def show_analytics(self):
        """Show analytics and reporting interface"""
        header = self.create_section_header("Analytics & Reports", "View detailed performance metrics and generate reports")
        
        # Summary cards
        summary_frame = ctk.CTkFrame(self.main_content, fg_color=self.colors["bg_primary"])
        summary_frame.pack(fill="x", padx=30, pady=(0, 20))
        
        summary_header = ctk.CTkLabel(
            summary_frame,
            text="Campaign Summary",
            font=self.fonts["heading"],
            text_color=self.colors["text_primary"]
        )
        summary_header.pack(anchor="w", padx=25, pady=(25, 15))
        
        # Analytics grid
        analytics_grid = ctk.CTkFrame(summary_frame, fg_color="transparent")
        analytics_grid.pack(fill="x", padx=25, pady=(0, 25))
        analytics_grid.grid_columnconfigure((0, 1, 2), weight=1)
        
        self.create_analytics_card(analytics_grid, "Total Campaigns", "0", "📊", 0)
        self.create_analytics_card(analytics_grid, "Total Emails Sent", "0", "📧", 1)
        self.create_analytics_card(analytics_grid, "Average Success Rate", "0%", "📈", 2)
        
        # Detailed metrics
        metrics_frame = ctk.CTkFrame(self.main_content, fg_color=self.colors["bg_primary"])
        metrics_frame.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        
        metrics_header = ctk.CTkLabel(
            metrics_frame,
            text="Performance Metrics",
            font=self.fonts["heading"],
            text_color=self.colors["text_primary"]
        )
        metrics_header.pack(anchor="w", padx=25, pady=(25, 15))
        
        # Metrics table
        self.create_metrics_table(metrics_frame)
        
    def create_analytics_card(self, parent, title, value, icon, col):
        """Create an analytics card"""
        card = ctk.CTkFrame(parent, fg_color=self.colors["bg_secondary"])
        card.grid(row=0, column=col, sticky="ew", padx=10, pady=5)
        
        icon_label = ctk.CTkLabel(
            card,
            text=icon,
            font=("Inter", 32)
        )
        icon_label.pack(pady=(20, 10))
        
        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=self.fonts["title"],
            text_color=self.colors["accent"]
        )
        value_label.pack()
        
        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=self.fonts["body"],
            text_color=self.colors["text_secondary"]
        )
        title_label.pack(pady=(5, 20))
        
    def create_metrics_table(self, parent):
        """Create metrics table"""
        table_frame = ctk.CTkScrollableFrame(parent, fg_color=self.colors["bg_secondary"])
        table_frame.pack(fill="both", expand=True, padx=25, pady=(0, 25))
        
        # Table headers
        headers = ["Campaign", "Date", "Emails Sent", "Success Rate", "Avg Speed", "Status"]
        header_frame = ctk.CTkFrame(table_frame, fg_color=self.colors["primary"])
        header_frame.pack(fill="x", pady=(0, 5))
        header_frame.grid_columnconfigure(tuple(range(len(headers))), weight=1)
        
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(
                header_frame,
                text=header,
                font=self.fonts["body_bold"],
                text_color="white"
            )
            label.grid(row=0, column=i, padx=10, pady=15, sticky="ew")
        
        # Sample data rows
        sample_data = [
            ["Campaign #1", "2024-01-15", "1,250", "98.4%", "145/min", "✅ Complete"],
            ["Campaign #2", "2024-01-14", "856", "96.8%", "132/min", "✅ Complete"],
            ["Campaign #3", "2024-01-13", "2,100", "97.2%", "158/min", "✅ Complete"],
        ]
        
        for row_data in sample_data:
            row_frame = ctk.CTkFrame(table_frame, fg_color=self.colors["bg_primary"])
            row_frame.pack(fill="x", pady=2)
            row_frame.grid_columnconfigure(tuple(range(len(row_data))), weight=1)
            
            for i, cell_data in enumerate(row_data):
                label = ctk.CTkLabel(
                    row_frame,
                    text=cell_data,
                    font=self.fonts["body"],
                    text_color=self.colors["text_primary"]
                )
                label.grid(row=0, column=i, padx=10, pady=10, sticky="ew")
    
    def create_section_header(self, title, description):
        """Create a section header"""
        header_frame = ctk.CTkFrame(self.main_content, fg_color="transparent", height=100)
        header_frame.pack(fill="x", padx=30, pady=(30, 20))
        header_frame.pack_propagate(False)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text=title,
            font=self.fonts["title"],
            text_color=self.colors["text_primary"]
        )
        title_label.pack(anchor="w", pady=(20, 5))
        
        desc_label = ctk.CTkLabel(
            header_frame,
            text=description,
            font=self.fonts["body"],
            text_color=self.colors["text_secondary"]
        )
        desc_label.pack(anchor="w")
        
        return header_frame
    
    # Core functionality methods
    def log(self, message, log_type="info"):
        """Add message to log with timestamp and styling"""
        def update_log():
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Color coding for different log types
            if log_type == "success":
                prefix = "✅"
                color_code = ""  # Green in the actual display
            elif log_type == "error":
                prefix = "❌"
                color_code = ""  # Red in the actual display  
            elif log_type == "warning":
                prefix = "⚠️"
                color_code = ""  # Orange in the actual display
            else:
                prefix = "ℹ️"
                color_code = ""  # Default color
            
            log_entry = f"[{timestamp}] {prefix} {message}\n"
            
            # Update dashboard log if it exists
            if hasattr(self, 'log_text'):
                self.log_text.insert("end", log_entry)
                self.log_text.see("end")
            
            # Update realtime log if it exists
            if hasattr(self, 'realtime_log'):
                self.realtime_log.insert("end", log_entry)
                self.realtime_log.see("end")
        
        # Ensure GUI updates happen on main thread
        if threading.current_thread() == threading.main_thread():
            update_log()
        else:
            self.root.after(0, update_log)
    
    def clear_log(self):
        """Clear the log display"""
        if hasattr(self, 'realtime_log'):
            self.realtime_log.delete("1.0", "end")
    
    def browse_file(self, file_type):
        """Browse and select files"""
        if file_type == "data":
            filetypes = [
                ("Excel files", "*.xlsx *.xls"),
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
            title = "Select Data File"
        else:
            filetypes = [("All files", "*.*")]
            title = "Select Attachment File"
        
        filename = filedialog.askopenfilename(title=title, filetypes=filetypes)
        if filename:
            if file_type == "data":
                self.data_file = filename
                self.log(f"Data file selected: {os.path.basename(filename)}", "success")
                # Validate immediately
                self.validate_data_file()
            else:
                self.attachment_file = filename
                # Pre-load attachment
                self.preload_attachment()
                self.log(f"Attachment selected: {os.path.basename(filename)}", "success")
            
            # Update UI
            if hasattr(self, 'file_info_labels'):
                self.file_info_labels[file_type].configure(
                    text=f"📎 {os.path.basename(filename)}",
                    text_color=self.colors["text_primary"]
                )
    
    def preload_attachment(self):
        """Pre-load attachment into memory"""
        if self.attachment_file:
            try:
                with open(self.attachment_file, "rb") as f:
                    self.attachment_data = f.read()
                self.attachment_name = os.path.basename(self.attachment_file)
                self.log(f"Attachment cached: {len(self.attachment_data)} bytes", "success")
            except Exception as e:
                self.log(f"Failed to cache attachment: {e}", "error")
    
    def validate_data_file(self):
        """Validate the selected data file"""
        if not self.data_file:
            self.log("No data file selected", "warning")
            return False
        
        try:
            # Load data
            if self.data_file.endswith('.csv'):
                df = pd.read_csv(self.data_file)
            else:
                df = pd.read_excel(self.data_file)
            
            # Check required columns
            required_columns = [
                'agency_name', 'agency_location', 'recipient_email', 'agency_person_name',
                'agency_address', 'audit_date', 'cc_to', 'Audit_Period', 'Types_Of_Risk',
                'Main_Category', 'Audit_Check', 'Auditor_Observations'
            ]
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                error_msg = f"Missing columns: {', '.join(missing_columns)}"
                self.log(error_msg, "error")
                if hasattr(self, 'validation_text'):
                    self.validation_text.delete("1.0", "end")
                    self.validation_text.insert("1.0", f"❌ Validation Failed\n\n{error_msg}\n\nAvailable columns:\n{', '.join(df.columns)}")
                return False
            
            # Success
            unique_agencies = df['agency_name'].nunique()
            valid_emails = df['recipient_email'].notna().sum()
            
            success_msg = f"✅ Validation Successful\n\nTotal Records: {len(df):,}\nUnique Agencies: {unique_agencies:,}\nValid Emails: {valid_emails:,}\n\nFile is ready for processing!"
            
            self.log(f"File validated: {len(df)} records, {unique_agencies} agencies", "success")
            
            if hasattr(self, 'validation_text'):
                self.validation_text.delete("1.0", "end")
                self.validation_text.insert("1.0", success_msg)
            
            # Pre-process data for performance
            self.preprocess_data(df)
            
            # Update status checks
            self.update_status_check('data_file', 'Data loaded & validated', True)
            
            return True
            
        except Exception as e:
            error_msg = f"Validation error: {str(e)}"
            self.log(error_msg, "error")
            if hasattr(self, 'validation_text'):
                self.validation_text.delete("1.0", "end")
                self.validation_text.insert("1.0", f"❌ Validation Failed\n\n{error_msg}")
            return False
    
    def preprocess_data(self, df):
        """Pre-process data for optimal performance"""
        try:
            df = df.fillna('')
            grouped = df.groupby('agency_name')
            
            # Pre-generate audit tables
            self.audit_table_cache.clear()
            for agency_name, agency_df in grouped:
                self.audit_table_cache[agency_name] = self.create_audit_table(agency_df)
            
            self.log(f"Pre-processed {len(grouped.groups)} audit tables", "success")
            
        except Exception as e:
            self.log(f"Pre-processing error: {e}", "error")
    
    def create_audit_table(self, agency_audit_df):
        """Create HTML audit table"""
        if agency_audit_df.empty:
            return "<p><strong>No audit observations found.</strong></p>"
        
        rows = []
        for i, (_, row) in enumerate(agency_audit_df.iterrows()):
            row_class = "even" if i % 2 == 0 else "odd"
            rows.append(f"""
            <tr class="{row_class}">
                <td style="text-align: center; font-weight: bold;">{i + 1}</td>
                <td>{row.get('Audit_Period', 'N/A')}</td>
                <td>{row.get('Types_Of_Risk', 'N/A')}</td>
                <td>{row.get('Main_Category', 'N/A')}</td>
                <td>{row.get('Audit_Check', 'N/A')}</td>
                <td>{row.get('Auditor_Observations', 'N/A')}</td>
                <td class="vendor-column">[To be filled by Vendor]</td>
            </tr>""")
        
        return f"""
        <table style="width: 100%; border-collapse: collapse; margin: 20px 0; font-family: 'Segoe UI', sans-serif;">
            <thead>
                <tr style="background: #1e293b; color: white;">
                    <th style="padding: 12px; border: 1px solid #ddd;">Sr. No.</th>
                    <th style="padding: 12px; border: 1px solid #ddd;">Audit Period</th>
                    <th style="padding: 12px; border: 1px solid #ddd;">Risk Type</th>
                    <th style="padding: 12px; border: 1px solid #ddd;">Category</th>
                    <th style="padding: 12px; border: 1px solid #ddd;">Audit Check</th>
                    <th style="padding: 12px; border: 1px solid #ddd;">Observations</th>
                    <th style="padding: 12px; border: 1px solid #ddd;">Vendor Response</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
        """
    
    def test_smtp_connection(self):
        """Test SMTP connection"""
        if not hasattr(self, 'form_fields'):
            messagebox.showerror("Error", "Please fill in the configuration first!")
            return
        
        try:
            # Get values from form
            provider = self.form_fields['email_provider'].get()
            email = self.form_fields['sender_email'].get()
            password = self.form_fields['app_password'].get()
            
            if not all([email, password]):
                messagebox.showerror("Error", "Please fill in email and password!")
                return
            
            # Set SMTP settings based on provider
            if provider in self.email_providers:
                smtp_server = self.email_providers[provider]["server"]
                smtp_port = self.email_providers[provider]["port"]
            
            self.log("Testing SMTP connection...", "info")
            
            # Test connection
            context = ssl.create_default_context()
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls(context=context)
                server.login(email, password)
                
            self.log("SMTP connection test successful!", "success")
            self.update_status_check('smtp_config', 'Configured & tested', True)
            self.update_status_check('connection', 'Connection verified', True)
            messagebox.showinfo("Success", "SMTP connection test successful!")
            
        except Exception as e:
            error_msg = f"SMTP connection failed: {str(e)}"
            self.log(error_msg, "error")
            messagebox.showerror("Connection Error", error_msg)
    
    def save_configuration(self):
        """Save email configuration"""
        if not hasattr(self, 'form_fields'):
            return
        
        try:
            # Extract form data
            self.config.sender_email = self.form_fields['sender_email'].get()
            self.config.password = self.form_fields['app_password'].get()
            self.config.your_name = self.form_fields['your_name'].get()
            self.config.your_designation = self.form_fields['your_designation'].get()
            
            provider = self.form_fields['email_provider'].get()
            if provider in self.email_providers:
                self.config.smtp_server = self.email_providers[provider]["server"]
                self.config.smtp_port = self.email_providers[provider]["port"]
            
            # Performance settings
            self.max_workers = int(self.form_fields['worker_threads'].get())
            self.batch_size = int(self.form_fields['batch_size'].get())
            pool_size = int(self.form_fields['connection_pool_size'].get())
            
            # Initialize connection pool
            if self.connection_pool:
                self.connection_pool.close_all()
            
            self.connection_pool = ConnectionPool(self.config, pool_size)
            
            self.log("Configuration saved successfully!", "success")
            self.update_status_check('smtp_config', 'Configured', True)
            self.connection_status.configure(text="🟢 Connected", text_color=self.colors["success"])
            
            messagebox.showinfo("Success", "Configuration saved and connection pool initialized!")
            
        except Exception as e:
            error_msg = f"Failed to save configuration: {str(e)}"
            self.log(error_msg, "error")
            messagebox.showerror("Error", error_msg)
    
    def update_status_check(self, check_name, status_text, is_ok):
        """Update status check indicators"""
        if hasattr(self, 'status_checks') and check_name in self.status_checks:
            icon = "✅" if is_ok else "❌"
            color = self.colors["success"] if is_ok else self.colors["error"]
            
            self.status_checks[check_name]['icon'].configure(text=icon)
            self.status_checks[check_name]['status'].configure(text=status_text, text_color=color)
    
    def preview_email_template(self):
        """Show email template preview"""
        if not self.config.sender_email:
            messagebox.showerror("Error", "Please configure email settings first!")
            return
        
        # Sample data for preview
        sample_data = {
            'date': datetime.now().strftime("%Y-%m-%d"),
            'agency_name': 'Sample Financial Services Pvt Ltd',
            'agency_address': '123 Business District, Tower A, Floor 15\nMumbai, Maharashtra 400001\nIndia',
            'agency_location': 'Mumbai',
            'audit_date': '2024-01-15',
            'agency_person_name': 'Mr. Rajesh Kumar',
            'your_name': self.config.your_name or "John Doe",
            'your_designation': self.config.your_designation or "Senior Manager - Audit",
            'cc_to': 'audit.manager@axisbank.com, compliance@axisbank.com',
            'audit_table': '''
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <thead>
                    <tr style="background: #1e293b; color: white;">
                        <th style="padding: 12px; border: 1px solid #ddd;">Sr. No.</th>
                        <th style="padding: 12px; border: 1px solid #ddd;">Audit Check</th>
                        <th style="padding: 12px; border: 1px solid #ddd;">Observation</th>
                        <th style="padding: 12px; border: 1px solid #ddd;">Vendor Response</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; text-align: center; font-weight: bold;">1</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Document Management</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Missing customer KYC documents for 5 accounts</td>
                        <td style="padding: 10px; border: 1px solid #ddd; background: #fef3c7; font-weight: bold; color: #92400e;">[To be filled by Vendor]</td>
                    </tr>
                    <tr style="background: #f8fafc;">
                        <td style="padding: 10px; border: 1px solid #ddd; text-align: center; font-weight: bold;">2</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Compliance Check</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Late submission of monthly reports</td>
                        <td style="padding: 10px; border: 1px solid #ddd; background: #fef3c7; font-weight: bold; color: #92400e;">[To be filled by Vendor]</td>
                    </tr>
                </tbody>
            </table>
            '''
        }
        
        email_body = self.EMAIL_TEMPLATE.substitute(sample_data)
        
        # Create preview window
        preview_window = ctk.CTkToplevel(self.root)
        preview_window.title("Email Template Preview - Axis Bank")
        preview_window.geometry("1000x800")
        preview_window.configure(fg_color=self.colors["bg_secondary"])
        
        # Header
        header_frame = ctk.CTkFrame(preview_window, fg_color=self.colors["primary"], height=60)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        header_label = ctk.CTkLabel(
            header_frame,
            text="📧 Email Template Preview",
            font=self.fonts["heading"],
            text_color="white"
        )
        header_label.pack(pady=15)
        
        # Content
        content_frame = ctk.CTkFrame(preview_window, fg_color=self.colors["bg_primary"])
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # HTML display (simplified as text)
        text_area = ctk.CTkTextbox(
            content_frame,
            font=("Consolas", 11),
            text_color=self.colors["text_primary"],
            fg_color=self.colors["bg_secondary"]
        )
        text_area.pack(fill="both", expand=True, padx=20, pady=20)
        text_area.insert("1.0", email_body)
        text_area.configure(state="disabled")
    
    def update_live_stats(self, processed=None, successful=None, failed=None, rate=None):
        """Update live statistics display"""
        def update():
            if hasattr(self, 'live_stats'):
                if processed is not None:
                    self.live_stats['processed'].configure(text=str(processed))
                if successful is not None:
                    self.live_stats['successful'].configure(text=str(successful))
                if failed is not None:
                    self.live_stats['failed'].configure(text=str(failed))
                if rate is not None:
                    self.live_stats['rate'].configure(text=f"{rate:.0f}/min")
            
            # Update dashboard stats too
            if hasattr(self, 'stat_cards'):
                if successful is not None:
                    self.stat_cards['total_sent'].configure(text=str(successful))
                if failed is not None:
                    self.stat_cards['failed'].configure(text=str(failed))
                if successful is not None and failed is not None and (successful + failed) > 0:
                    success_rate = (successful / (successful + failed)) * 100
                    self.stat_cards['success_rate'].configure(text=f"{success_rate:.1f}%")
                if rate is not None:
                    self.stat_cards['speed'].configure(text=f"{rate:.0f}/min")
        
        if threading.current_thread() == threading.main_thread():
            update()
        else:
            self.root.after(0, update)
    
    def update_progress(self, current, total, message=""):
        """Update progress bar and message"""
        def update():
            if total > 0:
                progress = current / total
                self.progress_bar.set(progress)
                
            if message:
                self.progress_label.configure(text=message)
            else:
                self.progress_label.configure(text=f"Processing: {current}/{total} ({(current/total)*100:.1f}%)")
        
        if threading.current_thread() == threading.main_thread():
            update()
        else:
            self.root.after(0, update)
    
    def send_optimized_email(self, agency_info, server):
        """Optimized email sending function"""
        try:
            agency_name = agency_info.get('agency_name', '')
            audit_table = self.audit_table_cache.get(agency_name, '<p><strong>No audit data found.</strong></p>')
            
            # Prepare email data
            data = {
                'date': datetime.now().strftime("%Y-%m-%d"),
                'agency_name': agency_name,
                'agency_address': agency_info.get('agency_address', ''),
                'agency_location': agency_info.get('agency_location', ''),
                'audit_date': agency_info.get('audit_date', 'N/A'),
                'agency_person_name': agency_info.get('agency_person_name', ''),
                'your_name': self.config.your_name,
                'your_designation': self.config.your_designation,
                'cc_to': agency_info.get('cc_to', ''),
                'audit_table': audit_table
            }
            
            recipient_email = agency_info.get('recipient_email', '').strip()
            if not recipient_email:
                return False, "No recipient email"
            
            # Parse CC emails
            cc_emails = [e.strip() for e in str(data.get('cc_to', '')).split(',') if e.strip()]
            
            # Create subject
            subject = f"{data['agency_name']} {data['agency_location']} - Show Cause Notice: Dated {data['audit_date']}"
            
            # Generate email body
            body = self.EMAIL_TEMPLATE.substitute(data)
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = f"{self.config.your_name} <{self.config.sender_email}>"
            msg['To'] = recipient_email
            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html'))
            
            # Add attachment if available
            if self.attachment_data and self.attachment_name:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(self.attachment_data)
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename= {self.attachment_name}')
                msg.attach(part)
            
            # Send email
            all_recipients = [recipient_email] + cc_emails
            server.sendmail(self.config.sender_email, all_recipients, msg.as_string())
            return True, "Success"
            
        except Exception as e:
            return False, str(e)
    
    def email_worker_thread(self, email_batch, results_queue, worker_id):
        """Worker thread for sending emails"""
        connection = None
        try:
            connection = self.connection_pool.get_connection()
            
            for i, agency_info in enumerate(email_batch):
                try:
                    success, result = self.send_optimized_email(agency_info, connection)
                    
                    if success:
                        self.sent_emails += 1
                        results_queue.put(('success', agency_info.get('agency_name', 'Unknown'), worker_id))
                    else:
                        self.failed_emails += 1
                        results_queue.put(('failed', f"{agency_info.get('agency_name', 'Unknown')}: {result}", worker_id))
                    
                    # Small delay to avoid overwhelming server
                    time.sleep(self.email_delay)
                    
                except Exception as e:
                    self.failed_emails += 1
                    results_queue.put(('error', f"{agency_info.get('agency_name', 'Unknown')}: {str(e)}", worker_id))
                    
        except Exception as e:
            results_queue.put(('thread_error', f"Worker {worker_id} error: {str(e)}", worker_id))
        finally:
            if connection and self.connection_pool:
                self.connection_pool.return_connection(connection)
    
    def process_bulk_emails(self, limit=None, test_mode=False):
        """Main bulk email processing with enhanced monitoring"""
        if not self.connection_pool:
            messagebox.showerror("Error", "Please configure SMTP settings first!")
            return
        
        if not self.data_file:
            messagebox.showerror("Error", "Please select a data file!")
            return
        
        try:
            self.log("🚀 Starting bulk email processing...", "info")
            
            # Load data
            if self.data_file.endswith('.csv'):
                df = pd.read_csv(self.data_file, dtype=str)
            else:
                df = pd.read_excel(self.data_file, dtype=str)
            
            df = df.fillna('')
            grouped = df.groupby('agency_name')
            agencies = list(grouped.groups.keys())
            
            if limit:
                agencies = agencies[:limit]
            
            if test_mode:
                self.log(f"🧪 Test mode: Processing {len(agencies)} agencies", "warning")
            
            # Prepare agency data
            agency_data = []
            for agency_name in agencies:
                agency_df = grouped.get_group(agency_name)
                agency_info = agency_df.iloc[0].to_dict()
                agency_data.append(agency_info)
            
            self.total_emails = len(agency_data)
            self.sent_emails = 0
            self.failed_emails = 0
            self.start_time = time.time()
            
            # Send test email if requested
            if self.test_email_var.get() and agency_data:
                self.log("📧 Sending test email to sender...", "info")
                test_info = agency_data[0].copy()
                test_info['recipient_email'] = self.config.sender_email
                test_info['agency_name'] = f"[TEST] {test_info['agency_name']}"
                
                connection = self.connection_pool.get_connection()
                success, _ = self.send_optimized_email(test_info, connection)
                self.connection_pool.return_connection(connection)
                
                if success:
                    self.log("✅ Test email sent successfully!", "success")
                    result = messagebox.askyesno("Test Email", "Test email sent! Continue with bulk sending?")
                    if not result:
                        self.log("❌ Bulk sending cancelled by user", "warning")
                        return
                else:
                    messagebox.showerror("Error", "Test email failed! Check configuration.")
                    return
            
            # Create batches
            batches = [agency_data[i:i + self.batch_size] for i in range(0, len(agency_data), self.batch_size)]
            self.log(f"📦 Created {len(batches)} batches with {self.max_workers} workers", "info")
            
            # Progress tracking
            results_queue = Queue()
            processed_count = 0
            
            # Process batches with ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all batches
                futures = []
                for i, batch in enumerate(batches):
                    future = executor.submit(self.email_worker_thread, batch, results_queue, i)
                    futures.append(future)
                
                # Monitor progress
                last_update_time = time.time()
                while processed_count < self.total_emails:
                    try:
                        result_type, message, worker_id = results_queue.get(timeout=1)
                        processed_count += 1
                        
                        # Log result
                        if result_type == 'success':
                            self.log(f"✅ Sent to {message}", "success")
                        elif result_type == 'failed':
                            self.log(f"❌ Failed: {message}", "error")
                        elif result_type in ['error', 'thread_error']:
                            self.log(f"🔥 {message}", "error")
                        
                        # Update UI every second or every 10 emails
                        current_time = time.time()
                        if current_time - last_update_time >= 1.0 or processed_count % 10 == 0:
                            elapsed_time = current_time - self.start_time
                            rate = (self.sent_emails + self.failed_emails) / (elapsed_time / 60) if elapsed_time > 0 else 0
                            
                            self.update_live_stats(
                                processed=self.sent_emails + self.failed_emails,
                                successful=self.sent_emails,
                                failed=self.failed_emails,
                                rate=rate
                            )
                            
                            self.update_progress(
                                processed_count,
                                self.total_emails,
                                f"Processing: {processed_count}/{self.total_emails} - Rate: {rate:.0f}/min"
                            )
                            
                            last_update_time = current_time
                        
                    except:
                        # Check if all futures are done
                        if all(f.done() for f in futures):
                            break
                        continue
                
                # Wait for completion
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        self.log(f"🔥 Batch error: {e}", "error")
            
            # Final statistics
            total_time = time.time() - self.start_time
            final_rate = self.total_emails / (total_time / 60) if total_time > 0 else 0
            success_rate = (self.sent_emails / self.total_emails * 100) if self.total_emails > 0 else 0
            
            self.update_live_stats(
                processed=self.sent_emails + self.failed_emails,
                successful=self.sent_emails,
                failed=self.failed_emails,
                rate=final_rate
            )
            
            self.update_progress(self.total_emails, self.total_emails, "✅ Processing Complete!")
            
            # Success message
            summary = f"""🎉 Bulk Email Campaign Complete!

📊 Campaign Statistics:
• Total Processed: {self.total_emails:,}
• Successfully Sent: {self.sent_emails:,}
• Failed: {self.failed_emails:,}
• Success Rate: {success_rate:.1f}%
• Processing Rate: {final_rate:.1f} emails/min
• Total Time: {total_time:.1f} seconds

🚀 Performance: {self.max_workers} workers, {self.batch_size} batch size"""
            
            self.log("🎉 Bulk email campaign completed successfully!", "success")
            messagebox.showinfo("Campaign Complete", summary)
            
        except Exception as e:
            error_msg = f"Critical error in bulk processing: {str(e)}"
            self.log(error_msg, "error")
            messagebox.showerror("Critical Error", error_msg)
    
    def send_test_batch(self):
        """Send test batch of 5 emails"""
        def run_test():
            self.process_bulk_emails(limit=5, test_mode=True)
        
        threading.Thread(target=run_test, daemon=True).start()
    
    def send_partial_batch(self):
        """Send partial batch of 100 emails"""
        def run_partial():
            self.process_bulk_emails(limit=100, test_mode=False)
        
        threading.Thread(target=run_partial, daemon=True).start()
    
    def send_all_emails(self):
        """Send all emails"""
        def run_all():
            self.process_bulk_emails(test_mode=False)
        
        threading.Thread(target=run_all, daemon=True).start()
    
    def run(self):
        """Start the application"""
        self.create_main_window()
        try:
            self.root.mainloop()
        finally:
            # Cleanup
            if self.connection_pool:
                self.connection_pool.close_all()


def main():
    """Main application entry point"""
    try:
        app = EnterpriseBulkEmailSystem()
        app.run()
    except Exception as e:
        print(f"Application startup error: {e}")
        messagebox.showerror("Startup Error", f"Failed to start application: {e}")


if __name__ == "__main__":
    main()
