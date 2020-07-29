ARG python_version
FROM python:$python_version
ENV PYTHONUNBUFFERED 1
COPY requirements.txt .
RUN pip install -r requirements.txt
ARG base_dir
COPY $base_dir /usr/src/$base_dir
WORKDIR /usr/src/$base_dir
RUN pip install -r requirements.txt
ARG base_name
ENV DJANGO_SETTINGS_MODULE=$base_name.settings
ENTRYPOINT gunicorn `echo $DJANGO_SETTINGS_MODULE | head -c -10`.asgi:application -w 4 -k uvicorn.workers.UvicornWorker -b :8000
