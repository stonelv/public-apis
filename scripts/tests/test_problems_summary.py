import pytest
from scripts.extract_apis import APIEntry, generate_problems_summary

class TestProblemsSummary:
    def test_stats_new_fields(self):
        # Create test APIs
        api1 = APIEntry(
            name="API 1",
            description="Test API 1",
            auth_original="",
            auth_normalized="unknown_auth",
            https=True,
            cors=True,
            category="Category 1",
            url="https://example.com/api1",
            domain="example.com",
            slug="api-1-example-com",
            line_no=1,
            problems=["short_description"]
        )
        
        api2 = APIEntry(
            name="API 2",
            description="Test API 2",
            auth_original="API Key",
            auth_normalized="apiKey",
            https=True,
            cors=True,
            category="Category 2",
            url="https://test.com/api2",
            domain="test.com",
            slug="api-2-test-com",
            line_no=2,
            problems=["cross_category_domain"]
        )
        
        apis = [api1, api2]
        summary = generate_problems_summary(apis)
        
        # Check new stats fields
        assert "unique_domains" in summary["stats"]
        assert summary["stats"]["unique_domains"] == 2
        
        assert "unknown_auth_count" in summary["stats"]
        assert summary["stats"]["unknown_auth_count"] == 1
        
        assert "cross_category_domain_count" in summary["stats"]
        assert summary["stats"]["cross_category_domain_count"] == 1
        
        assert "total_problems" in summary["stats"]
        assert summary["stats"]["total_problems"] == 2
    
    def test_problems_examples_limit(self):
        # Create multiple APIs with same problem
        apis = []
        for i in range(10):
            api = APIEntry(
                name=f"API {i}",
                description="Short",  # Short description
                auth_original="",
                auth_normalized="unknown_auth",
                https=True,
                cors=True,
                category=f"Category {i%2}",  # Alternate categories
                url=f"https://example.com/api{i}",
                domain="example.com",
                slug=f"api-{i}-example-com",
                line_no=i+1,
                problems=["short_description"]
            )
            apis.append(api)
        
        summary = generate_problems_summary(apis)
        
        # Check examples limit (should be <=5)
        assert len(summary["problems"]["short_description"]) <= 5
        assert len(summary["problems"]["short_description"]) == 5