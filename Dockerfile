FROM python:3.11-slim

# Install Chrome
RUN apt-get update && apt-get install -y wget gnupg unzip \
 && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
 && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
 && apt-get update && apt-get install -y google-chrome-stable

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Add ChromeDriver
RUN CHROMEDRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE) && \
 wget -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip && \
 unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
 chmod +x /usr/local/bin/chromedriver

# Set environment variables
ENV PATH="/usr/local/bin:$PATH"

# Copy app code
COPY . /app
WORKDIR /app

# Run script
CMD ["python", "final.py"]
