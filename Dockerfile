FROM continuumio/miniconda
COPY environment.yml .
RUN conda env update -n base -f environment.yml
COPY app.py .
COPY CountyUAs_cases_table.csv .
COPY la-boundaries-simple.geojson .
CMD python app.py -p $PORT