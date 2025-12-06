# Ragnarok - Red Team Automation Framework

![Ragnarok Banner](https://img.shields.io/badge/Status-Active-green) ![Python](https://img.shields.io/badge/Python-3.8%2B-blue) ![License](https://img.shields.io/badge/License-MIT-orange)

**Ragnarok** is a modular, high-speed, and stealthy Red Team framework designed for automated reconnaissance, vulnerability scanning, and exploitation verification. It combines speed (multi-threading) with stealth (User-Agent rotation, adaptive delays) to deliver a professional-grade pentesting experience.

## 🚀 Features

*   **🔍 Subdomain Hunter:**
    *   Enumerates subdomains using Certificate Transparency logs (`crt.sh`).
    *   Verifies live targets using multi-threaded DNS resolution.
    *   Handles rate-limiting and API errors gracefully.

*   **⚡ Turbo Scanner:**
    *   High-speed Port Scanner using `concurrent.futures`.
    *   Intelligent HTTP Banner Grabbing (handles redirects & timeouts).
    *   Adaptive speed control to prevent network congestion.

*   **🛡️ Vulnerability Analyzer:**
    *   Matches service banners against a database of known exploits (e.g., vsftpd 2.3.4, Telnet, Old Apache).
    *   Flags findings as `SAFE` or `CRITICAL`.

*   **📊 Professional Reporting:**
    *   Generates a clean, interactive CLI dashboard using the `rich` library.
    *   Exports findings to a detailed HTML report (`engagement_report.html`).

## 🛠️ Installation

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/LingeshwarKulal/Ragnarok.git
    cd Ragnarok
    ```

2.  **Install Dependencies:**
    ```bash
    pip install rich requests pyfiglet
    ```

## 💻 Usage

Run the main controller script:

```bash
python main.py
```

**Workflow:**
1.  Enter the **Target Domain** (e.g., `example.com`).
2.  The tool will enumerate subdomains and ask if you want to scan them.
3.  Ragnarok will perform port scanning and vulnerability analysis on all selected targets.
4.  View the final results in the terminal and the generated HTML report.

## ⚠️ Disclaimer

**Ragnarok is for EDUCATIONAL and ETHICAL PURPOSES ONLY.**
Usage of this tool for attacking targets without prior mutual consent is illegal. The developers assume no liability and are not responsible for any misuse or damage caused by this program.

---
*Developed by Lingeshwar Kulal*
