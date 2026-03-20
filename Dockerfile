FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && \
    mkdir -p /opt/extensions && \
    curl -Lo /opt/extensions/lambda-adapter https://github.com/awslabs/aws-lambda-web-adapter/releases/download/v0.8.4/lambda-adapter-x86_64 && \
    chmod +x /opt/extensions/lambda-adapter && \
    apt-get remove -y curl && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .

ENV MCP_TRANSPORT=sse
ENV PORT=8080
ENV AWS_LWA_PORT=8080
ENV AWS_LWA_READINESS_CHECK_PATH=/sse
EXPOSE 8080

CMD ["python", "server.py"]
