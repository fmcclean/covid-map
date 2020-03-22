FROM continuumio/miniconda
RUN apt-get update && apt-get install -y firefox wget
COPY environment.yml .
RUN conda env update -n base -f environment.yml
COPY . /app
WORKDIR /app
CMD gunicorn app:server