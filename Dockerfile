FROM public.ecr.aws/awsguru/aws-lambda-adapter:0.8.4 AS adapter
FROM python:3.12-slim

WORKDIR /app
COPY --from=adapter /lambda-adapter /opt/extensions/lambda-adapter

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .

ENV MCP_TRANSPORT=streamable-http
ENV PORT=8080
ENV FASTMCP_PORT=8080
ENV FASTMCP_HOST=0.0.0.0
ENV AWS_LWA_PORT=8080
ENV AWS_LWA_READINESS_CHECK_PROTOCOL=tcp
EXPOSE 8080

CMD ["python", "server.py"]
