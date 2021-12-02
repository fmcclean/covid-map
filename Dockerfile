FROM python:3.7
COPY environment.yml .
RUN pip install -r requirements.txt
COPY app /app/
CMD gunicorn app:server --chdir /app