FROM continuumio/miniconda
COPY environment.yml .
RUN conda env update -f environment.yml