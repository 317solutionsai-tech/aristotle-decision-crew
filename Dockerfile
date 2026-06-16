# For hosting on AWS App Runner (simplest) or any container host.
FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir "crewai[tools]" fastapi "uvicorn[standard]"
COPY server.py .
ENV MODEL=gpt-4o-mini
EXPOSE 8000
CMD ["uvicorn","server:app","--host","0.0.0.0","--port","8000"]
