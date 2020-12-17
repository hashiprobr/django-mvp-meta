ARG python_version
FROM python:$python_version
ENV PYTHONUNBUFFERED 1
RUN apt-get update &&\
    apt-get -y install libmemcached-dev
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY test_requirements.txt .
RUN pip install -r test_requirements.txt
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb &&\
    apt-get -y install ./google-chrome-stable_current_amd64.deb
RUN wget https://chromedriver.storage.googleapis.com/`curl https://chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip &&\
    unzip chromedriver_linux64.zip -d /usr/bin
ARG base_dir
COPY $base_dir /usr/src/$base_dir
WORKDIR /usr/src/$base_dir
RUN pip install -r requirements.txt
ARG base_name
ENV DJANGO_SETTINGS_MODULE=$base_name.settings
ENTRYPOINT gunicorn `echo $DJANGO_SETTINGS_MODULE | head -c -10`.asgi:application -w 4 -k uvicorn.workers.UvicornWorker -b :8000
