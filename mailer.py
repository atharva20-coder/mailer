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

# UI Libraries - Swapped to customtkinter
import customtkinter as ctk
from tkinter import filedialog, messagebox

# Set the appearance mode for customtkinter
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class EmailConfig:
    """Class to store email configuration (UNCHANGED)"""

    def __init__(self):
        self.sender_email = ""
        self.password = ""
        self.your_name = ""
        self.your_designation = ""
        self.smtp_server = ""
        self.smtp_port = 587


class BulkEmailSender:
    def __init__(self):
        self.config = EmailConfig()
        self.data_file = ""
        self.attachment_file = ""

        # Email providers configuration (UNCHANGED)
        self.email_providers = {
            "Gmail": {"server": "smtp.gmail.com", "port": 587},
            "Office 365": {"server": "smtp.office365.com", "port": 587},
            "Outlook.com": {"server": "smtp-mail.outlook.com", "port": 587},
            "Yahoo": {"server": "smtp.mail.yahoo.com", "port": 587},
            "Custom": {"server": "", "port": 587}
        }

        # --- UI STYLING CONSTANTS ---
        self.colors = {
            "bg": "#F9F5F2",
            "frame_bg": "#FFFFFF",
            "text": "#1E1E1E",
            "text_light": "#666666",
            "button": "#1E1E1E",
            "button_hover": "#333333",
            "accent": "#E67E22",
            "success": "#27AE60",
            "error": "#C0392B"
        }
        self.fonts = {
            "title": ("Times New Roman", 48, "bold"),
            "subtitle": ("Arial", 14),
            "heading": ("Arial", 16, "bold"),
            "body": ("Arial", 12),
            "button": ("Arial", 12, "bold"),
            "small": ("Arial", 10)
        }

        self.animation_steps = 20
        self.animation_speed = 0.008

        # Email Template (UNCHANGED)
        self.EMAIL_TEMPLATE = Template("""
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }
        .header { margin-bottom: 30px; }
        .content { margin: 20px 0; }
        .signature { margin-top: 30px; }
        .notice-title { color: #cc0000; font-weight: bold; font-size: 16px; }
    </style>
</head>
<body>
    <div class="header">
        <p><strong>Date:</strong> $date</p>
        <p><strong>To:</strong><br>
        $agency_name<br>
        $agency_address</p>

        <p class="notice-title">Subject: $agency_name $agency_location - Show Cause Notice for External Audit Observations: Dated $audit_date</p>
    </div>

    <div class="content">
        <p><strong>Dear Associate - $agency_person_name,</strong></p>

        <p>We are issuing this notice in your capacity as an empaneled vendor/agency of <strong>Axis Bank Ltd</strong>. This communication serves as a <strong>Show Cause Notice</strong> under the applicable contractual and legal obligations, including but not to the terms of engagement executed between your agency and Axis Bank.</p>

        <p>It has come to our attention, pursuant to external audit conducted at your agency (<strong>$agency_location</strong>) on dated <strong>$audit_date</strong>. During the External audit we have identified below mentioned observations:</p>

        $audit_table

        <p style="color: #cc0000; font-weight: bold;">Please provide your response and corrective action plan within 7 working days from the date of this notice.</p>

        <p><strong>Instructions for Response:</strong></p>
        <ul>
            <li>Fill the "Vendor Justifications and Documentations" column for each observation</li>
            <li>Provide supporting documents as evidence</li>
            <li>Submit corrective action plan with timelines</li>
            <li>Send response via email with all supporting documents</li>
        </ul>
    </div>

    <div class="signature">
        <p><strong>Regards,</strong><br>
        $your_name<br>
        $your_designation<br>
        <strong>Axis Bank Ltd.</strong></p>

        <p><strong>CC to:</strong> $cc_to</p>

        <p><strong>Annexures:</strong> As attached</p>
    </div>
</body>
</html>""")

    def setup_gui(self):
        """Create the main GUI window using customtkinter"""
        self.root = ctk.CTk()
        self.root.title("Universal Bulk Email System")
        self.root.geometry("1000x750")
        self.root.configure(fg_color=self.colors["bg"])
        self.root.resizable(True, True)  # Allow resizing/maximizing

        # Main layout: 1x2 grid
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=2)
        self.root.grid_rowconfigure(0, weight=1)

        # --- Left Frame (Title) ---
        self.left_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=40, pady=20)

        logo_label = ctk.CTkLabel(self.left_frame, text="*", font=("Arial", 30, "bold"),
                                  text_color=self.colors["accent"])
        logo_label.pack(anchor="w", pady=(20, 0))

        ctk.CTkLabel(self.left_frame, text="Automated", font=self.fonts["title"], text_color=self.colors["text"],
                     anchor="w", justify="left").pack(fill="x", pady=(20, 0))
        ctk.CTkLabel(self.left_frame, text="Mailer.", font=self.fonts["title"], text_color=self.colors["text"],
                     anchor="w", justify="left").pack(fill="x")

        ctk.CTkLabel(self.left_frame, text="The AI for bulk mailing", font=self.fonts["subtitle"],
                     text_color=self.colors["text_light"], anchor="w", justify="left").pack(fill="x", pady=(10, 0))

        # --- Right Frame (Container for sliding frames) ---
        self.right_frame_container = ctk.CTkFrame(self.root, fg_color="transparent")
        self.right_frame_container.grid(row=0, column=1, sticky="nsew", padx=(20, 40), pady=40)

        # --- Main Controls Frame (Initially visible) ---
        self.main_controls_frame = ctk.CTkFrame(self.right_frame_container, fg_color="transparent")
        self.main_controls_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.setup_main_controls()

        # --- Email Config Frame (Initially hidden to the left) ---
        self.config_frame = ctk.CTkFrame(self.right_frame_container, fg_color="transparent")
        self.config_frame.place(relx=-1, rely=0, relwidth=1, relheight=1)  # Start off-screen

        self.setup_config_controls()

    def setup_main_controls(self):
        """Create the widgets for the main control panel"""
        # --- Section 1: Setup ---
        setup_frame = ctk.CTkFrame(self.main_controls_frame, fg_color=self.colors["frame_bg"], corner_radius=15)
        setup_frame.pack(fill="x", expand=False, pady=(0, 15))

        ctk.CTkLabel(setup_frame, text="1. Setup", font=self.fonts["heading"], text_color=self.colors["text"]).pack(
            anchor="w", padx=20, pady=(15, 10))

        self.config_status = ctk.CTkLabel(setup_frame, text="❌ Not configured", text_color=self.colors["error"],
                                          font=self.fonts["body"])
        self.config_status.pack(side="right", padx=20, pady=10)
        ctk.CTkButton(setup_frame, text="Configure Email Settings", font=self.fonts["button"],
                      fg_color=self.colors["button"], hover_color=self.colors["button_hover"],
                      command=self.show_config_frame).pack(side="left", padx=20, pady=10)

        # --- Section 2: Files ---
        files_frame = ctk.CTkFrame(self.main_controls_frame, fg_color=self.colors["frame_bg"], corner_radius=15)
        files_frame.pack(fill="x", expand=False, pady=(0, 15))
        ctk.CTkLabel(files_frame, text="2. Add Files", font=self.fonts["heading"], text_color=self.colors["text"]).pack(
            anchor="w", padx=20, pady=(15, 10))

        data_frame = ctk.CTkFrame(files_frame, fg_color="transparent")
        data_frame.pack(fill='x', padx=20, pady=5)
        ctk.CTkLabel(data_frame, text="Data File (Excel/CSV):", font=self.fonts["body"]).pack(anchor="w")
        self.data_label = ctk.CTkLabel(data_frame, text="No file selected", text_color=self.colors["text_light"],
                                       font=self.fonts["small"], anchor="w")
        self.data_label.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(data_frame, text="Browse...", width=80, fg_color=self.colors["button"],
                      hover_color=self.colors["button_hover"], command=self.select_data_file).pack(side="right")

        attach_frame = ctk.CTkFrame(files_frame, fg_color="transparent")
        attach_frame.pack(fill='x', padx=20, pady=10)
        ctk.CTkLabel(attach_frame, text="Attachment (Optional):", font=self.fonts["body"]).pack(anchor="w")
        self.attachment_label = ctk.CTkLabel(attach_frame, text="No file selected",
                                             text_color=self.colors["text_light"], font=self.fonts["small"], anchor="w")
        self.attachment_label.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(attach_frame, text="Browse...", width=80, fg_color=self.colors["button"],
                      hover_color=self.colors["button_hover"], command=self.select_attachment_file).pack(side="right")

        # --- Section 3: Validate & Send ---
        action_frame = ctk.CTkFrame(self.main_controls_frame, fg_color=self.colors["frame_bg"], corner_radius=15)
        action_frame.pack(fill="x", expand=False, pady=(0, 15))
        ctk.CTkLabel(action_frame, text="3. Validate & Send", font=self.fonts["heading"],
                     text_color=self.colors["text"]).pack(anchor="w", padx=20, pady=(15, 10))

        button_grid = ctk.CTkFrame(action_frame, fg_color="transparent")
        button_grid.pack(fill="x", padx=20, pady=10)
        button_grid.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(button_grid, text="Preview Template", fg_color=self.colors["button"],
                      hover_color=self.colors["button_hover"], command=self.preview_email).grid(row=0, column=0,
                                                                                                sticky="ew",
                                                                                                padx=(0, 5))
        ctk.CTkButton(button_grid, text="Validate Data File", fg_color=self.colors["button"],
                      hover_color=self.colors["button_hover"], command=self.validate_files).grid(row=0, column=1,
                                                                                                 sticky="ew",
                                                                                                 padx=(5, 0))

        self.test_var = ctk.BooleanVar()
        ctk.CTkCheckBox(button_grid, text="Send test email first", variable=self.test_var,
                        font=self.fonts["body"]).grid(row=1, column=0, columnspan=2, pady=10, sticky="w")

        ctk.CTkButton(button_grid, text="Send to First 5 (Test)", command=self.send_test_batch).grid(row=2, column=0,
                                                                                                     sticky="ew",
                                                                                                     padx=(0, 5),
                                                                                                     pady=(5, 0))
        ctk.CTkButton(button_grid, text="Send All Emails", command=self.send_bulk_emails).grid(row=2, column=1,
                                                                                               sticky="ew", padx=(5, 0),
                                                                                               pady=(5, 0))

        # --- Section 4: Progress ---
        progress_frame = ctk.CTkFrame(self.main_controls_frame, fg_color=self.colors["frame_bg"], corner_radius=15)
        progress_frame.pack(fill="both", expand=True)

        self.progress_var = ctk.StringVar(value="Ready to start...")
        self.progress_label = ctk.CTkLabel(progress_frame, textvariable=self.progress_var, font=self.fonts["body"],
                                           text_color=self.colors["text_light"])
        self.progress_label.pack(anchor="w", padx=20, pady=(15, 5))

        self.progress_bar = ctk.CTkProgressBar(progress_frame, progress_color=self.colors["accent"])
        self.progress_bar.set(0)
        self.progress_bar.pack(fill='x', padx=20, pady=(0, 10))

        self.log_text = ctk.CTkTextbox(progress_frame, fg_color="#F0F0F0", text_color=self.colors["text_light"],
                                       font=self.fonts["small"])
        self.log_text.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        self.log("Application initialized.")

    def setup_config_controls(self):
        """Create the widgets for the email configuration panel"""
        container = ctk.CTkFrame(self.config_frame, fg_color=self.colors["frame_bg"], corner_radius=15)
        container.pack(fill="both", expand=True)

        ctk.CTkLabel(container, text="Email Configuration", font=self.fonts["heading"],
                     text_color=self.colors["text"]).pack(anchor="w", padx=20, pady=(15, 20))

        # --- Entries ---
        ctk.CTkLabel(container, text="Email Provider:", font=self.fonts["body"]).pack(anchor='w', padx=20)
        self.provider_var = ctk.StringVar(value="Gmail")
        provider_combo = ctk.CTkComboBox(container, variable=self.provider_var,
                                         values=list(self.email_providers.keys()), state="readonly",
                                         command=self.toggle_custom_fields)
        provider_combo.pack(fill='x', padx=20, pady=(2, 10))

        # This frame will contain the custom SMTP fields
        self.custom_frame = ctk.CTkFrame(container, fg_color="transparent")

        ctk.CTkLabel(self.custom_frame, text="Custom SMTP Server:", font=self.fonts["body"]).pack(anchor='w')
        self.custom_server_entry = ctk.CTkEntry(self.custom_frame)
        self.custom_server_entry.pack(fill='x', pady=2)
        ctk.CTkLabel(self.custom_frame, text="SMTP Port:", font=self.fonts["body"]).pack(anchor='w', pady=(5, 0))
        self.custom_port_entry = ctk.CTkEntry(self.custom_frame)
        self.custom_port_entry.pack(fill='x', pady=2)
        self.custom_port_entry.insert(0, "587")

        # Define the rest of the widgets
        self.email_label = ctk.CTkLabel(container, text="Sender Email:", font=self.fonts["body"])
        self.email_entry = ctk.CTkEntry(container)

        self.password_label = ctk.CTkLabel(container, text="App Password:", font=self.fonts["body"])
        self.password_entry = ctk.CTkEntry(container, show="*")

        self.name_label = ctk.CTkLabel(container, text="Your Name:", font=self.fonts["body"])
        self.name_entry = ctk.CTkEntry(container)

        self.designation_label = ctk.CTkLabel(container, text="Your Designation:", font=self.fonts["body"])
        self.designation_entry = ctk.CTkEntry(container)

        # Pack them in order
        self.email_label.pack(anchor='w', padx=20)
        self.email_entry.pack(fill='x', padx=20, pady=2)

        self.password_label.pack(anchor='w', padx=20, pady=(5, 0))
        self.password_entry.pack(fill='x', padx=20, pady=2)

        self.name_label.pack(anchor='w', padx=20, pady=(5, 0))
        self.name_entry.pack(fill='x', padx=20, pady=2)

        self.designation_label.pack(anchor='w', padx=20, pady=(5, 0))
        self.designation_entry.pack(fill='x', padx=20, pady=(2, 15))

        help_text = ctk.CTkLabel(container, text="Note: For Gmail, use an App Password.", wraplength=400,
                                 justify='left', text_color='gray', font=self.fonts["small"])
        help_text.pack(fill='x', padx=20, pady=(15, 5))

        # --- Buttons ---
        button_frame = ctk.CTkFrame(container, fg_color="transparent")
        button_frame.pack(fill='x', padx=20, pady=(20, 0), side="bottom")

        ctk.CTkButton(button_frame, text="Save Configuration", command=self.save_config).pack(side='right',
                                                                                              padx=(10, 0))
        ctk.CTkButton(button_frame, text="Back", command=self.hide_config_frame, fg_color="gray").pack(side='right')

        # Load existing config if available
        if self.config.sender_email: self.email_entry.insert(0, self.config.sender_email)
        if self.config.your_name: self.name_entry.insert(0, self.config.your_name)
        if self.config.your_designation: self.designation_entry.insert(0, self.config.your_designation)

    def toggle_custom_fields(self, *args):
        """Shows or hides the custom SMTP fields based on combobox selection."""
        if self.provider_var.get() == "Custom":
            # **FIX:** Pack the custom frame *before* the next widget (email_label)
            self.custom_frame.pack(fill='x', padx=20, pady=5, before=self.email_label)
        else:
            self.custom_frame.pack_forget()

    def show_config_frame(self):
        """Animates the configuration frame into view."""
        self.toggle_custom_fields()  # ensure correct fields are shown
        for i in range(self.animation_steps + 1):
            pos = i / self.animation_steps
            self.main_controls_frame.place(relx=pos, rely=0, relwidth=1, relheight=1)
            self.config_frame.place(relx=-1 + pos, rely=0, relwidth=1, relheight=1)
            self.root.update()
            time.sleep(self.animation_speed)

    def hide_config_frame(self):
        """Animates the configuration frame out of view."""
        for i in range(self.animation_steps + 1):
            pos = i / self.animation_steps
            self.main_controls_frame.place(relx=pos * -1, rely=0, relwidth=1, relheight=1)
            self.config_frame.place(relx=pos, rely=0, relwidth=1, relheight=1)
            self.root.update()
            time.sleep(self.animation_speed)

        # Reposition frames correctly after animation
        self.main_controls_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.config_frame.place(relx=-1, rely=0, relwidth=1, relheight=1)

    def save_config(self):
        """Saves the email configuration from the UI fields."""
        if not self.email_entry.get() or not self.password_entry.get() or not self.name_entry.get():
            messagebox.showerror("Error", "Please fill in all required fields!")
            return

        self.config.sender_email = self.email_entry.get()
        self.config.password = self.password_entry.get()
        self.config.your_name = self.name_entry.get()
        self.config.your_designation = self.designation_entry.get()

        provider = self.provider_var.get()
        if provider == "Custom":
            self.config.smtp_server = self.custom_server_entry.get()
            self.config.smtp_port = int(self.custom_port_entry.get())
        else:
            self.config.smtp_server = self.email_providers[provider]["server"]
            self.config.smtp_port = self.email_providers[provider]["port"]

        self.config_status.configure(text=f"✅ Configured ({provider})", text_color=self.colors["success"])
        self.log("Email configuration saved successfully!")
        self.hide_config_frame()

    # --- ALL CORE FUNCTIONALITY METHODS BELOW ARE UNCHANGED ---

    def select_data_file(self):
        """Select the main data file"""
        file_types = [
            ("Excel files", "*.xlsx *.xls"),
            ("CSV files", "*.csv"),
            ("All files", "*.*")
        ]
        filename = filedialog.askopenfilename(title="Select Data File", filetypes=file_types)
        if filename:
            self.data_file = filename
            self.data_label.configure(text=os.path.basename(filename), text_color=self.colors["text"])
            self.log(f"Selected data file: {os.path.basename(filename)}")

    def select_attachment_file(self):
        """Select attachment file"""
        filename = filedialog.askopenfilename(title="Select Attachment File")
        if filename:
            self.attachment_file = filename
            self.attachment_label.configure(text=os.path.basename(filename), text_color=self.colors["text"])
            self.log(f"Selected attachment file: {os.path.basename(filename)}")

    def log(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self.log_text.see("end")
        self.root.update_idletasks()

    def create_audit_table(self, agency_audit_df):
        """Creates a professional HTML table from audit data for a specific agency."""
        if agency_audit_df is None or agency_audit_df.empty:
            return "<p><strong>No specific audit observations found for this agency. Please check the main report.</strong></p>"

        html_table = """
<table border="1" style="border-collapse: collapse; width: 100%; margin: 20px 0; font-family: Arial, sans-serif;">
    <thead>
        <tr style="background-color: #0066cc; color: white; font-weight: bold;">
            <th style="padding: 12px 8px; text-align: center; border: 1px solid #ddd;">Sr. No.</th>
            <th style="padding: 12px 8px; text-align: center; border: 1px solid #ddd;">Audit Period</th>
            <th style="padding: 12px 8px; text-align: center; border: 1px solid #ddd;">Types Of Risk</th>
            <th style="padding: 12px 8px; text-align: center; border: 1px solid #ddd;">Main Category</th>
            <th style="padding: 12px 8px; text-align: center; border: 1px solid #ddd;">Audit Check</th>
            <th style="padding: 12px 8px; text-align: center; border: 1px solid #ddd;">Auditor Observations</th>
            <th style="padding: 12px 8px; text-align: center; border: 1px solid #ddd;">Vendor Justifications and Documentations</th>
        </tr>
    </thead>
    <tbody>
"""
        for i, (index, row) in enumerate(agency_audit_df.iterrows()):
            row_color = "#f9f9f9" if i % 2 == 0 else "#ffffff"
            html_table += f"""
        <tr style="background-color: {row_color};">
            <td style="padding: 10px 8px; text-align: center; border: 1px solid #ddd; font-weight: bold;">{i + 1}</td>
            <td style="padding: 10px 8px; border: 1px solid #ddd; vertical-align: top;">{row.get('Audit_Period', 'N/A')}</td>
            <td style="padding: 10px 8px; border: 1px solid #ddd; vertical-align: top;">{row.get('Types_Of_Risk', 'N/A')}</td>
            <td style="padding: 10px 8px; border: 1px solid #ddd; vertical-align: top;">{row.get('Main_Category', 'N/A')}</td>
            <td style="padding: 10px 8px; border: 1px solid #ddd; vertical-align: top;">{row.get('Audit_Check', 'N/A')}</td>
            <td style="padding: 10px 8px; border: 1px solid #ddd; vertical-align: top;">{row.get('Auditor_Observations', 'N/A')}</td>
            <td style="padding: 10px 8px; border: 1px solid #ddd; vertical-align: top; color: #cc0000;"><strong>[To be filled by Vendor]</strong></td>
        </tr>
"""

        html_table += """
    </tbody>
</table>
<p style="margin-top: 15px;"><strong>Note:</strong> Please fill the "Vendor Justifications and Documentations" column with your detailed response and supporting documents for each observation.</p>
"""
        return html_table

    def validate_files(self):
        """Validate selected data file and show summary"""
        if not self.data_file:
            messagebox.showerror("Error", "Please select a data file!")
            return

        try:
            if self.data_file.endswith('.csv'):
                df = pd.read_csv(self.data_file)
            else:
                df = pd.read_excel(self.data_file)

            required_columns = [
                'agency_name', 'agency_location', 'recipient_email', 'agency_person_name',
                'agency_address', 'audit_date', 'cc_to', 'Audit_Period', 'Types_Of_Risk',
                'Main_Category', 'Audit_Check', 'Auditor_Observations'
            ]
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                messagebox.showerror("Validation Error",
                                     f"Missing required columns in the data file:\n{', '.join(missing_columns)}\n\n"
                                     f"Available columns: {', '.join(df.columns)}")
                return

            unique_agencies = df['agency_name'].nunique()
            messagebox.showinfo("Validation Successful",
                                f"✅ File validated successfully!\n\n"
                                f"Total Rows: {len(df)}\n"
                                f"Unique Agencies: {unique_agencies}\n"
                                f"All required columns are present.")

            self.log(f"Validation successful: {len(df)} records for {unique_agencies} agencies.")

        except Exception as e:
            messagebox.showerror("Validation Error", f"Error reading data file: {str(e)}")

    def preview_email(self):
        """Show email preview with sample data"""
        if not self.config.sender_email:
            messagebox.showerror("Error", "Please configure email settings first!")
            return

        sample_data = {
            'date': datetime.now().strftime("%Y-%m-%d"),
            'agency_name': 'Sample Agency Pvt Ltd',
            'agency_address': '123 Business Street, Mumbai, Maharashtra 400001',
            'agency_location': 'Mumbai',
            'audit_date': '2024-01-15',
            'agency_person_name': 'John Doe',
            'your_name': self.config.your_name or "[Your Name]",
            'your_designation': self.config.your_designation or "[Your Designation]",
            'cc_to': 'manager@axisbank.com',
            'audit_table': '<p><strong>Sample audit table will appear here based on the data file.</strong></p>'
        }

        email_body = self.EMAIL_TEMPLATE.substitute(sample_data)

        preview_window = ctk.CTkToplevel(self.root)
        preview_window.title("Email Preview")
        preview_window.geometry("800x600")

        text_area = ctk.CTkTextbox(preview_window, font=("Arial", 10))
        text_area.pack(fill='both', expand=True, padx=10, pady=10)

        text_area.insert('1.0', email_body)
        text_area.configure(state='disabled')

    def send_templated_email(self, agency_info, agency_audit_df, server):
        """Sends a single email for one agency with all its audit data."""
        try:
            data = agency_info.copy()
            data['date'] = datetime.now().strftime("%Y-%m-%d")
            data['your_name'] = self.config.your_name
            data['your_designation'] = self.config.your_designation

            recipient_email = data.get('recipient_email')
            if not recipient_email:
                self.log(f"Skipping agency with empty recipient email: {data.get('agency_name', 'Unknown')}")
                return False, "Skipped"

            cc_emails = [e.strip() for e in str(data.get('cc_to', '')).split(',') if e.strip()]
            audit_date = data.get('audit_date', 'N/A')
            subject = f"{data['agency_name']} {data['agency_location']} - Show Cause Notice for External Audit Observations: Dated {audit_date}"

            data['audit_table'] = self.create_audit_table(agency_audit_df)

            body = self.EMAIL_TEMPLATE.substitute(data)

            msg = MIMEMultipart()
            msg['From'] = f"{self.config.your_name} <{self.config.sender_email}>"
            msg['To'] = recipient_email
            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'html'))

            if self.attachment_file and os.path.exists(self.attachment_file):
                with open(self.attachment_file, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {os.path.basename(self.attachment_file)}',
                )
                msg.attach(part)

            all_recipients = [recipient_email] + cc_emails
            server.sendmail(self.config.sender_email, all_recipients, msg.as_string())
            return True, "Success"

        except Exception as e:
            self.log(f"Failed to send email to {agency_info.get('recipient_email', 'Unknown')}: {str(e)}")
            return False, str(e)

    def send_bulk_emails(self):
        """Send emails to all agencies"""
        self.process_emails(send_all=True)

    def send_test_batch(self):
        """Send emails to first 5 unique agencies only"""
        self.process_emails(send_all=False, limit=5)

    def process_emails(self, send_all=True, limit=5):
        """Main email processing function"""
        if not self.config.sender_email:
            messagebox.showerror("Error", "Please configure email settings first!")
            return

        if not self.data_file:
            messagebox.showerror("Error", "Please select a data file!")
            return

        try:
            self.log("Reading data file...")
            if self.data_file.endswith('.csv'):
                df = pd.read_csv(self.data_file)
            else:
                df = pd.read_excel(self.data_file)

            df = df.fillna('')  # Clean NaN values

            grouped = df.groupby('agency_name')
            agencies_to_process = list(grouped.groups.keys())

            if not send_all:
                agencies_to_process = agencies_to_process[:limit]
                self.log(f"Processing first {len(agencies_to_process)} unique agencies (test mode)")
            else:
                self.log(f"Processing all {len(agencies_to_process)} unique agencies")

            self.log("Connecting to email server...")
            context = ssl.create_default_context()
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.config.sender_email, self.config.password)
                self.log("✅ Successfully connected to email server")

                if self.test_var.get():
                    self.log("Sending test email to sender's address...")
                    first_agency_name = agencies_to_process[0]
                    first_agency_df = grouped.get_group(first_agency_name)
                    test_info = first_agency_df.iloc[0].to_dict()
                    test_info['recipient_email'] = self.config.sender_email
                    test_info['agency_name'] = "[TEST] " + test_info['agency_name']

                    success, _ = self.send_templated_email(test_info, first_agency_df, server)
                    if success:
                        self.log("✅ Test email sent successfully!")
                        result = messagebox.askyesno("Test Email Sent",
                                                     "Test email sent successfully! Do you want to proceed?")
                        if not result:
                            self.log("Bulk sending cancelled by user")
                            return
                    else:
                        messagebox.showerror("Error", "Test email failed! Please check configuration and logs.")
                        return

                self.progress_bar.set(0)
                success_count = 0
                failed_count = 0

                for i, agency_name in enumerate(agencies_to_process):
                    self.progress_var.set(f"Processing {i + 1}/{len(agencies_to_process)}: {agency_name}")
                    self.log(f"Preparing email for: {agency_name}")

                    agency_df = grouped.get_group(agency_name)
                    agency_info = agency_df.iloc[0].to_dict()

                    success, reason = self.send_templated_email(agency_info, agency_df, server)
                    if success:
                        success_count += 1
                        self.log(f"✅ Email sent successfully to {agency_name}")
                    else:
                        failed_count += 1
                        if reason != "Skipped":
                            self.log(f"❌ Failed to send email to {agency_name}")

                    self.progress_bar.set((i + 1) / len(agencies_to_process))
                    self.root.update_idletasks()
                    time.sleep(2)

                self.progress_var.set("Completed!")
                summary_msg = (f"Bulk email process completed!\n\n"
                               f"✅ Successfully sent: {success_count}\n"
                               f"❌ Failed: {failed_count}\n"
                               f"📧 Total agencies processed: {len(agencies_to_process)}")

                self.log(
                    f"SUMMARY: {success_count} sent, {failed_count} failed, {len(agencies_to_process)} total agencies")
                messagebox.showinfo("Process Complete", summary_msg)

        except FileNotFoundError as e:
            error_msg = f"File not found: {str(e)}"
            self.log(f"❌ {error_msg}")
            messagebox.showerror("File Error", error_msg)
        except smtplib.SMTPAuthenticationError:
            error_msg = "SMTP Authentication failed. Check email/password (use App Password for Gmail)."
            self.log(f"❌ {error_msg}")
            messagebox.showerror("Authentication Error", error_msg)
        except Exception as e:
            error_msg = f"An unexpected error occurred: {str(e)}"
            self.log(f"❌ {error_msg}")
            messagebox.showerror("Error", error_msg)

    def run(self):
        """Start the GUI application"""
        self.setup_gui()
        self.root.mainloop()


def main():
    """Main function to start the application"""
    try:
        app = BulkEmailSender()
        app.run()
    except Exception as e:
        print(f"Failed to start application: {e}")
        messagebox.showerror("Startup Error", f"Failed to start application: {e}")


if __name__ == "__main__":
    main()
