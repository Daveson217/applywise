from ats_adapters.ashby import AshbyAdapter
from ats_adapters.greenhouse import GreenhouseAdapter
from ats_adapters.lever import LeverAdapter
from ats_adapters.registry import detect_ats_from_url
from ats_adapters.smartrecruiters import SmartRecruitersAdapter
from ats_adapters.workable import WorkableAdapter


class TestGreenhouseAdapter:
    def test_detect_boards_url(self):
        adapter = GreenhouseAdapter()
        assert adapter.detect("https://boards.greenhouse.io/stripe")
        assert adapter.detect("https://boards.greenhouse.io/anthropic/jobs/123")

    def test_detect_non_greenhouse(self):
        adapter = GreenhouseAdapter()
        assert not adapter.detect("https://careers.google.com")

    def test_extract_slug(self):
        adapter = GreenhouseAdapter()
        assert adapter.extract_company_identifier("https://boards.greenhouse.io/stripe") == "stripe"
        assert (
            adapter.extract_company_identifier("https://boards.greenhouse.io/anthropic/jobs/123")
            == "anthropic"
        )


class TestLeverAdapter:
    def test_detect(self):
        adapter = LeverAdapter()
        assert adapter.detect("https://jobs.lever.co/netflix")
        assert not adapter.detect("https://careers.google.com")

    def test_extract_slug(self):
        adapter = LeverAdapter()
        assert adapter.extract_company_identifier("https://jobs.lever.co/netflix") == "netflix"


class TestAshbyAdapter:
    def test_detect(self):
        adapter = AshbyAdapter()
        assert adapter.detect("https://jobs.ashbyhq.com/linear")
        assert not adapter.detect("https://lever.co/test")

    def test_extract_slug(self):
        adapter = AshbyAdapter()
        assert adapter.extract_company_identifier("https://jobs.ashbyhq.com/linear") == "linear"


class TestWorkableAdapter:
    def test_detect(self):
        adapter = WorkableAdapter()
        assert adapter.detect("https://apply.workable.com/company-x")
        assert not adapter.detect("https://greenhouse.io/test")

    def test_extract_slug(self):
        adapter = WorkableAdapter()
        assert (
            adapter.extract_company_identifier("https://apply.workable.com/company-x")
            == "company-x"
        )


class TestSmartRecruitersAdapter:
    def test_detect(self):
        adapter = SmartRecruitersAdapter()
        assert adapter.detect("https://careers.smartrecruiters.com/company")
        assert not adapter.detect("https://lever.co/test")


class TestATSRegistry:
    def test_detect_greenhouse_url(self):
        result = detect_ats_from_url("https://boards.greenhouse.io/stripe")
        assert result is not None
        assert result[0] == "greenhouse"
        assert result[1] == "stripe"

    def test_detect_lever_url(self):
        result = detect_ats_from_url("https://jobs.lever.co/netflix")
        assert result is not None
        assert result[0] == "lever"
        assert result[1] == "netflix"

    def test_detect_unknown_url(self):
        result = detect_ats_from_url("https://careers.randomcompany.com")
        assert result is None
