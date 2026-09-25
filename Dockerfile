#build
FROM python:3.12-slim AS builder

WORKDIR /install

COPY requirements.txt .

RUN pip install --no-cache-dir --prefix=/install/deps -r requirements.txt

#runtime
FROM python:3.12-slim

# create a non-root user to run app instead of root
RUN addgroup --system app && adduser --system --ingroup app app

WORKDIR /app

# copy only the installed dependencies from builder stage
COPY --from=builder /install/deps /usr/local

# copy application code/frontend assets
COPY app.py .
COPY index.html .
COPY viewCart.html .
COPY style.css .
COPY cert.pem .
COPY key.pem .

RUN chown -R app:app /app

USER app

EXPOSE 5000
ENV PORT=5000
ENV FLASK_DEBUG=false

CMD ["python", "app.py"]