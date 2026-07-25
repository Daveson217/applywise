from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class JobPostingData:
    external_id: str
    title: str
    url: str
    location: str = ""
    description_text: str = ""
    metadata: dict = field(default_factory=dict)


class ATSAdapter(ABC):
    name: str = ""

    @abstractmethod
    def detect(self, url: str) -> bool:
        """Return True if this URL is hosted on this ATS."""

    @abstractmethod
    async def fetch_jobs(self, company_identifier: str) -> list[JobPostingData]:
        """Fetch all current job postings for a company."""

    @abstractmethod
    def extract_company_identifier(self, url: str) -> str:
        """Pull the company slug/ID from a careers page URL."""
