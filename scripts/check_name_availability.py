#!/usr/bin/env python3
"""
Name Availability Checker - Python Script
Purpose: Check domain availability and generate report with links for manual verification
Usage: python check_name_availability.py --company "Gambling Excellence" --domain gamblingexcellence.com
"""

import argparse
import socket
import sys
from datetime import datetime
from urllib.parse import quote

class NameAvailabilityChecker:
    def __init__(self, company_name, domain, output_file="name_availability_results.txt"):
        self.company_name = company_name
        self.domain = domain
        self.output_file = output_file
        self.results = []
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def log(self, message, level="INFO"):
        """Log message with timestamp."""
        prefix = f"[{level}]" if level != "INFO" else ""
        print(f"{prefix} {message}")
        self.results.append(f"{prefix} {message}".strip())
    
    def check_dns_resolution(self):
        """Check if domain has DNS records (indicates registration)."""
        self.log(f"Checking DNS resolution for {self.domain}...")
        try:
            ip = socket.gethostbyname(self.domain)
            self.log(f"✗ Domain has DNS record (IP: {ip}) - Likely REGISTERED", "WARN")
            return False  # Domain is registered
        except socket.gaierror:
            self.log(f"✓ Domain has NO DNS record found - May be AVAILABLE", "PASS")
            return True  # Domain might be available
    
    def generate_registrar_links(self):
        """Generate links for domain registrars."""
        self.log("\nDomain Registrar Check Links:")
        
        domain_encoded = quote(self.domain)
        registrars = [
            ("GoDaddy", f"https://www.godaddy.com/domainsearch/find?checkAvailability=1&domainToCheck={domain_encoded}"),
            ("Namecheap", f"https://www.namecheap.com/domains/registration/results/?domain={domain_encoded}"),
            ("Dynadot", f"https://www.dynadot.com/domain/search.html?domain={domain_encoded}"),
            ("Bluehost", f"https://www.bluehost.com/"),
        ]
        
        for name, url in registrars:
            self.log(f"  → {name}: {url}")
    
    def generate_nevada_sos_links(self):
        """Generate links for Nevada Secretary of State."""
        self.log("\nNevada Secretary of State LLC Search:")
        self.log("  → https://www.nvsos.gov/sos/businesses/")
        self.log("     Search for: '" + self.company_name + "' (and variations)")
        self.log("     Variations to check:")
        variations = [
            self.company_name,
            self.company_name.replace(" ", ""),
            self.company_name.replace(" ", "-"),
            self.company_name.upper()
        ]
        for var in set(variations):
            self.log(f"       - {var}")
    
    def generate_trademark_links(self):
        """Generate links for USPTO trademark search."""
        self.log("\nUSPTO Trademark Search (Federal):")
        company_encoded = quote(self.company_name)
        self.log("  → https://www.uspto.gov/trademarks/search")
        self.log("     Use: 'Basic Word Mark Search'")
        self.log("     Search term: '" + self.company_name + "'")
        self.log("     Classes to check: 36 (Financial), 41 (Entertainment), 42 (Software)")
    
    def generate_social_media_links(self):
        """Generate links for social media handle checks."""
        self.log("\nSocial Media Handle Availability:")
        
        # Normalize handle (lowercase, underscores/hyphens)
        handle = self.company_name.lower().replace(" ", "")
        handle_hyphen = self.company_name.lower().replace(" ", "-")
        
        platforms = [
            ("Instagram", f"https://www.instagram.com/{handle}/"),
            ("Twitter/X", f"https://twitter.com/{handle}"),
            ("Facebook", f"https://www.facebook.com/{handle}/"),
            ("LinkedIn", f"https://www.linkedin.com/company/{handle.lower().replace(' ', '-')}/"),
            ("TikTok", f"https://www.tiktok.com/@{handle}/"),
            ("YouTube", f"https://youtube.com/@{handle}/")
        ]
        
        for platform, url in platforms:
            self.log(f"  → {platform}: {url}")
    
    def generate_google_searches(self):
        """Generate Google search links."""
        self.log("\nGoogle Brand Search:")
        
        company_encoded = quote(self.company_name)
        domain_encoded = quote(self.domain)
        
        searches = [
            (f'Exact: "{self.company_name}"', 
             f'https://www.google.com/search?q="{company_encoded}"'),
            (f'Exact: "{self.domain}"', 
             f'https://www.google.com/search?q="{domain_encoded}"'),
            (f'Brand: {self.company_name}', 
             f'https://www.google.com/search?q={company_encoded}'),
        ]
        
        for label, url in searches:
            self.log(f"  → {label}")
            self.log(f"     {url}")
    
    def generate_whois_links(self):
        """Generate WHOIS lookup links."""
        self.log("\nWHOIS & Domain History Lookup:")
        
        whois_services = [
            ("WHOIS.com", f"https://www.whois.com/whois/{self.domain}"),
            ("GoDaddy WHOIS", "https://www.godaddy.com/whois/"),
            ("ICANN Lookup", "https://lookup.icann.org/"),
            ("DNSchecker", f"https://dnschecker.org/#whois/{self.domain}"),
        ]
        
        for name, url in whois_services:
            self.log(f"  → {name}: {url}")
    
    def generate_summary(self):
        """Generate summary checklist."""
        self.log("\n" + "="*60)
        self.log("MANUAL VERIFICATION CHECKLIST", "SUMMARY")
        self.log("="*60)
        
        checks = [
            ("Domain Availability", "Open registrar links above and verify"),
            ("Nevada LLC Name", "Search https://www.nvsos.gov/sos/businesses/"),
            ("Federal Trademark", "Search class 36/41/42 at https://www.uspto.gov"),
            ("Social Media Handles", "Check Instagram, Twitter, Facebook, LinkedIn, TikTok"),
            ("Google Brand Search", "Google exact match and domain variations"),
            ("WHOIS/Domain History", "Check if domain was previously registered")
        ]
        
        for i, (check, instruction) in enumerate(checks, 1):
            self.log(f"  [{i}] {check}")
            self.log(f"      ✓ {instruction}")
    
    def save_results(self):
        """Save results to file."""
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write(f"NAME AVAILABILITY CHECK REPORT\n")
            f.write(f"Generated: {self.timestamp}\n")
            f.write(f"Company: {self.company_name}\n")
            f.write(f"Domain: {self.domain}\n")
            f.write(f"\n{'='*60}\n\n")
            for line in self.results:
                f.write(f"{line}\n")
            f.write(f"\n{'='*60}\n")
            f.write(f"FINAL DECISION:\n")
            f.write(f"[ ] Name is AVAILABLE - proceed with LLC formation\n")
            f.write(f"[ ] Name has CONFLICTS - consider alternate name\n")
            f.write(f"[ ] Name is PARTIALLY available - decide strategy\n")
        
        self.log(f"\n✓ Report saved to: {self.output_file}")
    
    def run(self):
        """Execute all checks."""
        print(f"\n{'='*60}")
        print(f"Business Name Availability Checker")
        print(f"{'='*60}\n")
        
        self.log(f"Company Name: {self.company_name}")
        self.log(f"Domain: {self.domain}")
        self.log(f"Timestamp: {self.timestamp}\n")
        
        # DNS check (automated)
        self.log("="*60)
        self.log("AUTOMATED CHECK: DNS Resolution", "CHECK")
        self.log("="*60)
        dns_available = self.check_dns_resolution()
        
        # Manual checks (links)
        self.log("\n" + "="*60)
        self.log("MANUAL CHECKS: Open Links in Browser", "MANUAL")
        self.log("="*60 + "\n")
        
        self.generate_registrar_links()
        self.log("")
        self.generate_nevada_sos_links()
        self.log("")
        self.generate_trademark_links()
        self.log("")
        self.generate_social_media_links()
        self.log("")
        self.generate_google_searches()
        self.log("")
        self.generate_whois_links()
        self.log("")
        
        # Summary
        self.generate_summary()
        
        # Save results
        self.save_results()
        
        print(f"\n{'='*60}")
        print("NEXT STEPS:")
        print("="*60)
        print("1. Open all links above in your web browser")
        print("2. Verify name/domain availability in each system")
        print("3. Document results in docs/name_availability_checklist.md")
        print("4. If all clear: Proceed to Nevada LLC formation")
        print("5. If conflicts: Choose alternate name and re-run check")
        print(f"\n✓ See {self.output_file} for full report\n")

def main():
    parser = argparse.ArgumentParser(
        description="Check business name availability across registries."
    )
    parser.add_argument(
        "--company", 
        default="Gambling Excellence", 
        help="Company name to check (default: Gambling Excellence)"
    )
    parser.add_argument(
        "--domain", 
        default="gamblingexcellence.com", 
        help="Domain to check (default: gamblingexcellence.com)"
    )
    parser.add_argument(
        "--output", 
        default="name_availability_results.txt", 
        help="Output file for results"
    )
    
    args = parser.parse_args()
    
    checker = NameAvailabilityChecker(args.company, args.domain, args.output)
    try:
        checker.run()
    except Exception as e:
        print(f"\n[ERROR] {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
