FROM node:16.16.0
ENV PYTHONUNBUFFERED=1
# ENV DEBUG="True"
WORKDIR /usr/src/app
RUN apt-get update || : && apt-get install python3 python3-pip -y && rm -rf /var/lib/apt/lists/*
COPY ./ ./
WORKDIR /usr/src/app/frontend
RUN npm ci --dev && ./node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./" && pip3 install -r ../requirements.txt
WORKDIR /usr/src/app/backend
EXPOSE 8000
CMD ["sh", "-c", "python3 manage.py migrate && python3 manage.py runserver 0.0.0.0:8000"] 