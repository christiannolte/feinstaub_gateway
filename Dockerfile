FROM python:3-slim

WORKDIR /usr/src/app

# Logs sofort ausgeben, damit sie auch vor einem Neustart sichtbar sind
ENV PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "gateway.py" ]