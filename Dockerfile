FROM python:3

COPY . /pywot
WORKDIR /pywot
RUN pip install -r requirements.txt
RUN python setup.py build
RUN python setup.py install
