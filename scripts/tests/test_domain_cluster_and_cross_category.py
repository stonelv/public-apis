import pytest
from scripts.extract_apis import APIEntry, detect_advanced_problems

class TestDomainClusterAndCrossCategory:
    def test_domain_cluster_detection(self):
        # Create APIs with same domain in same category
        api1 = APIEntry(
            name="API 1",
            description="Test API 1",
            auth_original="",
            auth_normalized="unknown_auth",
            https=True,
            cors=True,
            category="Test Category",
            url="https://example.com/api1",
            domain="example.com",
            slug="api-1-example-com",
            line_no=1,
            problems=[]
        )
        
        api2 = APIEntry(
            name="API 2",
            description="Test API 2",
            auth_original="",
            auth_normalized="unknown_auth",
            https=True,
            cors=True,
            category="Test Category",
            url="https://example.com/api2",
            domain="example.com",
            slug="api-2-example-com",
            line_no=2,
            problems=[]
        )
        
        api3 = APIEntry(
            name="API 3",
            description="Test API 3",
            auth_original="",
            auth_normalized="unknown_auth",
            https=True,
            cors=True,
            category="Test Category",
            url="https://example.com/api3",
            domain="example.com",
            slug="api-3-example-com",
            line_no=3,
            problems=[]
        )
        
        api4 = APIEntry(
            name="API 4",
            description="Test API 4",
            auth_original="",
            auth_normalized="unknown_auth",
            https=True,
            cors=True,
            category="Test Category",
            url="https://example.com/api4",
            domain="example.com",
            slug="api-4-example-com",
            line_no=4,
            problems=[]
        )
        
        apis = [api1, api2, api3, api4]
        detect_advanced_problems(apis)
        
        # All should have domain_cluster problem
        for api in apis:
            assert "domain_cluster" in api.problems
    
    def test_cross_category_domain_detection(self):
        # Create APIs with same domain in different categories
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
            problems=[]
        )
        
        api2 = APIEntry(
            name="API 2",
            description="Test API 2",
            auth_original="",
            auth_normalized="unknown_auth",
            https=True,
            cors=True,
            category="Category 2",
            url="https://example.com/api2",
            domain="example.com",
            slug="api-2-example-com",
            line_no=2,
            problems=[]
        )
        
        apis = [api1, api2]
        detect_advanced_problems(apis)
        
        # Both should have cross_category_domain problem
        assert "cross_category_domain" in api1.problems
        assert "cross_category_domain" in api2.problems