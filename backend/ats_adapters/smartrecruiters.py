import re

import httpx

from .base import ATSAdapter, JobPostingData


class SmartRecruitersAdapter(ATSAdapter):
    name = "smartrecruiters"
    API_BASE = "https://api.smartrecruiters.com/v1/companies"

    def detect(self, url: str) -> bool:
        return bool(re.search(r"smartrecruiters\.com", url, re.IGNORECASE))

    def extract_company_identifier(self, url: str) -> str:
        match = re.search(r"smartrecruiters\.com/(\w[\w-]*)", url, re.IGNORECASE)
        if match:
            return match.group(1)
        return ""

    async def fetch_jobs(self, company_identifier: str) -> list[JobPostingData]:
        url = f"{self.API_BASE}/{company_identifier}/postings"
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, params={"limit": 100})
            response.raise_for_status()
            data = response.json()

        jobs = []
        for job in data.get("content", []):
            location = ""
            loc = job.get("location", {})
            if loc.get("city"):
                location = loc["city"]
                if loc.get("region"):
                    location += f", {loc['region']}"

            ref_url = job.get("ref", "")

            jobs.append(
                JobPostingData(
                    external_id=str(job.get("id", "")),
                    title=job.get("name", ""),
                    url=ref_url,
                    location=location,
                )
            )
        return jobs
