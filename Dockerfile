FROM python:3.7 as builder
WORKDIR /app
RUN git clone https://github.com/ondercsn/k12_scraper.git
#COPY . k12_scraper/

FROM python:3.7-slim as runner
WORKDIR /app
COPY --from=builder /app/k12_scraper /app
RUN pip install -r requirements.txt
RUN mkdir -p /downloads
ENTRYPOINT ["python3", "-m", "src.app"]