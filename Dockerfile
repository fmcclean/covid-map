FROM continuumio/miniconda
COPY environment.yml .
RUN conda env update --quiet -n base -f environment.yml
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt-get -qq update && apt install -y ./google-chrome-stable_current_amd64.deb && \
    wget -q https://chromedriver.storage.googleapis.com/2.41/chromedriver_linux64.zip && \
    apt-get -qq install -y unzip && unzip chromedriver_linux64.zip && \
    mv chromedriver /usr/bin/chromedriver && \
    chown root:root /usr/bin/chromedriver && \
    chmod +x /usr/bin/chromedriver
COPY app /app/
CMD gunicorn app:server --chdir /app