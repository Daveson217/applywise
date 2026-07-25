import re

import httpx

from .base import ATSAdapter, JobPostingData


class LeverAdapter(ATSAdapter):
    name = "lever"
    API_BASE = "https://api.lever.co/v0/postings"

    def detect(self, url: str) -> bool:
        patterns = [
            r"jobs\.lever\.co",
            r"lever\.co",
        ]
        return any(re.search(p, url, re.IGNORECASE) for p in patterns)

    def extract_company_identifier(self, url: str) -> str:
        match = re.search(r"jobs\.lever\.co/(\w[\w-]*)", url, re.IGNORECASE)
        if match:
            return match.group(1)
        match = re.search(r"lever\.co/(\w[\w-]*)", url, re.IGNORECASE)
        if match:
            return match.group(1)
        return ""

    async def fetch_jobs(self, company_identifier: str) -> list[JobPostingData]:
        url = f"{self.API_BASE}/{company_identifier}"
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, params={"mode": "json"})
            response.raise_for_status()
            data = response.json()

        jobs = []
        for job in data:
            location_parts = []
            categories = job.get("categories", {})
            if categories.get("location"):
                location_parts.append(categories["location"])

            jobs.append(
                JobPostingData(
                    external_id=str(job["id"]),
                    title=job.get("text", ""),
                    url=job.get("hostedUrl", ""),
                    location=", ".join(location_parts),
                    description_text=job.get("descriptionPlain", ""),
                )
            )
        return jobs
