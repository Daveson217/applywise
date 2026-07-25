import re

import httpx

from .base import ATSAdapter, JobPostingData


class AshbyAdapter(ATSAdapter):
    name = "ashby"
    API_BASE = "https://api.ashbyhq.com/posting-api/job-board"

    def detect(self, url: str) -> bool:
        patterns = [
            r"jobs\.ashbyhq\.com",
            r"ashbyhq\.com",
        ]
        return any(re.search(p, url, re.IGNORECASE) for p in patterns)

    def extract_company_identifier(self, url: str) -> str:
        match = re.search(r"jobs\.ashbyhq\.com/(\w[\w-]*)", url, re.IGNORECASE)
        if match:
            return match.group(1)
        return ""

    async def fetch_jobs(self, company_identifier: str) -> list[JobPostingData]:
        url = f"{self.API_BASE}/{company_identifier}"
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        jobs = []
        for job in data.get("jobs", []):
            location = job.get("location", "")
            if isinstance(location, dict):
                location = location.get("name", "")

            posting_url = f"https://jobs.ashbyhq.com/{company_identifier}/{job.get('id', '')}"

            jobs.append(
                JobPostingData(
                    external_id=str(job["id"]),
                    title=job.get("title", ""),
                    url=job.get("jobUrl", posting_url),
                    location=location if isinstance(location, str) else "",
                    description_text=job.get("descriptionPlain", ""),
                )
            )
        return jobs
