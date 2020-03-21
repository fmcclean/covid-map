FROM continuumio/miniconda
COPY environment.yml .
RUN conda env update -n base -f environment.yml
COPY app.py .
CMD python app.py -p $PORT