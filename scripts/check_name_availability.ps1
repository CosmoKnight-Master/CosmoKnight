# Name Availability Checker - PowerShell Script
# Purpose: Check domain availability, generate links for manual checks
# Usage: .\check_name_availability.ps1 -CompanyName "Gambling Excellence"
#
# This script does NOT directly query Nevada SoS or trademark databases (requires API keys).
# Instead, it generates a ready-to-open checklist of links and formats domain lookups.

param(
    [string]$CompanyName = "Gambling Excellence",
    [string]$Domain = "gamblingexcellence.com",
    [string]$OutputFile = "name_availability_results.txt"
)

# Color helpers
function Write-Header {
    param([string]$Text)
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host $Text -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
}

function Write-Section {
    param([string]$Text)
    Write-Host "`n--- $Text ---`n" -ForegroundColor Yellow
}

function Write-Result {
    param([string]$Text, [string]$Status)
    if ($Status -eq "PASS") {
        Write-Host "✓ $Text" -ForegroundColor Green
    } elseif ($Status -eq "FAIL") {
        Write-Host "✗ $Text" -ForegroundColor Red
    } else {
        Write-Host "• $Text" -ForegroundColor White
    }
}

# Initialize output
$output = @()
$output += "NAME AVAILABILITY CHECK REPORT"
$output += "Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$output += "Company Name: $CompanyName"
$output += "Domain: $Domain"
$output += ""

Write-Header "Business Name Availability Checker"
Write-Host "Company: $CompanyName`nDomain: $Domain`n"

# 1. Domain Check (simple)
Write-Section "1. Domain Availability Check"
$output += "1. DOMAIN AVAILABILITY"
$output += "Domain: $Domain"

# Use whois-like check via DNSQuery (Windows built-in)
try {
    $domainParts = $Domain -split '\.'
    if ($domainParts.Count -eq 2) {
        # Simple DNS check (if domain resolves, it likely exists)
        $dnsTest = Resolve-DnsName -Name $Domain -ErrorAction SilentlyContinue
        if ($dnsTest) {
            Write-Result "Domain already has DNS records (may be registered)" "FAIL"
            $output += "Status: REGISTERED (Has DNS records)"
            $output += "Action: Check registrar directly or contact domain owner"
        } else {
            Write-Result "Domain has no DNS records found (may be available)" "PASS"
            $output += "Status: Potentially available"
            $output += "Action: Check registrar (GoDaddy, Namecheap, etc.) manually"
        }
    }
} catch {
    Write-Result "Could not query DNS for $Domain (check manually)" "FAIL"
    $output += "Status: Check registrar manually"
}

Write-Host "`nRegistrar Links (open these in browser):" -ForegroundColor White
$registrars = @(
    "https://www.godaddy.com/domainsearch/find?checkAvailability=1&domainToCheck=$Domain",
    "https://www.namecheap.com/domains/registration/results/?domain=$Domain",
    "https://www.namecheap.com/domains/registration/results/?domain=$Domain",
    "https://whois.godaddy.com/?isc=gd_com"
)

foreach ($reg in $registrars) {
    Write-Host "  → $reg" -ForegroundColor Blue
}

$output += ""
$output += "Registrar Check URLs:"
$output += "GoDaddy: https://www.godaddy.com/domainsearch/find?checkAvailability=1&domainToCheck=$Domain"
$output += "Namecheap: https://www.namecheap.com/domains/registration/results/?domain=$Domain"

# 2. Nevada Secretary of State Check
Write-Section "2. Nevada Secretary of State LLC Search"
$output += ""
$output += "2. NEVADA SECRETARY OF STATE LLC SEARCH"
$output += "URL: https://www.nvsos.gov/sos/businesses/"
Write-Result "Visit Nevada SoS and search '$CompanyName' manually" "INFO"
Write-Host "`nSteps:
  1. Go to https://www.nvsos.gov/sos/businesses/
  2. Click 'Business Search'
  3. Enter '$CompanyName' and click Search
  4. Note: variations like 'Gambling-Excellence', 'GamblingExcellence' also
  5. Screenshot results for your records
" -ForegroundColor White

$output += "Manual steps:"
$output += "1. Open https://www.nvsos.gov/sos/businesses/"
$output += "2. Click 'Business Search'"
$output += "3. Search: $CompanyName"
$output += "4. Also search variations: GamblingExcellence, Gambling-Excellence"
$output += "5. Document results"

# 3. USPTO Trademark Search
Write-Section "3. USPTO Trademark Search (Federal)"
$output += ""
$output += "3. USPTO TRADEMARK SEARCH"
$output += "URL: https://www.uspto.gov/trademarks/search"
Write-Host "TESS (Trademark Electronic Search System):
  1. Go to https://www.uspto.gov/trademarks/search
  2. Click 'Basic Word Mark Search'
  3. Enter: $CompanyName
  4. Review results for conflicts
  5. Check classes: 36 (Financial), 41 (Entertainment), 42 (Software)
" -ForegroundColor White

$output += "Manual steps:"
$output += "1. Open https://www.uspto.gov/trademarks/search"
$output += "2. Use 'Basic Word Mark Search'"
$output += "3. Search term: $CompanyName"
$output += "4. Classes to check: 36 (Financial Services), 41 (Entertainment), 42 (Software)"
$output += "5. Document any conflicting marks"

# 4. Social Media Handles
Write-Section "4. Social Media Handle Availability"
$output += ""
$output += "4. SOCIAL MEDIA HANDLES"

$handles = @(
    @{Platform="Instagram"; URL="https://www.instagram.com/gamblingexcellence/"},
    @{Platform="Twitter/X"; URL="https://twitter.com/gamblingexcellence"},
    @{Platform="Facebook"; URL="https://www.facebook.com/gamblingexcellence"},
    @{Platform="LinkedIn"; URL="https://www.linkedin.com/company/gamblingexcellence"}
)

foreach ($handle in $handles) {
    Write-Host "  → $($handle.Platform): $($handle.URL)" -ForegroundColor Blue
    $output += "$($handle.Platform): $($handle.URL)"
}

# 5. Google Brand Search
Write-Section "5. Google Brand Search"
$output += ""
$output += "5. GOOGLE BRAND SEARCH"
$googleSearches = @(
    "https://www.google.com/search?q=" + '"Gambling Excellence"',
    "https://www.google.com/search?q=" + '"gamblingexcellence.com"',
    "https://www.google.com/search?q=" + 'gamblingexcellence'
)

foreach ($search in $googleSearches) {
    Write-Host "  → $search" -ForegroundColor Blue
    $output += "Google Search: $search"
}

# 6. Whois Lookup
Write-Section "6. Whois & Domain History"
$output += ""
$output += "6. WHOIS LOOKUP"

Write-Host "Check domain history at:" -ForegroundColor White
$whoisServices = @(
    "https://www.whois.com/whois/$Domain",
    "https://www.godaddy.com/whois/",
    "https://whoisguard.com/"
)

foreach ($whois in $whoisServices) {
    Write-Host "  → $whois" -ForegroundColor Blue
    $output += "Whois service: $whois"
}

# 7. Results Summary
Write-Section "Summary & Next Steps"
$output += ""
$output += "=" * 50
$output += "CHECKLIST SUMMARY"
$output += "=" * 50

$checklist = @(
    @{Item="1. Domain ($Domain)"; Status="[ ] Complete"; Instruction="Open registrar links above and verify availability"},
    @{Item="2. Nevada SoS ($CompanyName LLC)"; Status="[ ] Complete"; Instruction="Search https://www.nvsos.gov/sos/businesses/"},
    @{Item="3. USPTO Trademark"; Status="[ ] Complete"; Instruction="Search class 36, 41, 42 at https://www.uspto.gov"},
    @{Item="4. Social Media Handles"; Status="[ ] Complete"; Instruction="Check Instagram, Twitter, Facebook, LinkedIn"},
    @{Item="5. Google Brand Search"; Status="[ ] Complete"; Instruction="Google exact match and domain"},
    @{Item="6. Whois/Domain History"; Status="[ ] Complete"; Instruction="Check if domain was previously registered"}
)

foreach ($item in $checklist) {
    Write-Host "$($item.Status) $($item.Item)" -ForegroundColor White
    Write-Host "        → $($item.Instruction)" -ForegroundColor Gray
    $output += "$($item.Status) $($item.Item) - $($item.Instruction)"
}

Write-Host "`n✓ All checks complete when all items are marked [ ]" -ForegroundColor Green

$output += ""
$output += "FINAL DECISION:"
$output += "[ ] Name is available — proceed with Nevada LLC formation"
$output += "[ ] Name has conflicts — consider alternate name"
$output += "[ ] Name is partially available (e.g., domain taken, LLC available) — decide strategy"

# Save output to file
$output | Out-File -FilePath $OutputFile -Encoding UTF8
Write-Host "`nResults saved to: $OutputFile`n" -ForegroundColor Green

Write-Header "Next Steps"
Write-Host @"
1. COMPLETE ALL MANUAL CHECKS above (open each link in your browser)
2. FILL IN RESULTS in docs/name_availability_checklist.md
3. IF ALL CLEAR:
   - Proceed to Nevada LLC formation (docs/nevada_llc_formation_guide.md)
   - Consult gaming attorney about license (docs/gambling_license_checklist.md)
4. IF CONFLICTS:
   - Choose alternate lname
   - Repeat checks for alternate
   - Return to step 1

Questions? See docs/name_availability_checklist.md for detailed instructions.
"@
