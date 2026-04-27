FROM python:3.10-slim

WORKDIR /325_Proj_1

COPY requirements.txt .

RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .
