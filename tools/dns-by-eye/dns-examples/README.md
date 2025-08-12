# DNS By Eye Test Zone Configuration

This directory contains BIND DNS zone files that create a broken subdomain `test.apathy.ca` specifically designed to demonstrate the capabilities of DNS By Eye. The configuration includes various intentional DNS issues that showcase the tool's diagnostic and visualization features.

## What This Demonstrates

The `test.apathy.ca` zone includes several intentional DNS problems:

### 1. **Broken Nameserver References**
- `ns3.broken.example` - Points to a non-existent domain
- Missing glue records for some nameservers
- Partial IPv6 support (some nameservers have AAAA records, others don't)

### 2. **Unreachable Nameservers**
- `ns2.test.apathy.ca` (192.0.2.2) - RFC 5737 test address that may not respond
- `ns4.test.apathy.ca` (203.0.113.4) - Another RFC 5737 test address

### 3. **Delegation Issues**
- Subdomain `sub.test.apathy.ca` with broken delegation
- Missing glue records for subdomain nameservers
- References to non-existent nameservers

### 4. **Response Time Variations**
- Mix of working and non-responsive nameservers
- Different response times to demonstrate slow query detection

## Files Included

- **`apathy.ca.zone`** - Parent zone with delegation to test subdomain
- **`test.apathy.ca.zone`** - Broken test zone with various DNS issues
- **`named.conf.local`** - BIND configuration to load the zones
- **`setup-instructions.md`** - Step-by-step setup guide

## Quick Setup

1. **Copy zone files to BIND directory:**
   ```bash
   sudo cp apathy.ca.zone /etc/bind/zones/
   sudo cp test.apathy.ca.zone /etc/bind/zones/
   sudo chown bind:bind /etc/bind/zones/*.zone
   ```

2. **Add zones to BIND configuration:**
   ```bash
   sudo cat named.conf.local >> /etc/bind/named.conf.local
   ```

3. **Check configuration and reload:**
   ```bash
   sudo named-checkconf
   sudo named-checkzone apathy.ca /etc/bind/zones/apathy.ca.zone
   sudo named-checkzone test.apathy.ca /etc/bind/zones/test.apathy.ca.zone
   sudo systemctl reload bind9
   ```

   **Important**: Make sure to use the correct zone name with the correct zone file:
   - `apathy.ca` zone uses `apathy.ca.zone` file
   - `test.apathy.ca` zone uses `test.apathy.ca.zone` file

4. **Test the broken domain:**
   ```bash
   dig @localhost test.apathy.ca NS
   dig @localhost test.apathy.ca A
   ```

## Expected DNS By Eye Results

When you analyze `test.apathy.ca` with DNS By Eye, you should see:

### **Delegation Chain Visualization**
- Root (.) → ca. → apathy.ca. → test.apathy.ca.
- Clear visualization of each delegation layer
- Response time measurements for each step

### **Nameserver Issues Highlighted**
- **Red boxes** around broken nameservers (ns3.broken.example)
- **Response time warnings** for slow/unresponsive servers
- **Missing glue record** indicators

### **Cross-Reference Analysis**
- Inconsistent responses between nameservers
- Servers that don't reference themselves properly
- Missing or broken nameserver relationships

### **Performance Metrics**
- Slow response indicators (⚠️ SLOW) for problematic servers
- Total response time analysis
- Comparison of nameserver performance

## Testing URLs

Once set up, test these URLs in DNS By Eye:

- **Basic Analysis**: `https://tools.apathy.ca/?domains=test.apathy.ca`
- **Verbose Mode**: `https://tools.apathy.ca/?domains=test.apathy.ca&verbose=true`
- **Multiple DNS Servers**: Try different resolvers to see varying results
- **Subdomain Issues**: `https://tools.apathy.ca/?domains=sub.test.apathy.ca`

## Educational Value

This configuration demonstrates:

1. **DNS Delegation Hierarchy** - How domains delegate authority
2. **Glue Record Importance** - What happens when they're missing
3. **Nameserver Redundancy** - Why multiple NS records matter
4. **Response Time Impact** - How slow DNS affects user experience
5. **Troubleshooting Process** - How to identify and diagnose DNS issues

## Real-World Scenarios

These issues mirror common real-world DNS problems:

- **Hosting migrations** where old nameservers are left in NS records
- **IPv6 deployment** with incomplete AAAA record coverage  
- **Subdomain delegation** to external providers with broken configurations
- **Nameserver maintenance** where some servers become unresponsive
- **Configuration errors** in zone files and glue records

## Cleanup

To remove the test zones:

```bash
# Remove from BIND configuration
sudo nano /etc/bind/named.conf.local  # Remove the zone blocks

# Remove zone files
sudo rm /etc/bind/zones/apathy.ca.zone
sudo rm /etc/bind/zones/test.apathy.ca.zone

# Reload BIND
sudo systemctl reload bind9
```

## Security Note

This configuration uses RFC 5737 test addresses (192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24) which are reserved for documentation and testing. These addresses should not route to real servers, making them safe for demonstration purposes.

The broken nameserver references point to `broken.example` which is also safe as `.example` is reserved for documentation per RFC 2606.
