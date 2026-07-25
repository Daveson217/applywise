import re

import httpx

from .base import ATSAdapter, JobPostingData


class GreenhouseAdapter(ATSAdapter):
    name = "greenhouse"
    API_BASE = "https://boards-api.greenhouse.io/v1/boards"

    def detect(self, url: str) -> bool:
        patterns = [
            r"boards\.greenhouse\.io",
            r"greenhouse\.io",
            r"grnh\.se",
        ]
        return any(re.search(p, url, re.IGNORECASE) for p in patterns)

    def extract_company_identifier(self, url: str) -> str:
        match = re.search(r"boards\.greenhouse\.io/(\w+)", url, re.IGNORECASE)
        if match:
            return match.group(1)
        match = re.search(r"greenhouse\.io/(?:embed/)?(\w+)", url, re.IGNORECASE)
        if match:
            return match.group(1)
        return ""

    async def fetch_jobs(self, company_identifier: str) -> list[JobPostingData]:
        url = f"{self.API_BASE}/{company_identifier}/jobs"
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, params={"content": "true"})
            response.raise_for_status()
            data = response.json()

        jobs = []
        for job in data.get("jobs", []):
            location = ""
            if job.get("location", {}).get("name"):
                location = job["location"]["name"]

            jobs.append(
                JobPostingData(
                    external_id=str(job["id"]),
                    title=job.get("title", ""),
                    url=job.get("absolute_url", ""),
                    location=location,
                    description_text=job.get("content", ""),
                )
            )
        return jobs
