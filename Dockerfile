FROM public.ecr.aws/awsguru/aws-lambda-adapter:1.0.0-rc1 AS adapter
FROM python:3.12-slim

WORKDIR /app
COPY --from=adapter /lambda-adapter /opt/extensions/lambda-adapter

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .

ENV MCP_TRANSPORT=sse
ENV PORT=8080
ENV FASTMCP_PORT=8080
ENV FASTMCP_HOST=0.0.0.0
ENV AWS_LWA_PORT=8080
ENV AWS_LWA_READINESS_CHECK_PATH=/sse
EXPOSE 8080

CMD ["python", "server.py"]
