# IPWhale TCP Session Tracking Deployment Guide

## 🎯 Overview

This deployment implements **complete TCP session visibility** for IPWhale, solving the implementation problem of missing public Internet port information. The solution uses enhanced nginx configuration to pass all four TCP session endpoints to the application.

## 🔧 What This Fixes

### **Before (Implementation Problem):**
- ❌ Client Public Port: Unknown (NAT port translation not visible)
- ❌ Server Public IP: Hidden by Docker networking
- ❌ Server Public Port: Obscured by proxy chain
- ❌ Connection ID: Not available

### **After (Complete TCP Session Tracking):**
- ✅ Client Public IP: Real client IP from nginx
- ✅ Client Public Port: Actual client port from TCP session
- ✅ Server Public IP: Server's public IP address  
- ✅ Server Public Port: Server's listening port (443/80)
- ✅ Connection ID: Unique connection identifier

## 📋 Deployment Steps

### 1. **Update Nginx Configuration**

The new `nginx-tools-ssl.conf` includes enhanced headers for IPWhale:

```nginx
# IPWhale - Enhanced with real TCP session information
location /ipwhale/ {
    # Standard proxy headers
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Port $server_port;
    
    # CRITICAL: Pass real TCP session information
    proxy_set_header X-Client-IP $remote_addr;
    proxy_set_header X-Client-Port $remote_port;
    proxy_set_header X-Server-IP $server_addr;
    proxy_set_header X-Server-Port $server_port;
    proxy_set_header X-Connection-ID $connection;
    
    # Additional connection details
    proxy_set_header X-Request-ID $request_id;
    proxy_set_header X-Nginx-Proxy "true";
}
```

### 2. **Deploy Updated Configuration**

```bash
# Navigate to tools-portal directory
cd tools-portal

# Pull latest changes
git pull

# Restart services to apply nginx configuration
docker-compose -f docker-compose-tools-ssl.yaml down
docker-compose -f docker-compose-tools-ssl.yaml up -d

# Verify nginx configuration
docker exec tools-nginx nginx -t
```

### 3. **Verify TCP Session Tracking**

After deployment, IPWhale will display:

```
🔄 NAT/Proxy
Client Public IP: 66.203.207.72
Client Public Port: 49188
Server Public IP: 138.197.146.85
Server Public Port: 443
Connection ID: 12345
Type: Client is behind NAT/proxy - multiple IP addresses detected
```

## 🔍 Technical Implementation

### **Nginx Variables Used:**

- `$remote_addr` - Client's IP address
- `$remote_port` - Client's port number
- `$server_addr` - Server's IP address
- `$server_port` - Server's port number
- `$connection` - Connection serial number

### **IPWhale Application Changes:**

```python
def get_client_info():
    # Get TCP session information from nginx headers
    client_port = request.headers.get('X-Client-Port')
    server_ip = request.headers.get('X-Server-IP')
    server_port = request.headers.get('X-Server-Port')
    connection_id = request.headers.get('X-Connection-ID')
    
    # Enhanced NAT detection with full session info
    nat_info = {
        'client_public_ip': real_client_ip,
        'client_public_port': client_port,
        'server_public_ip': server_ip,
        'server_public_port': server_port,
        'connection_id': connection_id
    }
```

## 🚀 Alternative Deployment Options

### **Option 1: Dedicated IPWhale Container (Maximum Visibility)**

For even more detailed connection information, IPWhale can be deployed with a dedicated IP:

```yaml
# docker-compose-ipwhale-dedicated.yaml
services:
  ipwhale-dedicated:
    build:
      context: ./tools/ipwhale
    ports:
      - "8080:5000"  # Direct port exposure
    networks:
      - host  # Host networking for maximum visibility
```

**Benefits:**
- Direct TCP connection visibility
- No proxy layer obfuscation
- Complete connection metadata
- Real-time connection tracking

### **Option 2: Enhanced Logging**

Enable detailed connection logging in nginx:

```nginx
log_format tcp_session '$remote_addr:$remote_port -> $server_addr:$server_port '
                       'connection=$connection request_id=$request_id '
                       'time=$time_iso8601';

access_log /var/log/nginx/tcp_sessions.log tcp_session;
```

## 📊 Expected Results

### **Complete TCP Session Display:**

```
🔗 Connection Chain Analysis

💻 Your Device
Browser: Mozilla/5.0 (Windows NT 10.0; Win64; x64)...
Client Port: 49188 (ephemeral)

↓ connects to

🔄 NAT/Proxy
Client Public IP: 66.203.207.72
Client Public Port: 49188
Server Public IP: 138.197.146.85
Server Public Port: 443
Connection ID: 12345
Type: Client is behind NAT/proxy - multiple IP addresses detected

↓ forwards to

🐋 IPWhale Server
Server Host: derpy.henrynet.ca
Server IP: 138.197.146.85
Server Port: 443 (HTTPS)
Protocol: HTTPS
```

### **API Endpoints Enhanced:**

```bash
# Full report now includes complete TCP session
curl -s https://derpy.henrynet.ca/ipwhale/api/report

{
  "tcp_session": {
    "client_ip": "66.203.207.72",
    "client_port": "49188",
    "server_ip": "138.197.146.85",
    "server_port": "443",
    "connection_id": "12345"
  },
  "nat_detection": {
    "detected": true,
    "client_public_ip": "66.203.207.72",
    "client_public_port": "49188",
    "server_public_ip": "138.197.146.85",
    "server_public_port": "443"
  }
}
```

## 🔒 Security Considerations

### **Information Exposure:**
- ✅ Real client IP and port visible (expected for network analysis tool)
- ✅ Server IP and port visible (public information)
- ✅ Connection ID visible (useful for debugging)
- ✅ Docker internal IPs still masked for security

### **Rate Limiting:**
```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req zone=api burst=20 nodelay;
```

## 🎉 Success Criteria

After deployment, verify:

1. ✅ **Client Public Port Visible**: No longer "Unknown"
2. ✅ **Server Public IP Displayed**: Real server IP shown
3. ✅ **Connection ID Available**: Unique session identifier
4. ✅ **Complete TCP Session**: All four endpoints visible
5. ✅ **API Endpoints Working**: curl commands return full data

## 🔧 Troubleshooting

### **If TCP session data is missing:**

```bash
# Check nginx headers are being passed
docker exec tools-nginx nginx -T | grep -A 10 "location /ipwhale"

# Verify IPWhale is receiving headers
docker logs ipwhale | grep "TCP Session"

# Test nginx configuration
docker exec tools-nginx nginx -t
```

### **If connection shows as direct when NAT expected:**

- Check X-Forwarded-For headers are being set
- Verify client is actually behind NAT
- Review nginx proxy configuration

## 📈 Performance Impact

- **Minimal**: Additional headers add ~200 bytes per request
- **Logging**: Enhanced logging may increase disk usage
- **Processing**: TCP session parsing adds negligible CPU overhead

This implementation solves the core problem of missing TCP session information while maintaining security and performance standards.
