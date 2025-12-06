import socket
import requests
import random
import time
import concurrent.futures
import logging
import sys
from datetime import datetime
from typing import List, Dict, Any, Set, Tuple

# Check and Import Dependencies
try:
    import pyfiglet
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
    from rich.panel import Panel
    from rich.logging import RichHandler
    from rich.text import Text
    from rich.prompt import Confirm, Prompt
except ImportError:
    print("[-] Missing dependencies. Please run: pip install rich requests pyfiglet")
    sys.exit(1)

# Setup Logging
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, show_path=False)]
)

log = logging.getLogger("rich")
console = Console()

# --- Configuration & Constants ---

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
]

# Top 1000 ports (simplified range for this example, or we could use a specific list)
# Using a subset of common ports for speed in demonstration, but logic supports full range
COMMON_PORTS = [
    21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 445, 993, 995, 
    1723, 3306, 3389, 5900, 8080, 8443, 27017, 6379
]
# To scan top 1000, we would use: list(range(1, 1001))
TARGET_PORTS = list(range(1, 1001))

# --- Module 1: Subdomain Hunter ---

class SubdomainHunter:
    """
    Enumerates subdomains using Certificate Transparency logs (crt.sh)
    and verifies which ones are live.
    """
    def fetch_subdomains(self, target_domain: str) -> Set[str]:
        console.print(f"[bold cyan][*] Querying crt.sh for subdomains of {target_domain}...[/bold cyan]")
        url = f"https://crt.sh/?q=%.{target_domain}&output=json"
        subdomains = set()
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        
        for attempt in range(1, 4):
            try:
                response = requests.get(url, headers=headers, timeout=20)
                if response.status_code == 200:
                    try:
                        data = response.json()
                        for entry in data:
                            name_value = entry['name_value']
                            # crt.sh can return multi-line strings
                            for sub in name_value.split('\n'):
                                if "*" not in sub: # Exclude wildcards
                                    subdomains.add(sub)
                        break # Success, exit loop
                    except ValueError:
                        log.warning("[!] crt.sh returned non-JSON response.")
                        break
                elif response.status_code == 429:
                    wait_time = attempt * 5
                    log.warning(f"[!] crt.sh Rate Limit (429). Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    log.warning(f"[!] crt.sh returned status {response.status_code}")
                    break
            except Exception as e:
                log.error(f"[!] Error fetching subdomains: {e}")
                time.sleep(2)
            
        return subdomains

    def verify_live(self, subdomains: Set[str]) -> List[Tuple[str, str]]:
        """
        Resolves subdomains to IPs to check if they are live.
        Returns list of (subdomain, ip).
        """
        live_hosts = []
        console.print(f"[bold cyan][*] Verifying {len(subdomains)} subdomains for liveness...[/bold cyan]")
        
        def resolve(hostname):
            try:
                ip = socket.gethostbyname(hostname)
                return (hostname, ip)
            except:
                return None

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        ) as progress:
            task = progress.add_task("[green]Resolving...", total=len(subdomains))
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                futures = {executor.submit(resolve, sub): sub for sub in subdomains}
                
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    if result:
                        live_hosts.append(result)
                    progress.advance(task)
                    
        return live_hosts

# --- Module 2: Stealth Recon (Removed) ---
# Google Dork features have been removed as requested.

# --- Module 3: Turbo Scanner (Port & Service Scan) ---

class TurboScanner:
    """
    High-speed port scanner with HTTP banner grabbing improvements.
    """
    def __init__(self, threads=50):
        self.threads = threads

    def get_banner(self, ip: str, port: int) -> str:
        """
        Retrieves service banner. Uses requests for HTTP ports, socket for others.
        Truncates to 50 chars.
        """
        banner = "Unknown"
        
        # HTTP/HTTPS Ports
        if port in [80, 443, 8080, 8443]:
            try:
                protocol = "https" if port in [443, 8443] else "http"
                url = f"{protocol}://{ip}:{port}"
                # Fix 1: allow_redirects=True, timeout=5
                response = requests.get(url, allow_redirects=True, timeout=5, verify=False)
                server_header = response.headers.get('Server', 'HTTP Service')
                banner = server_header
            except:
                banner = "HTTP/HTTPS (No Banner)"
        else:
            # Raw Socket Ports
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2)
                s.connect((ip, port))
                # Trigger output
                try:
                    s.send(b'HEAD / \r\n\r\n')
                except:
                    pass
                banner = s.recv(1024).decode('utf-8', errors='ignore').strip()
                s.close()
            except:
                pass

        # Fix 2: Truncate to max 50 chars
        if len(banner) > 50:
            banner = banner[:47] + "..."
        
        return banner if banner else "Unknown"

    def scan_port(self, ip: str, port: int) -> Dict[str, Any]:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            result = s.connect_ex((ip, port))
            s.close()
            
            if result == 0:
                banner = self.get_banner(ip, port)
                return {"ip": ip, "port": port, "status": "Open", "banner": banner}
            else:
                return None
        except:
            return None

    def scan_target(self, ip: str) -> List[Dict[str, Any]]:
        open_ports = []
        # console.print(f"[bold cyan][*] Scanning {ip}...[/bold cyan]")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = {executor.submit(self.scan_port, ip, port): port for port in TARGET_PORTS}
            
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    open_ports.append(result)
                    
        return open_ports

# --- Module 4: Vuln Analyzer ---

class VulnAnalyzer:
    """
    Analyzes banners for known vulnerabilities.
    """
    def __init__(self):
        self.vuln_db = {
            'vsftpd 2.3.4': 'Backdoor Command Execution',
            'Apache/2.2.8': 'Old Version - Multiple CVEs',
            'Telnet': 'Cleartext Protocol',
            'Anonymous': 'Anonymous Access Allowed',
            'Microsoft-IIS/6.0': 'Buffer Overflow Risk',
            'Werkzeug': 'Debug Mode Risk'
        }

    def analyze(self, scan_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        analyzed_results = []
        
        for item in scan_results:
            banner = item.get('banner', '')
            vuln_status = "[green]SAFE[/green]"
            
            for signature, description in self.vuln_db.items():
                if signature.lower() in banner.lower():
                    vuln_status = f"[red bold]CRITICAL: {description}[/red bold]"
                    break
            
            item['vuln_status'] = vuln_status
            analyzed_results.append(item)
            
        return analyzed_results

# --- Main Controller ---

class RagnarokFramework:
    def __init__(self):
        self.sub_hunter = SubdomainHunter()
        self.scanner = TurboScanner()
        self.analyzer = VulnAnalyzer()

    def print_banner(self):
        # Fix 3: Pyfiglet Banner
        ascii_banner = pyfiglet.figlet_format("RAGNAROK")
        console.print(f"[bold red]{ascii_banner}[/bold red]")
        console.print("[bold white]    RED TEAM AUTOMATION FRAMEWORK v2.0[/bold white]")
        console.print("[bold yellow]    Created by Linga[/bold yellow]")
        console.print("[bold white]    ----------------------------------[/bold white]")

    def run(self):
        self.print_banner()
        
        # 1. Input Target
        target_domain = Prompt.ask("[bold yellow]Enter Target Domain[/bold yellow]")
        
        # 2. Subdomain Enumeration
        subdomains = self.sub_hunter.fetch_subdomains(target_domain)
        live_subdomains = []
        
        if subdomains:
            console.print(f"[+] Found {len(subdomains)} unique subdomains.")
            live_subdomains = self.sub_hunter.verify_live(subdomains)
            
            # Display Live Subdomains
            sub_table = Table(title="Live Subdomains")
            sub_table.add_column("Subdomain", style="cyan")
            sub_table.add_column("IP Address", style="green")
            for sub, ip in live_subdomains:
                sub_table.add_row(sub, ip)
            console.print(sub_table)
        else:
            console.print("[-] No subdomains found.")

        # 3. Ask to Scan Subdomains
        targets_to_scan = []
        # Always scan the main domain
        try:
            main_ip = socket.gethostbyname(target_domain)
            targets_to_scan.append((target_domain, main_ip))
        except:
            console.print(f"[!] Could not resolve main domain {target_domain}")

        if live_subdomains:
            if Confirm.ask(f"[bold yellow]Do you want to scan these {len(live_subdomains)} subdomains?[/bold yellow]"):
                targets_to_scan.extend(live_subdomains)

        # 4. Recon & Scanning Loop
        all_findings = []
        
        console.print(f"\n[bold magenta][*] Starting Active Scans on {len(targets_to_scan)} targets...[/bold magenta]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        ) as progress:
            overall_task = progress.add_task("[magenta]Overall Progress", total=len(targets_to_scan))
            
            for domain, ip in targets_to_scan:
                # Scan
                raw_results = self.scanner.scan_target(ip)
                
                # Analyze
                analyzed = self.analyzer.analyze(raw_results)
                
                # Add domain info to results
                for item in analyzed:
                    item['domain'] = domain
                    all_findings.append(item)
                
                progress.advance(overall_task)

        # 5. Final Results
        console.print("\n")
        final_table = Table(title=f"RAGNAROK FINAL REPORT: {target_domain}")
        final_table.add_column("Target Domain", style="cyan")
        final_table.add_column("IP", style="blue")
        final_table.add_column("Port", style="white")
        final_table.add_column("Service Banner", style="magenta")
        final_table.add_column("Vuln Status", style="red")
        
        for item in all_findings:
            final_table.add_row(
                item['domain'],
                item['ip'],
                str(item['port']),
                item['banner'],
                item['vuln_status']
            )
            
        console.print(final_table)

if __name__ == "__main__":
    # Suppress InsecureRequestWarning for cleaner output
    requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
    
    framework = RagnarokFramework()
    framework.run()
