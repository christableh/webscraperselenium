# Use Node.js 18-alpine as the base image
FROM node:18-alpine

# Install Chromium and ChromeDriver
RUN apk add --no-cache \
    python3 \
    py3-pip \
    make \
    g++ \
    libffi-dev \
    openssl-dev \
    linux-headers \
    chromium \
    chromium-chromedriver

# Create a Python virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# ---------------- PYTHON SETUP ----------------
WORKDIR /app/python_scripts

# Copy Python requirements and install dependencies
COPY python_scripts/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Python scripts into the container
COPY python_scripts/ .

# Set Selenium environment variables
ENV CHROME_BIN=/usr/bin/chromium-browser
ENV CHROME_DRIVER=/usr/bin/chromedriver

# ---------------- REACT SETUP ----------------
WORKDIR /app/react

# Copy React dependencies and install them
COPY react/package*.json ./
RUN npm install

# Copy the React source code and build it
COPY react/ ./
RUN npm run build

# ---------------- EXPRESS SETUP ----------------
WORKDIR /app/express

# Copy Express dependencies and install them
COPY express/package*.json ./
RUN npm install

# Copy the rest of the Express codebase
COPY express/ .

# ---------------- DOCUSAURUS SETUP ----------------
WORKDIR /app/docs

# Copy Docusaurus dependencies and install them
COPY docs/package*.json ./
RUN npm install

# Build the Docusaurus documentation site
COPY docs/ ./
RUN npm run build

# ---------------- RUN ALL SERVICES ----------------
# Expose ports for React, Express, and Docusaurus
EXPOSE 3001 3002 3003

# Install `serve` and `concurrently` globally
RUN npm install -g serve concurrently

# Default working directory
WORKDIR /app

# Use concurrently to run React, Express, and Docusaurus
CMD ["npx", "concurrently", \
    "\"serve -s /app/react/build --listen 3001\"", \
    "\"node /app/express/server.js --port 3002\"", \
    "\"serve -s /app/docs/build --listen 3003\""]
