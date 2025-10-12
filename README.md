# Axis Bank - Automated Audit Mailer

## Executive Summary

The **Automated Audit Mailer** is a production-grade desktop application developed from scratch to streamline and automate the critical process of sending "Show Cause Notices" to external agencies following audit observations. Developed for Axis Bank, the third-largest private sector bank in India, this tool replaces a time-consuming, manual workflow with a robust, efficient, and error-proof automated solution.

As an **Assistant Manager at Axis Bank**, I single-handedly designed, developed, and led the deployment of this application. It is engineered to be used across the entire banking environment, demonstrating a significant contribution to operational efficiency and compliance.

---

## The Problem: A Manual and Error-Prone Process

Prior to this project, the process of communicating audit findings was entirely manual. The workflow involved:

* **Manual Data Aggregation:** Team members would manually filter and group hundreds of rows of audit observations from large Excel spreadsheets.
* **Repetitive Email Composition:** For each of the dozens of agencies, a separate email had to be composed, with observation data painstakingly copied and pasted.
* **High Risk of Human Error:** This manual process was highly susceptible to errors, such as pasting incorrect data, missing observations, or sending notices to the wrong recipients.
* **Lack of Standardization:** Emails lacked a consistent format, leading to potential miscommunication.
* **Inefficient and Time-Consuming:** The entire process consumed significant man-hours, diverting focus from more critical analytical tasks.

---

## The Solution: A Robust Automation Tool

The Automated Audit Mailer is a sophisticated Python application that transforms this workflow into a simple, three-step process: **select a file, configure settings, and send.**

### Key Features

* **Intuitive Graphical User Interface (GUI):** Built with CustomTkinter, the application provides a modern, user-friendly interface that requires no technical expertise to operate.
* **Bulk Processing from Excel:** The application ingests a single Excel file containing all audit data and processes it in one go.
* **Intelligent Data Handling:**
    * **Automatic Grouping:** It intelligently groups all audit findings for each unique agency.
    * **Multi-Observation Parsing:** It automatically detects and processes rows containing multiple comma-separated observations, correctly creating a detailed list for each one.
* **Dynamic HTML Email Generation:** Using the Jinja2 templating engine, the application generates a professional, standardized, and personalized HTML email for each agency, complete with a formatted table of their specific audit findings.
* **Enterprise Integration:** The application is specifically configured to work within Axis Bank's secure corporate network, connecting to an internal, IT-approved SMTP server.
* **Robust Performance & Reliability:**
    * **Multi-threaded Architecture:** A producer-consumer pattern ensures the UI remains responsive while emails are sent concurrently in the background.
    * **Comprehensive Logging:** It generates detailed logs for diagnostics and provides a clear audit trail of all sent communications.
    * **Progress Tracking:** The UI provides real-time feedback, including a progress bar, status updates, and success/failure counts.

---

## Tech Stack & Architecture

The technologies for this project were carefully selected to ensure robustness, security, and maintainability within a corporate environment.

* **Python:** Chosen as the core programming language for its versatility, powerful data processing libraries, and extensive support for application development.
* **Pandas:** Used for high-performance data manipulation. It is the engine that reads the source Excel file, cleans the data, and performs the complex grouping and normalization (`explode`) of multi-observation rows.
* **CustomTkinter:** The GUI framework used to build the modern and intuitive user interface. It provides a superior look and feel compared to standard Tkinter, making the application more professional.
* **Threading (Producer-Consumer Pattern):** Implemented to ensure the application remains fast and responsive. A "producer" thread reads and processes the data, placing email jobs onto a queue. A pool of "consumer" threads then picks up these jobs and sends the emails concurrently, preventing the UI from freezing.
* **Jinja2:** A powerful templating engine used to separate the email's HTML structure from the Python logic. This allows for easy updates to the email format without changing any application code.
* **Dotenv & Logging:** Used for configuration and diagnostics, respectively. The `.env` file keeps sensitive server details separate from the source code, while the logging module provides essential insights for a production-ready application.

### Architecture

The application follows a modular, multi-layered design to ensure separation of concerns:

`UI Layer (ui.py)` -> `Engine Layer (engine.py)` -> `Data Layer (data_handler.py)` & `Email Layer (email_sender.py)`

This architecture makes the application scalable and easy to maintain.

---

## Implementation within the Axis Bank Environment

Deploying an application in a tier-1 banking environment requires strict adherence to security and compliance protocols. I successfully navigated this process from end to end.

1.  **Initial Challenge:** The primary challenge was that the standard public SMTP servers (like Office 365) are blocked by corporate security policies for automated use.
2.  **Collaboration with IT:** I engaged directly with the **IT Mail Service and Network Security teams** to find a compliant solution.
3.  **Approved Solution:** The IT team provided access to a secure, **internal SMTP relay** (`smtpidc.axisb.com`) operating on a custom port (`2255`). This ensures all communication remains within the bank's secure network perimeter.
4.  **Firewall Configuration:** As per protocol, I raised a **"Skybox" firewall request** to open the port between the user's machine and the internal SMTP server. The rule was configured to use the user's unique **hostname** as the source, making it robust against the dynamic IP addresses typical in a corporate environment.
5.  **Formal Acceptance:** The final step in the deployment process is the **Operational Acceptance Sheet (OAS)**, for which I have already secured the necessary senior management approvals.

This end-to-end process demonstrates not only technical development skills but also the ability to navigate complex enterprise IT governance and deploy a secure, compliant solution.

---

## Setup and Usage

To run the application in a local development environment:

1.  **Prerequisites:**
    * Python 3.8+

2.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd automated-audit-mailer
    ```

3.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```

4.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Configure the environment:**
    * Copy the `.env.example` file to `.env`.
    * Open the `.env` file and fill in your sender details and SMTP server information.

6.  **Run the application:**
    ```bash
    python main.py
    ```

---

## Author

* **Atharva Joshi**
* *Assistant Manager, Axis Bank*
