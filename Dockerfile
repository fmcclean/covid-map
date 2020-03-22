FROM continuumio/miniconda
COPY environment.yml .
RUN conda env update -n base -f environment.yml
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN apt-get update && apt install -y ./google-chrome-stable_current_amd64.deb
RUN wget https://chromedriver.storage.googleapis.com/2.41/chromedriver_linux64.zip
RUN apt-get install -y unzip && unzip chromedriver_linux64.zip
RUN mv chromedriver /usr/bin/chromedriver
RUN chown root:root /usr/bin/chromedriver
RUN chmod +x /usr/bin/chromedriver
COPY . /app
WORKDIR /app
CMD gunicorn app:server