"""Unit tests for tier-2 fuzzy/synonym matching."""

from apps.watchlist.matching import (
    contains_any,
    expand_synonyms,
    infer_job_types,
    is_us_location,
    location_matches,
    matches,
)


class TestExpandSynonyms:
    def test_expands_known_group(self):
        # Typing "ml" should also pull in "machine learning" etc.
        result = expand_synonyms(["ml"])
        assert "ml" in result
        assert "machine learning" in result
        assert "ai/ml" in result

    def test_unknown_term_passes_through(self):
        assert expand_synonyms(["rust"]) == {"rust"}

    def test_normalizes_case_and_whitespace(self):
        assert expand_synonyms(["  ML  "]) >= {"ml", "machine learning"}

    def test_empty_and_blank_terms_skipped(self):
        assert expand_synonyms(["", "  ", "python"]) == {"python"}


class TestContainsAny:
    def test_word_boundary_prevents_partial_match(self):
        # "ai" must NOT match "paid" — the classic false positive.
        assert contains_any("paid intern", {"ai"}) is False

    def test_word_boundary_allows_real_match(self):
        assert contains_any("AI Engineer", {"ai"}) is True

    def test_multiword_phrase_matches(self):
        assert contains_any("Senior Machine Learning Engineer", {"machine learning"}) is True

    def test_case_insensitive(self):
        assert contains_any("SOFTWARE ENGINEER", {"software engineer"}) is True

    def test_empty_terms_returns_false(self):
        assert contains_any("anything", set()) is False


class TestInferJobTypes:
    def test_internship_title(self):
        assert "internship" in infer_job_types("Software Engineering Intern")

    def test_coop_variants(self):
        assert "internship" in infer_job_types("SWE Co-op")
        assert "internship" in infer_job_types("SWE Coop 2026")

    def test_summer_year(self):
        assert "internship" in infer_job_types("Summer 2026 Intern")

    def test_new_grad(self):
        assert "new_grad" in infer_job_types("New Grad Software Engineer")
        assert "new_grad" in infer_job_types("Entry-Level Data Analyst")

    def test_full_time(self):
        assert "full_time" in infer_job_types("Full-time Backend Engineer")

    def test_no_type(self):
        assert infer_job_types("Software Engineer") == set()


class TestIsUSLocation:
    def test_state_abbr(self):
        assert is_us_location("Mountain View, CA") is True
        assert is_us_location("Pittsburgh, PA") is True

    def test_state_name(self):
        assert is_us_location("Austin, Texas") is True

    def test_explicit_country(self):
        assert is_us_location("Remote - US") is True
        assert is_us_location("New York, NY, USA") is True

    def test_remote_treated_as_us(self):
        assert is_us_location("Remote") is True

    def test_non_us_rejected(self):
        assert is_us_location("London, UK") is False
        assert is_us_location("Berlin, Germany") is False
        assert is_us_location("Toronto, Canada") is False

    def test_empty(self):
        assert is_us_location("") is False

    def test_abbr_not_matched_inside_word(self):
        # "ca" must not match inside "Canada" (word boundary).
        assert is_us_location("Canada") is False


class TestLocationMatches:
    def test_country_matches_state(self):
        assert location_matches("San Francisco, CA", ["united states"]) is True

    def test_country_rejects_foreign(self):
        assert location_matches("London, UK", ["united states"]) is False

    def test_city_precision(self):
        assert location_matches("Pittsburgh, PA", ["pittsburgh"]) is True
        assert location_matches("Austin, TX", ["pittsburgh"]) is False

    def test_state_abbr_precision(self):
        assert location_matches("San Jose, CA", ["ca"]) is True
        assert location_matches("Austin, TX", ["ca"]) is False

    def test_remote_synonym_precision(self):
        assert location_matches("Fully Remote", ["remote"]) is True

    def test_empty_filter_is_match_all(self):
        assert location_matches("anywhere", []) is True

    def test_multiple_terms_or(self):
        # Any one term matching is enough. City/state precision is substring,
        # so "tx" matches "Austin, TX" (state name↔abbr are not cross-mapped).
        assert location_matches("Austin, TX", ["new york", "tx"]) is True
        assert location_matches("New York, NY", ["new york", "boston"]) is True


class TestMatches:
    def test_empty_rule_matches_everything(self):
        assert matches(title="Anything Goes") is True

    def test_keyword_positive(self):
        assert matches(title="ML Engineer", keywords=["ml"]) is True

    def test_keyword_synonym_expansion(self):
        # User asked for "ml" — posting title says "Machine Learning". Should match.
        assert matches(title="Senior Machine Learning Engineer", keywords=["ml"]) is True

    def test_keyword_no_match(self):
        assert matches(title="Marketing Manager", keywords=["ml"]) is False

    def test_exclusion_wins_over_positive(self):
        # Keyword "engineer" matches, but "senior" is excluded → skip.
        assert (
            matches(
                title="Senior Software Engineer",
                keywords=["engineer"],
                exclude_keywords=["senior"],
            )
            is False
        )

    def test_location_filter(self):
        assert matches(title="SWE", location="New York, NY", locations=["new york"]) is True
        assert matches(title="SWE", location="London, UK", locations=["new york"]) is False

    def test_location_remote_synonyms(self):
        # "remote" in rule should also match "Fully Remote" in posting.
        assert matches(title="SWE", location="Fully Remote", locations=["remote"]) is True

    def test_job_type_filter_matches_internship(self):
        assert matches(title="SWE Intern", job_types=["internship"]) is True

    def test_job_type_filter_rejects_full_time(self):
        # Title says Intern, but user asked for full_time.
        assert matches(title="SWE Intern", job_types=["full_time"]) is False

    def test_job_type_filter_no_inferable_type(self):
        # Title has no type marker → can't satisfy a job_types filter.
        assert matches(title="Software Engineer", job_types=["internship"]) is False

    def test_all_filters_anded(self):
        # Internship in NYC matching ML: all must pass.
        assert (
            matches(
                title="Machine Learning Intern",
                location="New York, NY",
                keywords=["ml"],
                locations=["new york"],
                job_types=["internship"],
            )
            is True
        )
        # Same but wrong location.
        assert (
            matches(
                title="Machine Learning Intern",
                location="Berlin",
                keywords=["ml"],
                locations=["new york"],
                job_types=["internship"],
            )
            is False
        )

    def test_search_description_off_by_default(self):
        # Keyword only in description → no match unless search_description=True.
        assert (
            matches(
                title="Software Engineer",
                description="Work with our ML team.",
                keywords=["ml"],
            )
            is False
        )

    def test_search_description_on(self):
        assert (
            matches(
                title="Software Engineer",
                description="Work with our ML team.",
                keywords=["ml"],
                search_description=True,
            )
            is True
        )

    def test_ai_does_not_match_paid(self):
        # Regression: word-boundary must prevent this classic false positive.
        assert matches(title="Paid Marketing Manager", keywords=["ai"]) is False

    def test_normalized_job_type_accepts_hyphens(self):
        # User may store "new-grad" or "new grad" — both should work.
        assert matches(title="New Grad SWE", job_types=["new-grad"]) is True
        assert matches(title="New Grad SWE", job_types=["new grad"]) is True
