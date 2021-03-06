FROM continuumio/miniconda
COPY environment.yml .
RUN conda env update --quiet -n base -f environment.yml
COPY app /app/
CMD gunicorn app:server --chdir /app