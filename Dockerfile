FROM python:3.12-slim

# Prevent Python from creating .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies and Google Chrome
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub \
        | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" \
        > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Application directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt

# Copy application
COPY LeaStripper.py .

# Run the application
ENTRYPOINT ["python", "LeaStripper.py"]

#docker build -t lea-stripper .
#docker run --rm lea-stripper https://wol.jw.org/es/wol/d/r4/lp-s/2026401
#
#bash:
#docker run -v $(pwd):/tmp \
# --rm leastripper \
# https://wol.jw.org/es/wol/d/r4/lp-s/2026401 \
# --tmpdir /tmp \
# --keeptmp
#
#win:
#docker run --rm `
#  -v "$(pwd):/tmp" `
#  lea-stripper `
#  "https://wol.jw.org/es/wol/d/r4/lp-s/2026401" `
#  --tmpdir /tmp `
#  --keeptmp