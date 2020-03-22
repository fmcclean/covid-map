FROM continuumio/miniconda
COPY environment.yml .
RUN conda env update -n base -f environment.yml
RUN apt-get update && apt-get install -y chromium
COPY . /app
WORKDIR /app
CMD gunicorn app:server