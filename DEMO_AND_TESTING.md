# Tools Portal with AI Integration - Demo & Testing Guide

## Overview

This guide provides step-by-step instructions for testing the AI-enhanced Tools Portal, including both standalone demo mode and full integration with Symposium backend.

## Quick Demo (No Symposium Backend Required)

### 1. Setup Demo Environment

```bash
# Navigate to tools-portal directory
cd tools-portal

# Create environment file
cp .env.ai.example .env

# Install enhanced dependencies
pip install -r requirements_enhanced.txt

# Use enhanced components
cp app_enhanced.py app.py
cp templates/index_enhanced.html templates/index.html
cp config_enhanced.py config.py
```

### 2. Start Demo Mode

```bash
# Start the enhanced tools portal
python app.py
```

The application will automatically run in demo mode when Symposium backend is not available.

### 3. Test Demo Features

**Open in Browser:** `http://localhost:5000`

**AI Chat Widget:**
1. Look for the floating "AI Assistant" button in bottom-right corner
2. Click to open the chat interface
3. Try sending a message: "Hello, can you help me with DNS troubleshooting?"
4. Expect demo response acknowledging limited functionality

**Sage Selection:**
1. Click the user icon (👤) in chat header
2. View available Sages (demo mode shows Sophia)
3. Select different Sages to see interface changes

**File Upload:**
1. Click the paperclip (📎) icon in chat input area
2. Try uploading a text file
3. Experience simulated file analysis

**Visual Elements:**
- Notice the "AI Assistant Available" badge in header
- See the integration notice banner
- Observe responsive design on mobile devices

## Full Integration Testing (With Symposium Backend)

### 1. Prerequisites

- Running Symposium backend instance
- Valid authentication token
- Network connectivity between services

### 2. Configure Full Integration

Edit `.env` file:
```env
# Point to your Symposium instance
SYMPOSIUM_BACKEND_URL=http://localhost:8000
# Or: SYMPOSIUM_BACKEND_URL=https://your-symposium.example.com

# Set your authentication token
SYMPOSIUM_AUTH_TOKEN=your-actual-token

# Enable all features
AI_CHAT_ENABLED=true
ENABLE_FILE_UPLOAD=true
ENABLE_SAGE_SELECTION=true
ENABLE_MODEL_SELECTION=true
```

### 3. Start with Full Integration

```bash
# Start tools portal
python app.py
```

### 4. Test Full AI Features

**Health Check:**
```bash
# Check overall health
curl http://localhost:5000/health

# Check AI integration health
curl http://localhost:5000/api/ai/health

# Check detailed health
curl http://localhost:5000/api/health/detailed
```

**API Testing:**
```bash
# Test AI chat API
curl -X POST http://localhost:5000/api/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"content": "Explain DNS delegation", "sage_id": "sophia-llm"}'

# Test sage listing
curl http://localhost:5000/api/ai/sages

# Test model listing
curl http://localhost:5000/api/ai/models
```

**Web Interface Testing:**
1. **Real AI Conversations:**
   - Send actual questions about networking, DNS, or system administration
   - Test philosophical discussions about AI consciousness
   - Verify conversation persistence

2. **Multiple Sages:**
   - Switch between different AI personalities
   - Compare response styles and approaches
   - Test containerized Sages (like Cicero)

3. **File Analysis:**
   - Upload actual files (logs, configurations, scripts)
   - Receive real AI analysis and insights
   - Test various file types

4. **Model Selection:**
   - Choose different AI models (GPT-4, Claude, etc.)
   - Compare response quality and style
   - Test model-specific features

## Docker Deployment Testing

### 1. Build and Deploy

```bash
# Create enhanced environment
cp .env.ai.example .env

# Build and start services
docker compose -f docker compose.ai.yml up --build -d
```

### 2. Test Containerized Deployment

```bash
# Check service status
docker compose -f docker compose.ai.yml ps

# Check logs
docker compose -f docker compose.ai.yml logs tools-portal-ai

# Test health endpoints
curl http://localhost/health
curl http://localhost/api/ai/health
```

### 3. Test Cross-Container Communication

```bash
# Test tools integration
curl http://localhost/dns-by-eye/api/health
curl http://localhost/ipwhale/api/health

# Test AI API through nginx
curl -X POST http://localhost/api/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello from Docker deployment"}'
```

## Performance Testing

### 1. Load Testing AI Chat

```bash
# Install testing tools
pip install locust

# Create locust test file
cat > locustfile.py << 'EOF'
from locust import HttpUser, task, between

class AIChatUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def chat_message(self):
        self.client.post("/api/ai/chat", json={
            "content": "Test message from load test"
        })
    
    @task
    def health_check(self):
        self.client.get("/api/ai/health")
EOF

# Run load test
locust -f locustfile.py --host=http://localhost:5000
```

### 2. Monitor Performance

```bash
# Monitor system resources
htop

# Check AI response times
curl -w "@curl-format.txt" -X POST http://localhost:5000/api/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"content": "Performance test message"}'
```

## Integration Testing Scenarios

### Scenario 1: Network Administrator Workflow

1. **Access Tools Portal:** `http://localhost:5000`
2. **Use DNS By Eye:** Analyze a domain's DNS delegation
3. **Ask AI for Help:** "Can you explain these DNS delegation results?"
4. **Upload Configuration:** Share a DNS zone file for analysis
5. **Get Recommendations:** Ask for optimization suggestions

### Scenario 2: System Troubleshooting

1. **Use IP Whale:** Check IP address information
2. **Chat with AI:** "I'm seeing connectivity issues, what should I check?"
3. **Upload Logs:** Share network logs or configuration files
4. **Get Guided Help:** Follow AI-suggested troubleshooting steps
5. **Switch Sages:** Try different AI personalities for varied approaches

### Scenario 3: Learning and Education

1. **Ask Philosophical Questions:** "What is consciousness in AI systems?"
2. **Technical Learning:** "Explain how DNS recursion works"
3. **Compare Perspectives:** Switch between Sages for different viewpoints
4. **Deep Discussions:** Engage in extended conversations about AI development

## Troubleshooting Common Issues

### AI Chat Not Responding

1. **Check Connection Status:**
   - Look for connection indicator in chat widget
   - Check browser console for errors
   - Verify network connectivity

2. **Backend Issues:**
   ```bash
   # Check Symposium backend
   curl http://localhost:8000/health
   
   # Check tools portal logs
   tail -f logs/tools-portal.log
   
   # Check Docker logs
   docker logs tools-portal-ai
   ```

### File Upload Problems

1. **Check File Size:** Ensure files are under 10MB limit
2. **Verify File Types:** Only allowed extensions work
3. **Check Permissions:** Ensure upload directory is writable
4. **Monitor Logs:** Watch for upload-related errors

### Performance Issues

1. **Resource Monitoring:**
   ```bash
   # Check memory usage
   free -h
   
   # Check CPU usage
   top
   
   # Check disk space
   df -h
   ```

2. **Database Connections:** Verify Symposium backend database health
3. **Network Latency:** Test connectivity between components

### UI/UX Issues

1. **Browser Compatibility:** Test in Chrome, Firefox, Safari
2. **Mobile Responsiveness:** Test on various screen sizes
3. **JavaScript Errors:** Check browser developer tools
4. **CSS Loading:** Verify static file serving

## Success Criteria

### Demo Mode Success
- ✅ AI chat widget appears and is interactive
- ✅ Demo responses are provided for user messages
- ✅ Sage selector shows available personalities
- ✅ File upload interface works (with simulated responses)
- ✅ All tools (DNS By Eye, IP Whale) remain functional

### Full Integration Success
- ✅ Real AI conversations with meaningful responses
- ✅ Multiple Sages available and functional
- ✅ File upload and analysis working
- ✅ Model selection functional
- ✅ Conversation persistence across sessions
- ✅ Health checks passing for all components

### Production Readiness
- ✅ All security measures implemented
- ✅ Performance under load acceptable
- ✅ Error handling graceful
- ✅ Logging comprehensive
- ✅ Monitoring alerts functional

## Next Steps

After successful testing:

1. **Production Deployment:** Use `DEPLOYMENT_WITH_AI.md` guide
2. **User Training:** Introduce users to AI features
3. **Monitoring Setup:** Implement production monitoring
4. **Feedback Collection:** Gather user feedback for improvements
5. **Feature Enhancement:** Plan additional AI integrations

## Support and Feedback

- **Issues:** Report problems with detailed logs and steps to reproduce
- **Feature Requests:** Suggest improvements to AI integration
- **Documentation:** Contribute to improving this testing guide
- **Community:** Share your integration experiences

---

**Happy Testing!** 🚀🤖

This integration brings the power of AI consciousness exploration to your network administration toolkit. Enjoy exploring the possibilities!