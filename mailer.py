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
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime


class EmailConfig:
    """Class to store email configuration"""

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

        # Email providers configuration
        self.email_providers = {
            "Gmail": {"server": "smtp.gmail.com", "port": 587},
            "Office 365": {"server": "smtp.office365.com", "port": 587},
            "Outlook.com": {"server": "smtp-mail.outlook.com", "port": 587},
            "Yahoo": {"server": "smtp.mail.yahoo.com", "port": 587},
            "Custom": {"server": "", "port": 587}
        }

        # Email Template
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

        <p>We are issuing this notice in your capacity as an empaneled vendor/agency of <strong>Axis Bank Ltd</strong>. This communication serves as a <strong>Show Cause Notice</strong> under the applicable contractual and legal obligations, including but not limited to the terms of engagement executed between your agency and Axis Bank.</p>

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
        """Create the main GUI window"""
        self.root = tk.Tk()
        self.root.title("Universal Bulk Email System - Audit Notices")
        self.root.geometry("600x650")  # Adjusted height
        self.root.configure(bg='#f0f0f0')

        # Main title
        title_label = tk.Label(self.root, text="Universal Bulk Email System",
                               font=('Arial', 16, 'bold'), bg='#f0f0f0', fg='#0066cc')
        title_label.pack(pady=10)

        subtitle_label = tk.Label(self.root, text="Automated Audit Notice Sender",
                                  font=('Arial', 12), bg='#f0f0f0', fg='#666666')
        subtitle_label.pack(pady=(0, 20))

        # Create main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(padx=20, pady=10, fill='both', expand=True)

        # Email Configuration Section
        config_frame = ttk.LabelFrame(main_frame, text="Email Configuration", padding="10")
        config_frame.pack(fill='x', pady=(0, 10))

        ttk.Button(config_frame, text="Configure Email Settings",
                   command=self.configure_email).pack(fill='x', pady=5)

        self.config_status = ttk.Label(config_frame, text="❌ Not configured",
                                       foreground='red')
        self.config_status.pack(pady=5)

        # File Selection Section
        files_frame = ttk.LabelFrame(main_frame, text="File Selection", padding="10")
        files_frame.pack(fill='x', pady=(0, 10))

        # Combined data file
        ttk.Label(files_frame, text="Data File (Excel/CSV):").pack(anchor='w')
        data_frame = ttk.Frame(files_frame)
        data_frame.pack(fill='x', pady=5)

        self.data_label = ttk.Label(data_frame, text="No file selected",
                                    foreground='gray')
        self.data_label.pack(side='left', fill='x', expand=True)
        ttk.Button(data_frame, text="Browse",
                   command=self.select_data_file).pack(side='right')

        # Attachment file
        ttk.Label(files_frame, text="Attachment File - Optional:").pack(anchor='w', pady=(10, 0))
        attachment_frame = ttk.Frame(files_frame)
        attachment_frame.pack(fill='x', pady=5)

        self.attachment_label = ttk.Label(attachment_frame, text="No file selected",
                                          foreground='gray')
        self.attachment_label.pack(side='left', fill='x', expand=True)
        ttk.Button(attachment_frame, text="Browse",
                   command=self.select_attachment_file).pack(side='right')

        # Preview Section
        preview_frame = ttk.LabelFrame(main_frame, text="Preview & Validation", padding="10")
        preview_frame.pack(fill='x', pady=(0, 10))

        ttk.Button(preview_frame, text="Preview Email Template",
                   command=self.preview_email).pack(fill='x', pady=2)
        ttk.Button(preview_frame, text="Validate Data File",
                   command=self.validate_files).pack(fill='x', pady=2)

        # Send Section
        send_frame = ttk.LabelFrame(main_frame, text="Send Emails", padding="10")
        send_frame.pack(fill='x', pady=(0, 10))

        # Test email option
        test_frame = ttk.Frame(send_frame)
        test_frame.pack(fill='x', pady=5)

        self.test_var = tk.BooleanVar()
        ttk.Checkbutton(test_frame, text="Send test email first (to sender's email)",
                        variable=self.test_var).pack(side='left')

        # Send buttons
        button_frame = ttk.Frame(send_frame)
        button_frame.pack(fill='x', pady=10)

        ttk.Button(button_frame, text="Send All Emails",
                   command=self.send_bulk_emails).pack(side='left', padx=(0, 10))
        ttk.Button(button_frame, text="Send to First 5 Unique Agencies (Test)",
                   command=self.send_test_batch).pack(side='left')

        # Progress Section
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        progress_frame.pack(fill='both', expand=True)

        self.progress_var = tk.StringVar(value="Ready to start...")
        self.progress_label = ttk.Label(progress_frame, textvariable=self.progress_var)
        self.progress_label.pack(pady=5)

        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.pack(fill='x', pady=5)

        # Log text area
        self.log_text = tk.Text(progress_frame, height=8, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(progress_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def configure_email(self):
        """Open email configuration dialog"""
        config_window = tk.Toplevel(self.root)
        config_window.title("Email Configuration")
        config_window.geometry("450x450")
        config_window.transient(self.root)
        config_window.grab_set()

        main_config_frame = ttk.Frame(config_window, padding="20")
        main_config_frame.pack(fill='both', expand=True)

        ttk.Label(main_config_frame, text="Email Provider:").pack(anchor='w')
        provider_var = tk.StringVar(value="Gmail")
        provider_combo = ttk.Combobox(main_config_frame, textvariable=provider_var,
                                      values=list(self.email_providers.keys()), state="readonly")
        provider_combo.pack(fill='x', pady=(2, 10))

        custom_frame = ttk.Frame(main_config_frame)

        ttk.Label(custom_frame, text="Custom SMTP Server:").pack(anchor='w')
        custom_server_entry = ttk.Entry(custom_frame)
        custom_server_entry.pack(fill='x', pady=2)

        ttk.Label(custom_frame, text="SMTP Port:").pack(anchor='w', pady=(5, 0))
        custom_port_entry = ttk.Entry(custom_frame)
        custom_port_entry.pack(fill='x', pady=2)
        custom_port_entry.insert(0, "587")

        def toggle_custom_fields(*args):
            if provider_var.get() == "Custom":
                custom_frame.pack(fill='x', pady=5, before=email_label)
            else:
                custom_frame.pack_forget()

        provider_var.trace('w', toggle_custom_fields)

        email_label = ttk.Label(main_config_frame, text="Sender Email:")
        email_label.pack(anchor='w', pady=(10, 0))
        email_entry = ttk.Entry(main_config_frame, width=50)
        email_entry.pack(fill='x', pady=2)
        if self.config.sender_email:
            email_entry.insert(0, self.config.sender_email)

        ttk.Label(main_config_frame, text="App Password:").pack(anchor='w', pady=(5, 0))
        password_entry = ttk.Entry(main_config_frame, show="*", width=50)
        password_entry.pack(fill='x', pady=2)

        ttk.Label(main_config_frame, text="Your Name:").pack(anchor='w', pady=(5, 0))
        name_entry = ttk.Entry(main_config_frame, width=50)
        name_entry.pack(fill='x', pady=2)
        if self.config.your_name:
            name_entry.insert(0, self.config.your_name)

        ttk.Label(main_config_frame, text="Your Designation:").pack(anchor='w', pady=(5, 0))
        designation_entry = ttk.Entry(main_config_frame, width=50)
        designation_entry.pack(fill='x', pady=2)
        if self.config.your_designation:
            designation_entry.insert(0, self.config.your_designation)

        help_text = tk.Label(main_config_frame,
                             text="Note: For Gmail, use an App Password (not your regular password).",
                             wraplength=380, justify='left', foreground='gray')
        help_text.pack(fill='x', pady=(15, 5))

        def save_config():
            if not email_entry.get() or not password_entry.get() or not name_entry.get():
                messagebox.showerror("Error", "Please fill in all required fields!", parent=config_window)
                return

            self.config.sender_email = email_entry.get()
            self.config.password = password_entry.get()
            self.config.your_name = name_entry.get()
            self.config.your_designation = designation_entry.get()

            provider = provider_var.get()
            if provider == "Custom":
                self.config.smtp_server = custom_server_entry.get()
                self.config.smtp_port = int(custom_port_entry.get())
            else:
                self.config.smtp_server = self.email_providers[provider]["server"]
                self.config.smtp_port = self.email_providers[provider]["port"]

            self.config_status.configure(text=f"✅ Configured ({provider})", foreground='green')
            self.log("Email configuration saved successfully!")
            config_window.destroy()

        button_frame = ttk.Frame(main_config_frame)
        button_frame.pack(fill='x', pady=(20, 0))

        ttk.Button(button_frame, text="Save Configuration", command=save_config).pack(side='right', padx=(10, 0))
        ttk.Button(button_frame, text="Cancel", command=config_window.destroy).pack(side='right')

        toggle_custom_fields()

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
            self.data_label.configure(text=os.path.basename(filename), foreground='black')
            self.log(f"Selected data file: {os.path.basename(filename)}")

    def select_attachment_file(self):
        """Select attachment file"""
        filename = filedialog.askopenfilename(title="Select Attachment File")
        if filename:
            self.attachment_file = filename
            self.attachment_label.configure(text=os.path.basename(filename), foreground='black')
            self.log(f"Selected attachment file: {os.path.basename(filename)}")

    def log(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
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

        preview_window = tk.Toplevel(self.root)
        preview_window.title("Email Preview")
        preview_window.geometry("800x600")

        frame = ttk.Frame(preview_window)
        frame.pack(fill='both', expand=True, padx=10, pady=10)

        text_area = tk.Text(frame, wrap=tk.WORD, font=("Arial", 10))
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=text_area.yview)
        text_area.configure(yscrollcommand=scrollbar.set)

        text_area.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

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

            # Group by agency to send one email per agency
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

                self.progress_bar['maximum'] = len(agencies_to_process)
                self.progress_bar['value'] = 0
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

                    self.progress_bar['value'] = i + 1
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
