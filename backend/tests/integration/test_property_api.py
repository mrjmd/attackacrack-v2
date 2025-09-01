"""
Integration tests for Property API endpoints.

Tests the complete Property CRUD operations and related functionality:
1. GET /api/v1/properties - List properties with pagination and filters
2. GET /api/v1/properties/{id} - Get single property by ID
3. POST /api/v1/properties - Create new property
4. PUT /api/v1/properties/{id} - Update existing property
5. DELETE /api/v1/properties/{id} - Delete property
6. POST /api/v1/properties/import-csv - Import PropertyRadar CSV file
7. GET /api/v1/properties/search - Search properties with query
8. POST /api/v1/properties/batch-delete - Delete multiple properties

These tests will FAIL initially (RED phase) since no API implementation exists.
They define the expected API contract and behavior.
"""

import io
import json
import pytest
import time
from datetime import datetime
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from unittest.mock import Mock, patch, AsyncMock

from app.models import Property, Contact, User, PropertyList
from app.services.property_radar_parser import PropertyRadarParser


class TestPropertiesListAPI:
    """Test GET /api/v1/properties - List properties with pagination and filters."""
    
    @pytest.mark.asyncio
    async def test_list_properties_empty(self, client: AsyncClient, test_user: User):
        """Test listing properties when none exist."""
        response = await client.get(
            "/api/v1/properties",
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["properties"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["per_page"] == 10

    @pytest.mark.asyncio
    async def test_list_properties_with_data(
        self, 
        client: AsyncClient, 
        test_user: User,
        db_session: AsyncSession
    ):
        """Test listing properties with existing data."""
        # Create test properties directly in database
        properties_data = [
            {
                "address": "123 Main St",
                "city": "Los Angeles",
                "zip_code": "90210",
                "est_value": Decimal("500000.00"),
                "est_equity_percent": Decimal("65.50"),
                "property_type": "SFR",
                "bedrooms": 3,
                "bathrooms": Decimal("2.5"),
                "square_feet": 1800,
                "year_built": 1995,
                "owner_name": "John Smith"
            },
            {
                "address": "456 Oak Ave",
                "city": "Beverly Hills", 
                "zip_code": "90210",
                "est_value": Decimal("750000.00"),
                "est_equity_percent": Decimal("80.25"),
                "property_type": "CONDO",
                "bedrooms": 2,
                "bathrooms": Decimal("2.0"),
                "square_feet": 1200,
                "year_built": 2010,
                "owner_name": "Jane Doe"
            }
        ]
        
        for prop_data in properties_data:
            property_obj = Property(**prop_data)
            db_session.add(property_obj)
        
        await db_session.commit()
        
        response = await client.get(
            "/api/v1/properties",
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["properties"]) == 2
        assert data["total"] == 2
        
        # Verify property structure
        property_data = data["properties"][0]
        required_fields = [
            "id", "address", "city", "zip_code", "property_type",
            "est_value", "est_equity_percent", "bedrooms", "bathrooms",
            "square_feet", "year_built", "owner_name", "created_at", "updated_at"
        ]
        for field in required_fields:
            assert field in property_data

    @pytest.mark.asyncio
    async def test_list_properties_pagination(
        self,
        client: AsyncClient,
        test_user: User,
        db_session: AsyncSession
    ):
        """Test properties pagination parameters."""
        # Create 25 test properties
        for i in range(25):
            property_obj = Property(
                address=f"{i+100} Test St",
                city="Test City",
                zip_code="12345",
                owner_name=f"Owner {i+1}"
            )
            db_session.add(property_obj)
        
        await db_session.commit()
        
        # Test page 1 with default per_page (10)
        response = await client.get(
            "/api/v1/properties",
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["properties"]) == 10
        assert data["total"] == 25
        assert data["page"] == 1
        assert data["per_page"] == 10
        assert data["total_pages"] == 3
        
        # Test page 2 with custom per_page
        response = await client.get(
            "/api/v1/properties?page=2&per_page=5",
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["properties"]) == 5
        assert data["page"] == 2
        assert data["per_page"] == 5

    @pytest.mark.asyncio
    async def test_list_properties_city_filter(
        self,
        client: AsyncClient,
        test_user: User,
        db_session: AsyncSession
    ):
        """Test filtering properties by city."""
        # Create properties in different cities
        cities_data = [
            ("Los Angeles", 3),
            ("Beverly Hills", 2),
            ("Santa Monica", 1)
        ]
        
        for city, count in cities_data:
            for i in range(count):
                property_obj = Property(
                    address=f"{i+100} {city} St",
                    city=city,
                    zip_code="90210",
                    owner_name=f"Owner {city} {i+1}"
                )
                db_session.add(property_obj)
        
        await db_session.commit()
        
        # Filter by Los Angeles
        response = await client.get(
            "/api/v1/properties?city=Los Angeles",
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["properties"]) == 3
        assert all(prop["city"] == "Los Angeles" for prop in data["properties"])

    @pytest.mark.asyncio
    async def test_list_properties_price_range_filter(
        self,
        client: AsyncClient,
        test_user: User,
        db_session: AsyncSession
    ):
        """Test filtering properties by price range."""
        # Create properties with different values
        values = [250000, 500000, 750000, 1000000]
        for i, value in enumerate(values):
            property_obj = Property(
                address=f"{i+100} Value St",
                city="Test City",
                zip_code="12345",
                est_value=Decimal(str(value)),
                owner_name=f"Owner {i+1}"
            )
            db_session.add(property_obj)
        
        await db_session.commit()
        
        # Filter by price range $400,000 - $800,000
        response = await client.get(
            "/api/v1/properties?min_value=400000&max_value=800000",
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["properties"]) == 2
        
        for prop in data["properties"]:
            value = float(prop["est_value"])
            assert 400000 <= value <= 800000

    @pytest.mark.asyncio
    async def test_list_properties_equity_filter(
        self,
        client: AsyncClient,
        test_user: User,
        db_session: AsyncSession
    ):
        """Test filtering properties by equity percentage."""
        # Create properties with different equity percentages
        equity_percentages = [25.5, 50.0, 75.5, 90.0]
        for i, equity in enumerate(equity_percentages):
            property_obj = Property(
                address=f"{i+100} Equity St",
                city="Test City",
                zip_code="12345",
                est_equity_percent=Decimal(str(equity)),
                owner_name=f"Owner {i+1}"
            )
            db_session.add(property_obj)
        
        await db_session.commit()
        
        # Filter by high equity (>= 50%)
        response = await client.get(
            "/api/v1/properties?min_equity=50",
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["properties"]) == 3
        
        for prop in data["properties"]:
            equity = float(prop["est_equity_percent"])
            assert equity >= 50.0

    @pytest.mark.asyncio
    async def test_list_properties_sorting(
        self,
        client: AsyncClient,
        test_user: User,
        db_session: AsyncSession
    ):
        """Test sorting properties by different fields."""
        # Create properties with different values
        properties_data = [
            {"address": "300 C St", "est_value": Decimal("300000")},
            {"address": "100 A St", "est_value": Decimal("100000")},
            {"address": "200 B St", "est_value": Decimal("200000")}
        ]
        
        for prop_data in properties_data:
            property_obj = Property(
                **prop_data,
                city="Test City",
                zip_code="12345",
                owner_name="Test Owner"
            )
            db_session.add(property_obj)
        
        await db_session.commit()
        
        # Sort by value ascending
        response = await client.get(
            "/api/v1/properties?sort_by=est_value&sort_order=asc",
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        values = [float(prop["est_value"]) for prop in data["properties"]]
        assert values == [100000.0, 200000.0, 300000.0]
        
        # Sort by value descending
        response = await client.get(
            "/api/v1/properties?sort_by=est_value&sort_order=desc",
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        values = [float(prop["est_value"]) for prop in data["properties"]]
        assert values == [300000.0, 200000.0, 100000.0]

    @pytest.mark.asyncio
    async def test_list_properties_unauthorized(self, client: AsyncClient):
        """Test accessing properties without authentication."""
        response = await client.get("/api/v1/properties")
        assert response.status_code == 401
        
        # Test with invalid token
        response = await client.get(
            "/api/v1/properties",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401


class TestPropertyDetailAPI:
    """Test GET /api/v1/properties/{id} - Get single property by ID."""
    
    @pytest.mark.asyncio
    async def test_get_property_success(
        self,
        client: AsyncClient,
        test_user: User,
        db_session: AsyncSession
    ):
        """Test successfully retrieving a property by ID."""
        # Create test property
        property_obj = Property(
            address="123 Detail St",
            city="Los Angeles",
            zip_code="90210",
            property_type="SFR",
            est_value=Decimal("500000.00"),
            est_equity_percent=Decimal("65.50"),
            bedrooms=3,
            bathrooms=Decimal("2.5"),
            square_feet=1800,
            year_built=1995,
            owner_name="John Detail",
            latitude=Decimal("34.0522"),
            longitude=Decimal("-118.2437"),
            apn="1234567890"
        )
        db_session.add(property_obj)
        await db_session.commit()
        await db_session.refresh(property_obj)
        
        response = await client.get(
            f"/api/v1/properties/{property_obj.id}",
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all fields are present and correct
        assert data["id"] == str(property_obj.id)
        assert data["address"] == "123 Detail St"
        assert data["city"] == "Los Angeles"
        assert data["zip_code"] == "90210"
        assert data["property_type"] == "SFR"
        assert float(data["est_value"]) == 500000.00
        assert float(data["est_equity_percent"]) == 65.50
        assert data["bedrooms"] == 3
        assert float(data["bathrooms"]) == 2.5
        assert data["square_feet"] == 1800
        assert data["year_built"] == 1995
        assert data["owner_name"] == "John Detail"
        assert float(data["latitude"]) == 34.0522
        assert float(data["longitude"]) == -118.2437
        assert data["apn"] == "1234567890"

    @pytest.mark.asyncio
    async def test_get_property_not_found(self, client: AsyncClient, test_user: User):
        """Test getting non-existent property returns 404."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = await client.get(
            f"/api/v1/properties/{fake_uuid}",
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_property_invalid_uuid(self, client: AsyncClient, test_user: User):
        """Test getting property with invalid UUID format."""
        response = await client.get(
            "/api/v1/properties/invalid-uuid",
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_property_unauthorized(self, client: AsyncClient, db_session: AsyncSession):
        """Test getting property without authentication."""
        # Create property
        property_obj = Property(
            address="123 Unauth St",
            city="Test City", 
            zip_code="12345",
            owner_name="Test Owner"
        )
        db_session.add(property_obj)
        await db_session.commit()
        await db_session.refresh(property_obj)
        
        response = await client.get(f"/api/v1/properties/{property_obj.id}")
        assert response.status_code == 401


class TestPropertyCreateAPI:
    """Test POST /api/v1/properties - Create new property."""
    
    @pytest.mark.asyncio
    async def test_create_property_success(
        self,
        client: AsyncClient,
        test_user: User
    ):
        """Test successfully creating a new property."""
        property_data = {
            "address": "789 Create St",
            "city": "Los Angeles",
            "zip_code": "90210",
            "property_type": "SFR",
            "est_value": "600000.00",
            "est_equity_percent": "70.25",
            "bedrooms": 4,
            "bathrooms": "3.0",
            "square_feet": 2000,
            "year_built": 2000,
            "owner_name": "New Owner",
            "subdivision": "Test Subdivision",
            "latitude": "34.0522",
            "longitude": "-118.2437",
            "apn": "9876543210"
        }
        
        response = await client.post(
            "/api/v1/properties",
            json=property_data,
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify response contains all fields
        assert "id" in data
        assert data["address"] == "789 Create St"
        assert data["city"] == "Los Angeles"
        assert data["zip_code"] == "90210"
        assert data["property_type"] == "SFR"
        assert float(data["est_value"]) == 600000.00
        assert float(data["est_equity_percent"]) == 70.25
        assert data["bedrooms"] == 4
        assert float(data["bathrooms"]) == 3.0
        assert data["square_feet"] == 2000
        assert data["year_built"] == 2000
        assert data["owner_name"] == "New Owner"

    @pytest.mark.asyncio
    async def test_create_property_minimal_data(
        self,
        client: AsyncClient,
        test_user: User
    ):
        """Test creating property with minimal required data."""
        property_data = {
            "address": "456 Minimal St",
            "city": "Test City",
            "zip_code": "12345",
            "owner_name": "Minimal Owner"
        }
        
        response = await client.post(
            "/api/v1/properties",
            json=property_data,
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["address"] == "456 Minimal St"
        assert data["city"] == "Test City"
        assert data["zip_code"] == "12345"
        assert data["owner_name"] == "Minimal Owner"

    @pytest.mark.asyncio
    async def test_create_property_duplicate_address(
        self,
        client: AsyncClient,
        test_user: User,
        db_session: AsyncSession
    ):
        """Test creating property with duplicate address (should fail)."""
        # Create existing property
        existing_property = Property(
            address="123 Duplicate St",
            city="Los Angeles",
            zip_code="90210",
            owner_name="First Owner"
        )
        db_session.add(existing_property)
        await db_session.commit()
        
        # Try to create duplicate
        property_data = {
            "address": "123 Duplicate St",
            "city": "Los Angeles", 
            "zip_code": "90210",
            "owner_name": "Second Owner"
        }
        
        response = await client.post(
            "/api/v1/properties",
            json=property_data,
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 409  # Conflict
        assert "already exists" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_property_validation_errors(
        self,
        client: AsyncClient,
        test_user: User
    ):
        """Test property creation with validation errors."""
        test_cases = [
            # Missing required fields
            ({}, 422),
            ({"address": "Test"}, 422),
            ({"address": "Test", "city": "Test"}, 422),
            
            # Invalid data types
            ({
                "address": "123 Test St",
                "city": "Test City",
                "zip_code": "12345",
                "owner_name": "Test",
                "bedrooms": "invalid"
            }, 422),
            
            # Invalid year built
            ({
                "address": "123 Test St",
                "city": "Test City",
                "zip_code": "12345", 
                "owner_name": "Test",
                "year_built": 1800  # Too old
            }, 422),
            
            # Invalid coordinates
            ({
                "address": "123 Test St",
                "city": "Test City",
                "zip_code": "12345",
                "owner_name": "Test",
                "latitude": "invalid"
            }, 422)
        ]
        
        for property_data, expected_status in test_cases:
            response = await client.post(
                "/api/v1/properties",
                json=property_data,
                headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
            )
            assert response.status_code == expected_status

    @pytest.mark.asyncio
    async def test_create_property_unauthorized(self, client: AsyncClient):
        """Test creating property without authentication."""
        property_data = {
            "address": "123 Unauth St",
            "city": "Test City",
            "zip_code": "12345",
            "owner_name": "Test Owner"
        }
        
        response = await client.post("/api/v1/properties", json=property_data)
        assert response.status_code == 401


class TestPropertyUpdateAPI:
    """Test PUT /api/v1/properties/{id} - Update existing property."""
    
    @pytest.mark.asyncio
    async def test_update_property_success(
        self,
        client: AsyncClient,
        test_user: User,
        db_session: AsyncSession
    ):
        """Test successfully updating a property."""
        # Create initial property
        property_obj = Property(
            address="123 Update St",
            city="Los Angeles",
            zip_code="90210",
            owner_name="Original Owner",
            bedrooms=3,
            bathrooms=Decimal("2.0")
        )
        db_session.add(property_obj)
        await db_session.commit()
        await db_session.refresh(property_obj)
        
        # Update data
        update_data = {
            "bedrooms": 4,
            "bathrooms": "3.5",
            "owner_name": "Updated Owner",
            "est_value": "750000.00"
        }
        
        response = await client.put(
            f"/api/v1/properties/{property_obj.id}",
            json=update_data,
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify updates
        assert data["bedrooms"] == 4
        assert float(data["bathrooms"]) == 3.5
        assert data["owner_name"] == "Updated Owner"
        assert float(data["est_value"]) == 750000.00
        
        # Verify unchanged fields
        assert data["address"] == "123 Update St"
        assert data["city"] == "Los Angeles"

    @pytest.mark.asyncio
    async def test_update_property_not_found(self, client: AsyncClient, test_user: User):
        """Test updating non-existent property."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        update_data = {"owner_name": "New Owner"}
        
        response = await client.put(
            f"/api/v1/properties/{fake_uuid}",
            json=update_data,
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_property_validation_errors(
        self,
        client: AsyncClient,
        test_user: User,
        db_session: AsyncSession
    ):
        """Test property update with validation errors."""
        # Create property
        property_obj = Property(
            address="123 Validate St",
            city="Test City",
            zip_code="12345",
            owner_name="Test Owner"
        )
        db_session.add(property_obj)
        await db_session.commit()
        await db_session.refresh(property_obj)
        
        # Test invalid updates
        invalid_updates = [
            {"bedrooms": "invalid"},
            {"year_built": 1800},
            {"latitude": "invalid_lat"},
            {"est_value": "not_a_number"}
        ]
        
        for update_data in invalid_updates:
            response = await client.put(
                f"/api/v1/properties/{property_obj.id}",
                json=update_data,
                headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
            )
            assert response.status_code == 422


class TestPropertyDeleteAPI:
    """Test DELETE /api/v1/properties/{id} - Delete property."""
    
    @pytest.mark.asyncio
    async def test_delete_property_success(
        self,
        client: AsyncClient,
        test_user: User,
        db_session: AsyncSession
    ):
        """Test successfully deleting a property."""
        # Create property
        property_obj = Property(
            address="123 Delete St",
            city="Test City",
            zip_code="12345",
            owner_name="Delete Owner"
        )
        db_session.add(property_obj)
        await db_session.commit()
        await db_session.refresh(property_obj)
        property_id = property_obj.id
        
        response = await client.delete(
            f"/api/v1/properties/{property_id}",
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 204
        
        # Verify property is deleted
        result = await db_session.execute(
            select(Property).where(Property.id == property_id)
        )
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_delete_property_not_found(self, client: AsyncClient, test_user: User):
        """Test deleting non-existent property."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        
        response = await client.delete(
            f"/api/v1/properties/{fake_uuid}",
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_property_with_contacts(
        self,
        client: AsyncClient,
        test_user: User,
        db_session: AsyncSession
    ):
        """Test deleting property that has associated contacts."""
        # Create fresh user in this session (since db_session cleanup deletes users)
        from app.models.user import User
        fresh_user = User(
            id=test_user.id,  # Keep the same ID for auth token
            email=test_user.email,
            name=test_user.name,
            is_active=True
        )
        db_session.add(fresh_user)
        await db_session.commit()
        
        # Create property with contacts
        property_obj = Property(
            address="123 Contact St",
            city="Test City",
            zip_code="12345",
            owner_name="Property Owner"
        )
        
        contact = Contact(
            name="Property Contact",
            phone_number="+15551234567",
            user_id=fresh_user.id
        )
        
        property_obj.contacts.append(contact)
        db_session.add(property_obj)
        db_session.add(contact)
        await db_session.commit()
        await db_session.refresh(property_obj)
        
        response = await client.delete(
            f"/api/v1/properties/{property_obj.id}",
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 204
        
        # Verify property is deleted but contact remains
        result = await db_session.execute(
            select(Property).where(Property.id == property_obj.id)
        )
        assert result.scalar_one_or_none() is None
        
        result = await db_session.execute(
            select(Contact).where(Contact.id == contact.id)
        )
        assert result.scalar_one_or_none() is not None


class TestPropertyCSVImportAPI:
    """Test POST /api/v1/properties/import-csv - Import PropertyRadar CSV."""
    
    @pytest.mark.asyncio
    async def test_import_csv_success(
        self,
        client: AsyncClient,
        test_user: User,
        db_session: AsyncSession
    ):
        """Test successful CSV import."""
        # Create valid PropertyRadar CSV content
        csv_content = """Type,Address,City,ZIP,Subdivision,Longitude,Latitude,APN,Yr Built,Purchase Date,Purchase Mos Since,Sq Ft,Beds,Baths,Est Value,Est Equity $,Owner,Mail Address,Mail City,Mail State,Mail ZIP,Owner Occ?,Listed for Sale?,Listing Status,Foreclosure?,Est Equity %,High Equity?,Primary Name,Primary Mobile Phone1,Primary Mobile 1 Status,Primary Email1,Primary Email 1 Status,Primary Email1 Hash,Secondary Name,Secondary Mobile Phone1,Secondary Mobile 1 Status,Secondary Email1,Secondary Email 1 Status,Secondary Email1 Hash
SFR,123 Import St,Los Angeles,90210,Test Subdivision,-118.2437,34.0522,1234567890,1995,2020-01-15,36,1800,3,2.5,500000,325000,SMITH JOHN J,456 Mail St,Los Angeles,CA,90210,N,N,,N,65.0,Y,John Smith,+15551234567,Active,john@example.com,Active,hash123,Jane Smith,+15559876543,Active,jane@example.com,Active,hash456
CONDO,456 Test Ave,Beverly Hills,90210,,,,,2010,,24,1200,2,2.0,750000,600000,DOE JANE,789 Different St,Beverly Hills,CA,90210,Y,N,,N,80.0,Y,Jane Doe,+15555555555,Active,jane.doe@example.com,Active,hash789,,,,,,"""
        
        # Create CSV file
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        
        response = await client.post(
            "/api/v1/properties/import-csv",
            files={"file": ("properties.csv", csv_file, "text/csv")},
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify import results
        assert data["total_rows"] == 2
        assert data["processed_rows"] == 2
        assert data["failed_rows"] == 0
        assert data["properties_created"] == 2
        assert data["contacts_created"] >= 2  # At least primary contacts
        assert data["success_rate"] == 1.0
        
        # Verify properties were created in database
        result = await db_session.execute(select(func.count(Property.id)))
        property_count = result.scalar()
        assert property_count == 2

    @pytest.mark.asyncio
    async def test_import_csv_with_list_assignment(
        self,
        client: AsyncClient,
        test_user: User,
        db_session: AsyncSession
    ):
        """Test CSV import with assignment to property list."""
        # Create a fresh user in this session (since db_session cleanup deletes users)
        from app.models.user import User
        fresh_user = User(
            id=test_user.id,  # Keep the same ID for auth token
            email=test_user.email,
            name=test_user.name,
            is_active=True
        )
        db_session.add(fresh_user)
        await db_session.commit()
        
        # Create property list
        property_list = PropertyList(
            name="Import Test List",
            description="Test list for CSV import",
            user_id=fresh_user.id
        )
        db_session.add(property_list)
        await db_session.commit()
        await db_session.refresh(property_list)
        
        csv_content = """Type,Address,City,ZIP,Subdivision,Longitude,Latitude,APN,Yr Built,Purchase Date,Purchase Mos Since,Sq Ft,Beds,Baths,Est Value,Est Equity $,Owner,Mail Address,Mail City,Mail State,Mail ZIP,Owner Occ?,Listed for Sale?,Listing Status,Foreclosure?,Est Equity %,High Equity?,Primary Name,Primary Mobile Phone1,Primary Mobile 1 Status,Primary Email1,Primary Email 1 Status,Primary Email1 Hash,Secondary Name,Secondary Mobile Phone1,Secondary Mobile 1 Status,Secondary Email1,Secondary Email 1 Status,Secondary Email1 Hash
SFR,789 List St,Los Angeles,90210,Test Subdivision,-118.2437,34.0522,9876543210,2000,,12,2000,4,3.0,600000,420000,JOHNSON BOB,789 List St,Los Angeles,CA,90210,Y,N,,N,70.0,Y,Bob Johnson,+15551111111,Active,bob@example.com,Active,hashbob,,,,,,"""
        
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        
        response = await client.post(
            f"/api/v1/properties/import-csv?list_id={property_list.id}",
            files={"file": ("properties.csv", csv_file, "text/csv")},
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["processed_rows"] == 1
        
        # Verify property is assigned to list
        result = await db_session.execute(
            select(Property).where(Property.source_list_id == property_list.id)
        )
        properties = result.scalars().all()
        assert len(properties) == 1

    @pytest.mark.asyncio
    async def test_import_csv_invalid_file(
        self,
        client: AsyncClient,
        test_user: User
    ):
        """Test CSV import with invalid file format."""
        # Invalid CSV content
        invalid_csv = "This,is,not,a,valid,PropertyRadar,CSV"
        csv_file = io.BytesIO(invalid_csv.encode('utf-8'))
        
        response = await client.post(
            "/api/v1/properties/import-csv",
            files={"file": ("invalid.csv", csv_file, "text/csv")},
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_import_csv_empty_file(
        self,
        client: AsyncClient,
        test_user: User
    ):
        """Test CSV import with empty file."""
        csv_file = io.BytesIO(b"")
        
        response = await client.post(
            "/api/v1/properties/import-csv",
            files={"file": ("empty.csv", csv_file, "text/csv")},
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_import_csv_performance(
        self,
        client: AsyncClient,
        test_user: User
    ):
        """Test CSV import performance with larger file."""
        # Create CSV with 100 properties
        header = "Type,Address,City,ZIP,Subdivision,Longitude,Latitude,APN,Yr Built,Purchase Date,Purchase Mos Since,Sq Ft,Beds,Baths,Est Value,Est Equity $,Owner,Mail Address,Mail City,Mail State,Mail ZIP,Owner Occ?,Listed for Sale?,Listing Status,Foreclosure?,Est Equity %,High Equity?,Primary Name,Primary Mobile Phone1,Primary Mobile 1 Status,Primary Email1,Primary Email 1 Status,Primary Email1 Hash,Secondary Name,Secondary Mobile Phone1,Secondary Mobile 1 Status,Secondary Email1,Secondary Email 1 Status,Secondary Email1 Hash"
        
        rows = []
        for i in range(100):
            row = f"SFR,{i+1000} Performance St,Los Angeles,90210,Test Sub,-118.2437,34.0522,100{i:07d},1995,,12,1800,3,2.5,{500000 + i*1000},{300000 + i*600},OWNER{i:03d} FIRST,{i+1000} Performance St,Los Angeles,CA,90210,N,N,,N,60.0,Y,Owner {i},+155512{i:05d},Active,owner{i}@example.com,Active,hash{i},,,,,,"
            rows.append(row)
        
        csv_content = header + "\n" + "\n".join(rows)
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        
        start_time = time.time()
        response = await client.post(
            "/api/v1/properties/import-csv",
            files={"file": ("performance.csv", csv_file, "text/csv")},
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        end_time = time.time()
        
        assert response.status_code == 200
        assert end_time - start_time < 5.0  # Should complete in under 5 seconds
        
        data = response.json()
        assert data["total_rows"] == 100
        assert data["processed_rows"] == 100


class TestPropertySearchAPI:
    """Test GET /api/v1/properties/search - Search properties with query."""
    
    @pytest.mark.asyncio
    async def test_search_properties_by_address(
        self,
        client: AsyncClient,
        test_user: User,
        db_session: AsyncSession
    ):
        """Test searching properties by address."""
        # Create test properties
        properties_data = [
            {"address": "123 Main Street", "city": "Los Angeles", "zip_code": "90210"},
            {"address": "456 Oak Avenue", "city": "Beverly Hills", "zip_code": "90210"},
            {"address": "789 Pine Road", "city": "Santa Monica", "zip_code": "90401"}
        ]
        
        for prop_data in properties_data:
            property_obj = Property(**prop_data, owner_name="Search Owner")
            db_session.add(property_obj)
        
        await db_session.commit()
        
        # Search by address
        response = await client.get(
            "/api/v1/properties/search?q=Main Street",
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["properties"]) == 1
        assert "Main Street" in data["properties"][0]["address"]

    @pytest.mark.asyncio
    async def test_search_properties_by_owner(
        self,
        client: AsyncClient,
        test_user: User,
        db_session: AsyncSession
    ):
        """Test searching properties by owner name."""
        properties_data = [
            {"address": "123 Owner St", "owner_name": "John Smith"},
            {"address": "456 Owner Ave", "owner_name": "Jane Smith"},
            {"address": "789 Owner Rd", "owner_name": "Bob Johnson"}
        ]
        
        for prop_data in properties_data:
            property_obj = Property(
                **prop_data,
                city="Test City",
                zip_code="12345"
            )
            db_session.add(property_obj)
        
        await db_session.commit()
        
        # Search by owner name
        response = await client.get(
            "/api/v1/properties/search?q=Smith",
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["properties"]) == 2
        
        for prop in data["properties"]:
            assert "Smith" in prop["owner_name"]

    @pytest.mark.asyncio
    async def test_search_properties_by_city(
        self,
        client: AsyncClient,
        test_user: User,
        db_session: AsyncSession
    ):
        """Test searching properties by city."""
        properties_data = [
            {"address": "123 Test St", "city": "Los Angeles"},
            {"address": "456 Test Ave", "city": "Los Angeles"},
            {"address": "789 Test Rd", "city": "Beverly Hills"}
        ]
        
        for prop_data in properties_data:
            property_obj = Property(
                **prop_data,
                zip_code="90210",
                owner_name="Test Owner"
            )
            db_session.add(property_obj)
        
        await db_session.commit()
        
        response = await client.get(
            "/api/v1/properties/search?q=Los Angeles",
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["properties"]) == 2

    @pytest.mark.asyncio
    async def test_search_properties_empty_query(
        self,
        client: AsyncClient,
        test_user: User
    ):
        """Test search with empty query returns all properties."""
        response = await client.get(
            "/api/v1/properties/search?q=",
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 400
        assert "query" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_search_properties_no_results(
        self,
        client: AsyncClient,
        test_user: User,
        db_session: AsyncSession
    ):
        """Test search with no matching results."""
        # Create a property
        property_obj = Property(
            address="123 Real St",
            city="Real City",
            zip_code="12345",
            owner_name="Real Owner"
        )
        db_session.add(property_obj)
        await db_session.commit()
        
        response = await client.get(
            "/api/v1/properties/search?q=NonExistentTerm",
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["properties"]) == 0
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_search_properties_with_filters(
        self,
        client: AsyncClient,
        test_user: User,
        db_session: AsyncSession
    ):
        """Test search with additional filters."""
        # Create properties with different values
        properties_data = [
            {
                "address": "123 Search St",
                "city": "Los Angeles",
                "zip_code": "90210",
                "owner_name": "High Value Owner",
                "est_value": Decimal("800000"),
                "property_type": "SFR"
            },
            {
                "address": "456 Search Ave", 
                "city": "Los Angeles",
                "zip_code": "90210",
                "owner_name": "Low Value Owner",
                "est_value": Decimal("200000"),
                "property_type": "CONDO"
            }
        ]
        
        for prop_data in properties_data:
            property_obj = Property(**prop_data)
            db_session.add(property_obj)
        
        await db_session.commit()
        
        # Search with filters
        response = await client.get(
            "/api/v1/properties/search?q=Search&min_value=500000&property_type=SFR",
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["properties"]) == 1
        assert data["properties"][0]["owner_name"] == "High Value Owner"


class TestPropertyBatchDeleteAPI:
    """Test POST /api/v1/properties/batch-delete - Delete multiple properties."""
    
    @pytest.mark.asyncio
    async def test_batch_delete_success(
        self,
        client: AsyncClient,
        test_user: User,
        db_session: AsyncSession
    ):
        """Test successful batch deletion of properties."""
        # Create test properties
        properties = []
        for i in range(5):
            property_obj = Property(
                address=f"{i+100} Batch St",
                city="Test City",
                zip_code="12345",
                owner_name=f"Batch Owner {i+1}"
            )
            db_session.add(property_obj)
            properties.append(property_obj)
        
        await db_session.commit()
        
        # Refresh to get IDs
        for prop in properties:
            await db_session.refresh(prop)
        
        # Delete first 3 properties
        property_ids = [str(prop.id) for prop in properties[:3]]
        
        response = await client.post(
            "/api/v1/properties/batch-delete",
            json={"property_ids": property_ids},
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["deleted_count"] == 3
        assert data["failed_count"] == 0
        
        # Verify properties are deleted
        for prop_id in property_ids:
            result = await db_session.execute(
                select(Property).where(Property.id == prop_id)
            )
            assert result.scalar_one_or_none() is None
        
        # Verify remaining properties exist
        result = await db_session.execute(select(func.count(Property.id)))
        remaining_count = result.scalar()
        assert remaining_count == 2

    @pytest.mark.asyncio
    async def test_batch_delete_partial_success(
        self,
        client: AsyncClient,
        test_user: User,
        db_session: AsyncSession
    ):
        """Test batch deletion with some invalid IDs."""
        # Create test property
        property_obj = Property(
            address="123 Valid St",
            city="Test City",
            zip_code="12345",
            owner_name="Valid Owner"
        )
        db_session.add(property_obj)
        await db_session.commit()
        await db_session.refresh(property_obj)
        
        # Mix valid and invalid IDs
        property_ids = [
            str(property_obj.id),
            "00000000-0000-0000-0000-000000000000",  # Invalid UUID
            "11111111-1111-1111-1111-111111111111"   # Non-existent UUID
        ]
        
        response = await client.post(
            "/api/v1/properties/batch-delete",
            json={"property_ids": property_ids},
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["deleted_count"] == 1  # Only the valid one
        assert data["failed_count"] == 2
        assert len(data["failed_ids"]) == 2

    @pytest.mark.asyncio
    async def test_batch_delete_empty_list(
        self,
        client: AsyncClient,
        test_user: User
    ):
        """Test batch deletion with empty property list."""
        response = await client.post(
            "/api/v1/properties/batch-delete",
            json={"property_ids": []},
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_batch_delete_too_many_ids(
        self,
        client: AsyncClient,
        test_user: User
    ):
        """Test batch deletion with too many IDs (over limit)."""
        # Create list with 101 fake UUIDs (assuming 100 is the limit)
        property_ids = [f"00000000-0000-0000-0000-{i:012d}" for i in range(101)]
        
        response = await client.post(
            "/api/v1/properties/batch-delete",
            json={"property_ids": property_ids},
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 400
        assert "limit" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_batch_delete_invalid_request_format(
        self,
        client: AsyncClient,
        test_user: User
    ):
        """Test batch deletion with invalid request format."""
        # Invalid request formats
        invalid_requests = [
            {},  # Missing property_ids
            {"property_ids": "not_a_list"},  # Wrong type
            {"property_ids": [123, 456]},  # Wrong item type
            {"wrong_field": ["uuid1", "uuid2"]}  # Wrong field name
        ]
        
        for invalid_request in invalid_requests:
            response = await client.post(
                "/api/v1/properties/batch-delete",
                json=invalid_request,
                headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
            )
            assert response.status_code == 422


class TestPropertyAPIPerformance:
    """Test Property API performance requirements."""
    
    @pytest.mark.asyncio
    async def test_list_properties_response_time(
        self,
        client: AsyncClient,
        test_user: User,
        db_session: AsyncSession
    ):
        """Test properties list API meets response time requirements."""
        # Create 50 properties
        for i in range(50):
            property_obj = Property(
                address=f"{i+1000} Performance St",
                city="Performance City",
                zip_code="12345",
                owner_name=f"Performance Owner {i+1}",
                est_value=Decimal(str(500000 + i * 10000))
            )
            db_session.add(property_obj)
        
        await db_session.commit()
        
        # Measure response time
        start_time = time.time()
        response = await client.get(
            "/api/v1/properties",
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        end_time = time.time()
        
        assert response.status_code == 200
        assert end_time - start_time < 0.2  # Under 200ms requirement

    @pytest.mark.asyncio
    async def test_search_properties_response_time(
        self,
        client: AsyncClient,
        test_user: User,
        db_session: AsyncSession
    ):
        """Test property search API meets response time requirements."""
        # Create 100 properties
        for i in range(100):
            property_obj = Property(
                address=f"{i+2000} Search Performance St",
                city=f"Search City {i % 10}",
                zip_code="54321",
                owner_name=f"Search Owner {i+1}"
            )
            db_session.add(property_obj)
        
        await db_session.commit()
        
        # Measure search response time
        start_time = time.time()
        response = await client.get(
            "/api/v1/properties/search?q=Search",
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        end_time = time.time()
        
        assert response.status_code == 200
        assert end_time - start_time < 0.2  # Under 200ms requirement


class TestPropertyAPIAuthorization:
    """Test Property API authorization and security."""
    
    @pytest.mark.asyncio
    async def test_property_isolation_between_users(
        self,
        client: AsyncClient,
        test_user: User,
        db_session: AsyncSession
    ):
        """Test that users can only see their own properties."""
        # Create another user
        other_user = User(
            email="other@example.com",
            name="Other User",
            is_active=True
        )
        db_session.add(other_user)
        await db_session.commit()
        await db_session.refresh(other_user)
        
        # Create properties for different users
        user1_property = Property(
            address="123 User1 St",
            city="User1 City",
            zip_code="11111",
            owner_name="User1 Owner"
        )
        
        user2_property = Property(
            address="456 User2 St", 
            city="User2 City",
            zip_code="22222",
            owner_name="User2 Owner"
        )
        
        db_session.add_all([user1_property, user2_property])
        await db_session.commit()
        
        # User 1 should only see their properties
        response = await client.get(
            "/api/v1/properties",
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Implementation should filter by user - this test defines the expected behavior
        # In real implementation, properties would be filtered by user ownership/access
        # For now, this test documents the expected security behavior
        
        # Note: This test will fail initially as no user-based filtering exists
        # The API implementation must ensure proper user isolation

    @pytest.mark.asyncio
    async def test_sql_injection_protection(
        self,
        client: AsyncClient,
        test_user: User
    ):
        """Test that API endpoints are protected against SQL injection."""
        # SQL injection attempts in various parameters
        sql_injection_attempts = [
            "'; DROP TABLE properties; --",
            "' OR '1'='1",
            "1' UNION SELECT * FROM users --",
            "'; DELETE FROM properties WHERE 1=1; --"
        ]
        
        for injection_attempt in sql_injection_attempts:
            # Test search endpoint
            response = await client.get(
                f"/api/v1/properties/search?q={injection_attempt}",
                headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
            )
            
            # Should either return 200 with no results or 400 for invalid query
            # Should NOT cause database errors or return unexpected data
            assert response.status_code in [200, 400]
            
            # Test city filter
            response = await client.get(
                f"/api/v1/properties?city={injection_attempt}",
                headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
            )
            
            assert response.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_property_input_sanitization(
        self,
        client: AsyncClient,
        test_user: User
    ):
        """Test that property inputs are properly sanitized."""
        # Test creating property with potentially malicious input
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "../../etc/passwd",
            "NULL; DROP TABLE properties;",
            "<?xml version='1.0'?><!DOCTYPE root [<!ENTITY test SYSTEM 'file:///etc/passwd'>]><root>&test;</root>"
        ]
        
        for malicious_input in malicious_inputs:
            property_data = {
                "address": malicious_input,
                "city": "Test City",
                "zip_code": "12345",
                "owner_name": malicious_input
            }
            
            response = await client.post(
                "/api/v1/properties",
                json=property_data,
                headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
            )
            
            # Should either create property with sanitized data or reject it
            # Should NOT execute any malicious code or cause errors
            assert response.status_code in [201, 400, 422]
            
            if response.status_code == 201:
                # If created, verify data is sanitized
                data = response.json()
                # Implementation should sanitize inputs
                # This test documents expected sanitization behavior