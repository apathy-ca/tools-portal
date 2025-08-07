# Existing Broken Domains for DNS By Eye Testing

Instead of setting up local DNS zones, you can use these existing domains that have various DNS issues for demonstrating DNS By Eye's capabilities.

## Real-World Broken Domains

### 1. **Domains with Missing Glue Records**
- `broken-glue.example.org` (if it exists)
- Look for domains where NS records point to nameservers within the domain but lack A/AAAA glue records

### 2. **Domains with Slow/Unresponsive Nameservers**
- Many expired or abandoned domains have this issue
- Domains with nameservers pointing to decommissioned servers

### 3. **Domains with Mixed IPv4/IPv6 Issues**
- Domains where some nameservers have IPv6 but others don't
- Incomplete AAAA record coverage

## Testing Strategy

### **Use DNS By Eye's Multi-Server Feature**
Test the same domain against different DNS servers to see varying results:

```
Domain: example-with-issues.com
DNS Servers to try:
- 8.8.8.8 (Google)
- 1.1.1.1 (Cloudflare) 
- 9.9.9.9 (Quad9)
- System default
```

### **Look for These Patterns**
1. **Response Time Variations**: Different servers may have different cached results
2. **Inconsistent Results**: Some servers may return different nameserver lists
3. **Timeout Issues**: Some servers may timeout while others succeed

## Common Real-World Issues to Demonstrate

### **1. Hosting Migration Problems**
Many domains have old nameservers still listed in NS records after migrations:
- Old nameservers that no longer respond
- Mix of old and new nameservers
- Inconsistent responses between nameservers

### **2. IPv6 Deployment Issues**
- Domains with partial IPv6 support
- Missing AAAA records for some nameservers
- IPv6-only nameservers that cause issues for IPv4-only clients

### **3. Subdomain Delegation Issues**
- Subdomains delegated to external providers
- Broken delegation chains
- Missing glue records for subdomain nameservers

## Example Domains to Test

### **Large Organizations (Often Have Complex DNS)**
- `microsoft.com` - Complex delegation with many nameservers
- `amazon.com` - Multiple levels of delegation
- `google.com` - Good example of proper DNS setup (for comparison)

### **Government Domains (Sometimes Have Issues)**
- Various `.gov` domains may have configuration issues
- Educational `.edu` domains often have complex setups

### **International Domains**
- Domains from different countries may show interesting delegation patterns
- Different TLD nameserver behaviors

## Creating Your Own Test Cases

### **Temporary Subdomains**
If you control a domain, you can create temporary broken subdomains:

1. **Create NS records** pointing to non-existent nameservers
2. **Add partial glue records** (some A records missing)
3. **Point to slow/unresponsive servers**
4. **Create circular dependencies**

### **Example Configuration for Your Domain**
```
; Add to your existing zone
broken.yourdomain.com.    IN    NS    ns1.broken.yourdomain.com.
broken.yourdomain.com.    IN    NS    ns2.broken.yourdomain.com.
broken.yourdomain.com.    IN    NS    nonexistent.example.

; Add only partial glue
ns1.broken.yourdomain.com.    IN    A    192.0.2.1
; ns2.broken.yourdomain.com missing A record
```

## Testing Methodology

### **1. Start with Working Domains**
- Test known good domains first to establish baseline
- `google.com`, `cloudflare.com`, `github.com` are usually well-configured

### **2. Compare Different DNS Servers**
- Use the same domain with different resolvers
- Look for inconsistencies in results
- Note response time differences

### **3. Use Verbose Mode**
- Enable verbose output to see glue record details
- Look for missing A/AAAA records
- Check for response time variations

### **4. Test Subdomain Delegation**
- Find domains with complex subdomain structures
- Look for delegation to external providers
- Test multiple levels of delegation

## Documentation for Demonstrations

When demonstrating DNS By Eye:

1. **Start with a working domain** to show normal delegation
2. **Show a domain with issues** to highlight problems
3. **Use different DNS servers** to show varying results
4. **Enable verbose mode** to show technical details
5. **Compare multiple domains** to show different patterns

This approach lets you demonstrate DNS By Eye's capabilities without needing to set up local DNS infrastructure.
