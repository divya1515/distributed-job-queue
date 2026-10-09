from locust import HttpUser, task, between
import uuid

CSV_FILE_PATH = "/Users/apple/Desktop/Divya/Distributed Job Queue System/bulk_urls (1).csv"

class BulkUrlJobUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task
    def create_bulk_job(self):
        with open(CSV_FILE_PATH, "rb") as f:
            self.client.post(
                "/jobs/bulk_url_shorten",
                files={"file": ("urls.csv", f, "text/csv")},
                data={"email": "divya.kaushik1515@gmail.com"},
            )