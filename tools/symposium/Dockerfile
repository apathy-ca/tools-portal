FROM node:18-alpine

WORKDIR /app

# Update package list and install curl for health checks
RUN apk update && apk add --no-cache curl

# Copy package files first for better caching
COPY package*.json ./

# Install dependencies with increased timeout
RUN npm install --timeout=300000

# Copy source code
COPY . .

# Build the application for production
RUN npm run build

# Create .next directory with proper permissions
RUN mkdir -p node_modules .next

# Expose port 5000 to match tools-portal pattern
EXPOSE 5000

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:5000/api/health || exit 1

# Start in production mode
CMD ["npm", "start"]
