"""
Unit tests for Property model.

Tests property creation, validation, business logic methods, and relationships.
Focuses on the Property model's unique functionality including:
- Address deduplication constraints
- High value target detection
- Marketing priority scoring
- Geographic data handling
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from datetime import datetime, timezone
from decimal import Decimal
import uuid
import random
import string
from typing import AsyncGenerator


class TestPropertyModelCreation:
    """Test basic Property model creation and field validation."""
    
    @pytest.mark.asyncio
    async def test_property_model_creation(self, db_session: AsyncSession):
        """Test Property model can be created with required fields."""
        from app.models.property import Property
        
        # Use unique address to avoid constraint violations
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        address = f"{random.randint(100, 9999)} Test St {unique_id}"
        
        property_obj = Property(
            property_type="SFR",
            address=address,
            city="Atlanta",
            zip_code="30309",
            subdivision="Midtown",
            latitude=Decimal("33.7490"),
            longitude=Decimal("-84.3880"),
            apn=f"APN{unique_id}",
            year_built=2010,
            square_feet=2500,
            bedrooms=3,
            bathrooms=Decimal("2.5"),
            est_value=Decimal("350000.00"),
            est_equity_dollar=Decimal("175000.00"),
            est_equity_percent=Decimal("50.00"),
            high_equity=True,
            owner_name="John Smith",
            mail_address="456 Mail Ave",
            mail_city="Atlanta",
            mail_state="GA",
            mail_zip="30309",
            owner_occupied=True,
            listed_for_sale=False,
            listing_status="Active",
            foreclosure=False
        )
        
        db_session.add(property_obj)
        await db_session.commit()
        await db_session.refresh(property_obj)
        
        # Test basic fields
        assert property_obj.id is not None
        assert isinstance(property_obj.id, uuid.UUID)
        assert property_obj.property_type == "SFR"
        assert property_obj.address == address
        assert property_obj.city == "Atlanta"
        assert property_obj.zip_code == "30309"
        assert property_obj.subdivision == "Midtown"
        
        # Test numeric fields
        assert property_obj.latitude == Decimal("33.7490")
        assert property_obj.longitude == Decimal("-84.3880")
        assert property_obj.year_built == 2010
        assert property_obj.square_feet == 2500
        assert property_obj.bedrooms == 3
        assert property_obj.bathrooms == Decimal("2.5")
        
        # Test financial fields
        assert property_obj.est_value == Decimal("350000.00")
        assert property_obj.est_equity_dollar == Decimal("175000.00")
        assert property_obj.est_equity_percent == Decimal("50.00")
        assert property_obj.high_equity is True
        
        # Test boolean fields
        assert property_obj.owner_occupied is True
        assert property_obj.listed_for_sale is False
        assert property_obj.foreclosure is False
        
        # Test timestamps
        assert property_obj.created_at is not None
        assert property_obj.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_property_minimal_creation(self, db_session: AsyncSession):
        """Test Property can be created with only required fields."""
        from app.models.property import Property
        
        # Use unique address to avoid constraint violations
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        address = f"{random.randint(100, 9999)} Minimal St {unique_id}"
        
        property_obj = Property(
            address=address,
            city="Atlanta",
            zip_code="30309"
        )
        
        db_session.add(property_obj)
        await db_session.commit()
        await db_session.refresh(property_obj)
        
        assert property_obj.id is not None
        assert property_obj.address == address
        assert property_obj.city == "Atlanta"
        assert property_obj.zip_code == "30309"
        
        # Optional fields should be None or default values
        assert property_obj.property_type is None
        assert property_obj.high_equity is False  # Default value
        assert property_obj.listed_for_sale is False  # Default value
        assert property_obj.foreclosure is False  # Default value
    
    @pytest.mark.asyncio
    async def test_property_unique_apn_constraint(self, db_session: AsyncSession):
        """Test Property APN must be unique when present."""
        from app.models.property import Property
        
        # Use unique identifiers
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        apn = f"APN{unique_id}"
        
        # Create first property with APN
        property1 = Property(
            address=f"{random.randint(100, 9999)} First St {unique_id}",
            city="Atlanta",
            zip_code="30309",
            apn=apn
        )
        db_session.add(property1)
        await db_session.commit()
        
        # Try to create second property with same APN
        property2 = Property(
            address=f"{random.randint(100, 9999)} Second St {unique_id}",
            city="Atlanta", 
            zip_code="30309",
            apn=apn  # Same APN should fail
        )
        db_session.add(property2)
        
        with pytest.raises(IntegrityError):
            await db_session.commit()


class TestPropertyUniqueConstraints:
    """Test Property unique constraints for address deduplication."""
    
    @pytest.mark.asyncio
    async def test_address_city_zip_unique_constraint(self, db_session: AsyncSession):
        """Test Property address+city+zip must be unique for deduplication."""
        from app.models.property import Property
        
        # Use consistent address components
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        address = f"{random.randint(100, 9999)} Duplicate St {unique_id}"
        city = "Atlanta"
        zip_code = "30309"
        
        # Create first property
        property1 = Property(
            address=address,
            city=city,
            zip_code=zip_code,
            owner_name="John Smith"
        )
        db_session.add(property1)
        await db_session.commit()
        
        # Try to create second property with same address/city/zip
        property2 = Property(
            address=address,
            city=city,
            zip_code=zip_code,
            owner_name="Jane Smith"  # Different owner, same address
        )
        db_session.add(property2)
        
        with pytest.raises(IntegrityError):
            await db_session.commit()
    
    @pytest.mark.asyncio
    async def test_different_cities_allow_same_address(self, db_session: AsyncSession):
        """Test same address in different cities is allowed."""
        from app.models.property import Property
        
        # Use same address, different cities
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        address = f"123 Main St {unique_id}"
        
        # Create property in Atlanta
        property1 = Property(
            address=address,
            city="Atlanta",
            zip_code="30309"
        )
        db_session.add(property1)
        await db_session.commit()
        
        # Create property in Nashville - should succeed
        property2 = Property(
            address=address,
            city="Nashville",
            zip_code="37203"
        )
        db_session.add(property2)
        await db_session.commit()
        await db_session.refresh(property2)
        
        assert property2.id is not None
        assert property2.city == "Nashville"
    
    @pytest.mark.asyncio
    async def test_different_zips_allow_same_address_city(self, db_session: AsyncSession):
        """Test same address+city in different zip codes is allowed."""
        from app.models.property import Property
        
        # Use same address and city, different zip codes
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        address = f"123 Main St {unique_id}"
        city = "Atlanta"
        
        # Create property in zip 30309
        property1 = Property(
            address=address,
            city=city,
            zip_code="30309"
        )
        db_session.add(property1)
        await db_session.commit()
        
        # Create property in zip 30308 - should succeed
        property2 = Property(
            address=address,
            city=city,
            zip_code="30308"
        )
        db_session.add(property2)
        await db_session.commit()
        await db_session.refresh(property2)
        
        assert property2.id is not None
        assert property2.zip_code == "30308"


class TestPropertyBusinessLogic:
    """Test Property business logic methods."""
    
    @pytest.mark.asyncio
    async def test_get_display_address(self, db_session: AsyncSession):
        """Test Property.get_display_address() method."""
        from app.models.property import Property
        
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        address = f"123 Display St {unique_id}"
        
        property_obj = Property(
            address=address,
            city="Atlanta",
            zip_code="30309"
        )
        
        display_address = property_obj.get_display_address()
        assert display_address == f"{address}, Atlanta, 30309"
    
    @pytest.mark.asyncio
    async def test_is_high_value_target_high_equity(self, db_session: AsyncSession):
        """Test is_high_value_target() returns True for high equity properties."""
        from app.models.property import Property
        
        # High equity (≥50%) + reasonable value (≥$200k)
        property_obj = Property(
            address="123 High Equity St",
            city="Atlanta",
            zip_code="30309",
            est_equity_percent=Decimal("60.00"),
            est_value=Decimal("300000.00")
        )
        
        assert property_obj.is_high_value_target() is True
    
    @pytest.mark.asyncio
    async def test_is_high_value_target_recent_purchase(self, db_session: AsyncSession):
        """Test is_high_value_target() returns True for recent purchases."""
        from app.models.property import Property
        
        # Recent purchase (≤12 months)
        property_obj = Property(
            address="123 Recent Purchase St",
            city="Atlanta",
            zip_code="30309",
            purchase_months_since=6,
            est_value=Decimal("250000.00")
        )
        
        assert property_obj.is_high_value_target() is True
    
    @pytest.mark.asyncio
    async def test_is_high_value_target_investment_property(self, db_session: AsyncSession):
        """Test is_high_value_target() returns True for investment properties."""
        from app.models.property import Property
        
        # Non-owner occupied (investment) + reasonable value (≥$150k)
        property_obj = Property(
            address="123 Investment St",
            city="Atlanta",
            zip_code="30309",
            owner_occupied=False,
            est_value=Decimal("200000.00")
        )
        
        assert property_obj.is_high_value_target() is True
    
    @pytest.mark.asyncio
    async def test_is_high_value_target_false_cases(self, db_session: AsyncSession):
        """Test is_high_value_target() returns False for low-value cases."""
        from app.models.property import Property
        
        # Low equity, old purchase, owner occupied, low value
        property_obj = Property(
            address="123 Low Value St",
            city="Atlanta",
            zip_code="30309",
            est_equity_percent=Decimal("20.00"),
            est_value=Decimal("100000.00"),
            purchase_months_since=36,
            owner_occupied=True
        )
        
        assert property_obj.is_high_value_target() is False
        
        # Missing critical data
        property_obj2 = Property(
            address="123 No Data St",
            city="Atlanta",
            zip_code="30309"
            # No equity, value, or other data
        )
        
        assert property_obj2.is_high_value_target() is False


class TestPropertyMarketingScore:
    """Test Property marketing priority scoring."""
    
    @pytest.mark.asyncio
    async def test_marketing_priority_score_maximum(self, db_session: AsyncSession):
        """Test get_marketing_priority_score() returns 100 for perfect property."""
        from app.models.property import Property
        
        # Perfect property: high equity, high value, investment, for sale, foreclosure, recent
        property_obj = Property(
            address="123 Perfect St",
            city="Atlanta",
            zip_code="30309",
            est_equity_percent=Decimal("80.00"),  # 40 points
            est_value=Decimal("600000.00"),       # 20 points  
            owner_occupied=False,                 # 15 points
            listed_for_sale=True,                 # 15 points
            foreclosure=True,                     # 10 points
            purchase_months_since=3               # 10 points
        )
        
        score = property_obj.get_marketing_priority_score()
        assert score == 100  # Should be capped at 100
    
    @pytest.mark.asyncio
    async def test_marketing_priority_score_equity_tiers(self, db_session: AsyncSession):
        """Test marketing score equity-based tiers."""
        from app.models.property import Property
        
        # Test 70%+ equity = 40 points
        property1 = Property(
            address="123 High Equity St",
            city="Atlanta",
            zip_code="30309",
            est_equity_percent=Decimal("75.00")
        )
        assert property1.get_marketing_priority_score() == 40
        
        # Test 50-69% equity = 30 points  
        property2 = Property(
            address="123 Medium Equity St",
            city="Atlanta", 
            zip_code="30309",
            est_equity_percent=Decimal("60.00")
        )
        assert property2.get_marketing_priority_score() == 30
        
        # Test 30-49% equity = 20 points
        property3 = Property(
            address="123 Low Equity St",
            city="Atlanta",
            zip_code="30309", 
            est_equity_percent=Decimal("40.00")
        )
        assert property3.get_marketing_priority_score() == 20
    
    @pytest.mark.asyncio
    async def test_marketing_priority_score_value_tiers(self, db_session: AsyncSession):
        """Test marketing score value-based tiers."""
        from app.models.property import Property
        
        # Test $500k+ value = 20 points
        property1 = Property(
            address="123 High Value St",
            city="Atlanta",
            zip_code="30309",
            est_value=Decimal("600000.00")
        )
        assert property1.get_marketing_priority_score() == 20
        
        # Test $300k-$499k value = 15 points
        property2 = Property(
            address="123 Medium Value St",
            city="Atlanta",
            zip_code="30309", 
            est_value=Decimal("400000.00")
        )
        assert property2.get_marketing_priority_score() == 15
        
        # Test $200k-$299k value = 10 points
        property3 = Property(
            address="123 Low Value St",
            city="Atlanta",
            zip_code="30309",
            est_value=Decimal("250000.00")
        )
        assert property3.get_marketing_priority_score() == 10
    
    @pytest.mark.asyncio
    async def test_marketing_priority_score_status_flags(self, db_session: AsyncSession):
        """Test marketing score status-based points."""
        from app.models.property import Property
        
        # Test individual status flags
        base_address = "123 Status Test St"
        
        # Non-owner occupied = 15 points
        property1 = Property(
            address=f"{base_address} 1",
            city="Atlanta",
            zip_code="30309",
            owner_occupied=False
        )
        assert property1.get_marketing_priority_score() == 15
        
        # Listed for sale = 15 points
        property2 = Property(
            address=f"{base_address} 2", 
            city="Atlanta",
            zip_code="30309",
            listed_for_sale=True
        )
        assert property2.get_marketing_priority_score() == 15
        
        # Foreclosure = 10 points
        property3 = Property(
            address=f"{base_address} 3",
            city="Atlanta",
            zip_code="30309",
            foreclosure=True
        )
        assert property3.get_marketing_priority_score() == 10
        
        # Recent purchase (≤6 months) = 10 points
        property4 = Property(
            address=f"{base_address} 4",
            city="Atlanta", 
            zip_code="30309",
            purchase_months_since=3
        )
        assert property4.get_marketing_priority_score() == 10
    
    @pytest.mark.asyncio
    async def test_marketing_priority_score_zero(self, db_session: AsyncSession):
        """Test marketing score returns 0 for minimal property."""
        from app.models.property import Property
        
        # Property with no scoring attributes
        property_obj = Property(
            address="123 Empty St",
            city="Atlanta",
            zip_code="30309"
            # No equity, value, or status flags
        )
        
        score = property_obj.get_marketing_priority_score()
        assert score == 0


class TestPropertyRelationships:
    """Test Property model relationships."""
    
    @pytest.mark.asyncio
    async def test_property_source_list_relationship(self, db_session: AsyncSession):
        """Test Property belongs to source List relationship."""
        from app.models.property import Property
        from app.models.list import List
        from app.models.user import User
        
        # Create user and list first
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        user_email = f"list_rel_{unique_id}@example.com"
        
        user = User(email=user_email, name="Test User")
        db_session.add(user)
        await db_session.commit()
        
        list_obj = List(
            name=f"Test List {unique_id}",
            user_id=user.id
        )
        db_session.add(list_obj)
        await db_session.commit()
        
        # Create property with source list
        property_obj = Property(
            address=f"{random.randint(100, 9999)} List St {unique_id}",
            city="Atlanta",
            zip_code="30309",
            source_list_id=list_obj.id
        )
        db_session.add(property_obj)
        await db_session.commit()
        
        # Test relationship loading
        await db_session.refresh(property_obj, ["source_list"])
        assert property_obj.source_list is not None
        assert property_obj.source_list.name == f"Test List {unique_id}"
        assert property_obj.source_list_id == list_obj.id
    
    @pytest.mark.asyncio
    async def test_property_contacts_many_to_many(self, db_session: AsyncSession):
        """Test Property has many Contacts relationship through association table."""
        from app.models.property import Property, contact_property_association
        from app.models.contact import Contact
        from app.models.user import User
        from sqlalchemy import insert
        
        # Create user first
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        user_email = f"contact_rel_{unique_id}@example.com"
        
        user = User(email=user_email, name="Test User")
        db_session.add(user)
        await db_session.commit()
        
        # Create property
        property_obj = Property(
            address=f"{random.randint(100, 9999)} Contact St {unique_id}",
            city="Atlanta",
            zip_code="30309"
        )
        db_session.add(property_obj)
        await db_session.commit()
        
        # Create contacts
        contact1 = Contact(
            phone_number=f"+155512345{random.randint(10, 99)}",
            name="John Smith",
            user_id=user.id
        )
        contact2 = Contact(
            phone_number=f"+155512345{random.randint(10, 99)}",
            name="Jane Smith",
            user_id=user.id
        )
        db_session.add_all([contact1, contact2])
        await db_session.commit()
        
        # Create associations through association table
        await db_session.execute(
            insert(contact_property_association).values([
                {
                    'contact_id': contact1.id,
                    'property_id': property_obj.id,
                    'relationship_type': 'primary'
                },
                {
                    'contact_id': contact2.id,
                    'property_id': property_obj.id, 
                    'relationship_type': 'secondary'
                }
            ])
        )
        await db_session.commit()
        
        # Test relationship loading
        await db_session.refresh(property_obj, ["contacts"])
        assert len(property_obj.contacts) == 2
        contact_names = [c.name for c in property_obj.contacts]
        assert "John Smith" in contact_names
        assert "Jane Smith" in contact_names


class TestPropertyStringRepresentation:
    """Test Property model string representation."""
    
    @pytest.mark.asyncio
    async def test_property_repr_with_equity(self, db_session: AsyncSession):
        """Test Property __repr__ includes address and equity."""
        from app.models.property import Property
        
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        address = f"123 Repr St {unique_id}"
        
        property_obj = Property(
            address=address,
            city="Atlanta",
            zip_code="30309",
            est_equity_percent=Decimal("65.50")
        )
        
        repr_str = repr(property_obj)
        assert f"address='{address}, Atlanta, 30309'" in repr_str
        assert "equity=65.50%" in repr_str
    
    @pytest.mark.asyncio
    async def test_property_repr_without_equity(self, db_session: AsyncSession):
        """Test Property __repr__ handles missing equity."""
        from app.models.property import Property
        
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        address = f"123 No Equity St {unique_id}"
        
        property_obj = Property(
            address=address,
            city="Atlanta",
            zip_code="30309"
            # No equity data
        )
        
        repr_str = repr(property_obj)
        assert f"address='{address}, Atlanta, 30309'" in repr_str
        assert "equity=N/A" in repr_str


class TestPropertyIndexes:
    """Test Property model database indexes are working."""
    
    @pytest.mark.asyncio
    async def test_property_city_zip_index_query(self, db_session: AsyncSession):
        """Test queries using city+zip index perform efficiently."""
        from app.models.property import Property
        
        # Create test properties in different locations
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        
        # Atlanta properties
        for i in range(3):
            property_obj = Property(
                address=f"{random.randint(100, 9999)} Atlanta St {unique_id} {i}",
                city="Atlanta",
                zip_code="30309"
            )
            db_session.add(property_obj)
        
        # Nashville properties
        for i in range(2):
            property_obj = Property(
                address=f"{random.randint(100, 9999)} Nashville St {unique_id} {i}",
                city="Nashville",
                zip_code="37203"
            )
            db_session.add(property_obj)
        
        await db_session.commit()
        
        # Query should use city+zip index
        result = await db_session.execute(
            select(Property).where(
                Property.city == "Atlanta",
                Property.zip_code == "30309"
            )
        )
        atlanta_properties = result.scalars().all()
        
        # Should find exactly our 3 Atlanta properties
        atlanta_count = sum(1 for p in atlanta_properties if unique_id in p.address)
        assert atlanta_count == 3
    
    @pytest.mark.asyncio
    async def test_property_equity_value_index_query(self, db_session: AsyncSession):
        """Test queries using equity+value index for high-value targeting."""
        from app.models.property import Property
        
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        
        # Create high-equity, high-value properties
        for i in range(2):
            property_obj = Property(
                address=f"{random.randint(100, 9999)} High Value St {unique_id} {i}",
                city="Atlanta",
                zip_code="30309",
                est_equity_percent=Decimal("70.00"),
                est_value=Decimal("500000.00")
            )
            db_session.add(property_obj)
        
        # Create low-equity properties
        property_low = Property(
            address=f"{random.randint(100, 9999)} Low Equity St {unique_id}",
            city="Atlanta",
            zip_code="30309",
            est_equity_percent=Decimal("20.00"),
            est_value=Decimal("200000.00")
        )
        db_session.add(property_low)
        
        await db_session.commit()
        
        # Query for high-equity, high-value properties (should use index)
        result = await db_session.execute(
            select(Property).where(
                Property.est_equity_percent >= 60.0,
                Property.est_value >= 400000.0
            )
        )
        high_value_properties = result.scalars().all()
        
        # Should find exactly our 2 high-value properties
        high_value_count = sum(1 for p in high_value_properties 
                              if unique_id in p.address and "High Value" in p.address)
        assert high_value_count == 2