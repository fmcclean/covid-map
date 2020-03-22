FROM continuumio/miniconda
COPY environment.yml .
RUN conda env update -n base -f environment.yml
COPY . /app
WORKDIR /app
CMD gunicorn app:server