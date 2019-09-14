FROM python:slim

RUN pip3 install blinkpy

COPY entrypoint.py .
ENTRYPOINT ["python3", "entrypoint.py"]
CMD []
