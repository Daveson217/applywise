import re

import httpx

from .base import ATSAdapter, JobPostingData


class WorkableAdapter(ATSAdapter):
    name = "workable"
    API_BASE = "https://apply.workable.com/api/v3/accounts"

    def detect(self, url: str) -> bool:
        return bool(re.search(r"apply\.workable\.com", url, re.IGNORECASE))

    def extract_company_identifier(self, url: str) -> str:
        match = re.search(
            r"apply\.workable\.com/(\w[\w-]*)", url, re.IGNORECASE
        )
        if match:
            return match.group(1)
        return ""

    async def fetch_jobs(self, company_identifier: str) -> list[JobPostingData]:
        url = f"{self.API_BASE}/{company_identifier}/jobs"
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        jobs = []
        for job in data.get("results", []):
            jobs.append(
                JobPostingData(
                    external_id=str(job.get("shortcode", job.get("id", ""))),
                    title=job.get("title", ""),
                    url=job.get("url", ""),
                    location=job.get("location", {}).get("city", ""),
                    description_text=job.get("description", ""),
                )
            )
        return jobs
