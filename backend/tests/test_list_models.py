"""
Unit tests for List model.

Tests list creation, validation, business logic methods, and relationships.
Focuses on the List model's unique functionality including:
- Import status transitions
- Statistics calculation  
- Target quality scoring
- Geographic metadata
- Processing duration tracking
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from datetime import datetime, timezone, timedelta
import uuid
import random
import string
import json
from typing import AsyncGenerator


class TestListModelCreation:
    """Test basic List model creation and field validation."""
    
    @pytest.mark.asyncio
    async def test_list_model_creation(self, db_session: AsyncSession):
        """Test List model can be created with required fields."""
        from app.models.list import List, ListStatus, ListSource
        from app.models.user import User
        
        # Create user first
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        user_email = f"list_test_{unique_id}@example.com"
        
        user = User(email=user_email, name="Test User")
        db_session.add(user)
        await db_session.commit()
        
        # Create list with comprehensive data
        list_obj = List(
            name=f"Property Import {unique_id}",
            description="Test property list import from PropertyRadar",
            status=ListStatus.COMPLETED,
            source=ListSource.PROPERTY_RADAR,
            original_filename="properties_atlanta_30309.csv",
            file_size_bytes=1024576,  # ~1MB
            total_rows_imported=1500,
            properties_created=1450,
            properties_updated=50,
            contacts_created=1200,
            contacts_updated=300,
            errors_count=5,
            import_started_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            import_completed_at=datetime(2024, 1, 15, 10, 45, 0, tzinfo=timezone.utc),
            error_details='{"row_errors": ["Invalid phone format on row 1250"]}',
            sample_data='{"headers": ["Address", "City", "Owner"], "sample_rows": []}',
            primary_city="Atlanta",
            primary_state="GA", 
            zip_codes_covered='["30309", "30308", "30307"]',
            min_property_value=150000,
            max_property_value=850000,
            avg_property_value=425000,
            high_equity_count=350,
            avg_equity_percent=65,
            user_id=user.id
        )
        
        db_session.add(list_obj)
        await db_session.commit()
        await db_session.refresh(list_obj)
        
        # Test basic fields
        assert list_obj.id is not None
        assert isinstance(list_obj.id, uuid.UUID)
        assert list_obj.name == f"Property Import {unique_id}"
        assert list_obj.description == "Test property list import from PropertyRadar"
        assert list_obj.status == ListStatus.COMPLETED
        assert list_obj.source == ListSource.PROPERTY_RADAR
        
        # Test file information
        assert list_obj.original_filename == "properties_atlanta_30309.csv"
        assert list_obj.file_size_bytes == 1024576
        
        # Test import statistics
        assert list_obj.total_rows_imported == 1500
        assert list_obj.properties_created == 1450
        assert list_obj.properties_updated == 50
        assert list_obj.contacts_created == 1200
        assert list_obj.contacts_updated == 300
        assert list_obj.errors_count == 5
        
        # Test timestamps
        assert list_obj.import_started_at is not None
        assert list_obj.import_completed_at is not None
        assert list_obj.created_at is not None
        assert list_obj.updated_at is not None
        
        # Test geographic data
        assert list_obj.primary_city == "Atlanta"
        assert list_obj.primary_state == "GA"
        assert list_obj.zip_codes_covered == '["30309", "30308", "30307"]'
        
        # Test value statistics
        assert list_obj.min_property_value == 150000
        assert list_obj.max_property_value == 850000
        assert list_obj.avg_property_value == 425000
        assert list_obj.high_equity_count == 350
        assert list_obj.avg_equity_percent == 65
        
        # Test user relationship
        assert list_obj.user_id == user.id
    
    @pytest.mark.asyncio
    async def test_list_minimal_creation(self, db_session: AsyncSession):
        """Test List can be created with only required fields."""
        from app.models.list import List, ListStatus, ListSource
        from app.models.user import User
        
        # Create user first
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        user_email = f"minimal_list_{unique_id}@example.com"
        
        user = User(email=user_email, name="Test User")
        db_session.add(user)
        await db_session.commit()
        
        # Create minimal list
        list_obj = List(
            name=f"Minimal List {unique_id}",
            user_id=user.id
        )
        
        db_session.add(list_obj)
        await db_session.commit()
        await db_session.refresh(list_obj)
        
        assert list_obj.id is not None
        assert list_obj.name == f"Minimal List {unique_id}"
        assert list_obj.user_id == user.id
        
        # Test default values
        assert list_obj.status == ListStatus.UPLOADING  # Default
        assert list_obj.source == ListSource.PROPERTY_RADAR  # Default
        assert list_obj.total_rows_imported == 0
        assert list_obj.properties_created == 0
        assert list_obj.properties_updated == 0
        assert list_obj.contacts_created == 0
        assert list_obj.contacts_updated == 0
        assert list_obj.errors_count == 0
        assert list_obj.high_equity_count == 0


class TestListStatusEnum:
    """Test List status enumeration and transitions."""
    
    @pytest.mark.asyncio
    async def test_list_status_values(self, db_session: AsyncSession):
        """Test all ListStatus enum values are valid."""
        from app.models.list import List, ListStatus, ListSource
        from app.models.user import User
        
        # Create user first
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        user_email = f"status_test_{unique_id}@example.com"
        
        user = User(email=user_email, name="Test User")
        db_session.add(user)
        await db_session.commit()
        
        # Test each status value
        valid_statuses = [
            ListStatus.UPLOADING,
            ListStatus.PROCESSING,
            ListStatus.COMPLETED,
            ListStatus.FAILED,
            ListStatus.ARCHIVED
        ]
        
        for i, status in enumerate(valid_statuses):
            list_obj = List(
                name=f"Status Test {status.value} {unique_id}",
                status=status,
                user_id=user.id
            )
            
            db_session.add(list_obj)
            await db_session.commit()
            await db_session.refresh(list_obj)
            
            assert list_obj.status == status
            assert list_obj.status.value in [
                "uploading", "processing", "completed", "failed", "archived"
            ]
            
            # Clean up for next iteration
            await db_session.delete(list_obj)
            await db_session.commit()
    
    @pytest.mark.asyncio
    async def test_list_source_values(self, db_session: AsyncSession):
        """Test all ListSource enum values are valid."""
        from app.models.list import List, ListStatus, ListSource
        from app.models.user import User
        
        # Create user first
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        user_email = f"source_test_{unique_id}@example.com"
        
        user = User(email=user_email, name="Test User")
        db_session.add(user)
        await db_session.commit()
        
        # Test each source value
        valid_sources = [
            ListSource.PROPERTY_RADAR,
            ListSource.MANUAL_UPLOAD,
            ListSource.API_IMPORT,
            ListSource.OTHER
        ]
        
        for i, source in enumerate(valid_sources):
            list_obj = List(
                name=f"Source Test {source.value} {unique_id}",
                source=source,
                user_id=user.id
            )
            
            db_session.add(list_obj)
            await db_session.commit()
            await db_session.refresh(list_obj)
            
            assert list_obj.source == source
            assert list_obj.source.value in [
                "property_radar", "manual_upload", "api_import", "other"
            ]
            
            # Clean up for next iteration
            await db_session.delete(list_obj)
            await db_session.commit()


class TestListBusinessLogicMethods:
    """Test List model business logic methods."""
    
    @pytest.mark.asyncio
    async def test_get_import_duration(self, db_session: AsyncSession):
        """Test List.get_import_duration() calculation."""
        from app.models.list import List
        from app.models.user import User
        
        # Create user first
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        user_email = f"duration_test_{unique_id}@example.com"
        
        user = User(email=user_email, name="Test User")
        db_session.add(user)
        await db_session.commit()
        
        # Test with both timestamps
        start_time = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        end_time = datetime(2024, 1, 15, 10, 45, 30, tzinfo=timezone.utc)  # 15.5 minutes
        
        list_obj = List(
            name=f"Duration Test {unique_id}",
            import_started_at=start_time,
            import_completed_at=end_time,
            user_id=user.id
        )
        
        duration = list_obj.get_import_duration()
        assert duration == 930  # 15.5 minutes = 930 seconds
        
        # Test with missing start time
        list_obj2 = List(
            name=f"No Start Test {unique_id}",
            import_completed_at=end_time,
            user_id=user.id
        )
        
        duration2 = list_obj2.get_import_duration()
        assert duration2 is None
        
        # Test with missing end time
        list_obj3 = List(
            name=f"No End Test {unique_id}",
            import_started_at=start_time,
            user_id=user.id
        )
        
        duration3 = list_obj3.get_import_duration()
        assert duration3 is None
    
    @pytest.mark.asyncio
    async def test_get_import_success_rate(self, db_session: AsyncSession):
        """Test List.get_import_success_rate() calculation."""
        from app.models.list import List
        from app.models.user import User
        
        # Create user first
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        user_email = f"success_rate_{unique_id}@example.com"
        
        user = User(email=user_email, name="Test User")
        db_session.add(user)
        await db_session.commit()
        
        # Test 95% success rate (1000 total, 50 errors)
        list_obj = List(
            name=f"Success Test {unique_id}",
            total_rows_imported=1000,
            errors_count=50,
            user_id=user.id
        )
        
        success_rate = list_obj.get_import_success_rate()
        assert success_rate == 95.0  # (1000 - 50) / 1000 * 100
        
        # Test 100% success rate (no errors)
        list_obj2 = List(
            name=f"Perfect Test {unique_id}",
            total_rows_imported=500,
            errors_count=0,
            user_id=user.id
        )
        
        success_rate2 = list_obj2.get_import_success_rate()
        assert success_rate2 == 100.0
        
        # Test 0% success rate (no imports)
        list_obj3 = List(
            name=f"Empty Test {unique_id}",
            total_rows_imported=0,
            errors_count=0,
            user_id=user.id
        )
        
        success_rate3 = list_obj3.get_import_success_rate()
        assert success_rate3 == 0.0
    
    @pytest.mark.asyncio
    async def test_is_ready_for_campaigns(self, db_session: AsyncSession):
        """Test List.is_ready_for_campaigns() logic."""
        from app.models.list import List, ListStatus
        from app.models.user import User
        
        # Create user first
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        user_email = f"ready_test_{unique_id}@example.com"
        
        user = User(email=user_email, name="Test User")
        db_session.add(user)
        await db_session.commit()
        
        # Test ready list (completed + has properties + has contacts)
        ready_list = List(
            name=f"Ready List {unique_id}",
            status=ListStatus.COMPLETED,
            properties_created=100,
            contacts_created=75,
            user_id=user.id
        )
        
        assert ready_list.is_ready_for_campaigns() is True
        
        # Test not ready - wrong status
        not_ready_status = List(
            name=f"Processing List {unique_id}",
            status=ListStatus.PROCESSING,
            properties_created=100,
            contacts_created=75,
            user_id=user.id
        )
        
        assert not_ready_status.is_ready_for_campaigns() is False
        
        # Test not ready - no properties
        not_ready_props = List(
            name=f"No Props List {unique_id}",
            status=ListStatus.COMPLETED,
            properties_created=0,
            contacts_created=75,
            user_id=user.id
        )
        
        assert not_ready_props.is_ready_for_campaigns() is False
        
        # Test not ready - no contacts
        not_ready_contacts = List(
            name=f"No Contacts List {unique_id}",
            status=ListStatus.COMPLETED,
            properties_created=100,
            contacts_created=0,
            user_id=user.id
        )
        
        assert not_ready_contacts.is_ready_for_campaigns() is False


class TestListTargetQualityScore:
    """Test List target quality scoring algorithm."""
    
    @pytest.mark.asyncio
    async def test_target_quality_score_maximum(self, db_session: AsyncSession):
        """Test get_target_quality_score() returns 100 for perfect list."""
        from app.models.list import List
        from app.models.user import User
        
        # Create user first
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        user_email = f"quality_max_{unique_id}@example.com"
        
        user = User(email=user_email, name="Test User")
        db_session.add(user)
        await db_session.commit()
        
        # Perfect list: high equity ratio, high avg value, high avg equity, good contact coverage
        perfect_list = List(
            name=f"Perfect List {unique_id}",
            properties_created=1000,          # Base for ratios
            high_equity_count=1000,           # 100% high equity = 30 points
            avg_property_value=600000,        # $600k+ = 25 points
            avg_equity_percent=80,            # 80% equity = 25 points
            contacts_created=1000,            # 100% contact coverage = 20 points
            user_id=user.id
        )
        
        score = perfect_list.get_target_quality_score()
        assert score == 100  # Should be capped at 100
    
    @pytest.mark.asyncio
    async def test_target_quality_score_equity_ratio(self, db_session: AsyncSession):
        """Test target quality score equity ratio component."""
        from app.models.list import List
        from app.models.user import User
        
        # Create user first
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        user_email = f"equity_ratio_{unique_id}@example.com"
        
        user = User(email=user_email, name="Test User")
        db_session.add(user)
        await db_session.commit()
        
        # Test 50% equity ratio = 15 points (50% of max 30)
        list_obj = List(
            name=f"Equity Test {unique_id}",
            properties_created=1000,
            high_equity_count=500,  # 50% ratio
            user_id=user.id
        )
        
        score = list_obj.get_target_quality_score()
        assert score == 15  # Only equity ratio contributes
        
        # Test 100% equity ratio = 30 points
        list_obj2 = List(
            name=f"Perfect Equity {unique_id}",
            properties_created=100,
            high_equity_count=100,  # 100% ratio
            user_id=user.id
        )
        
        score2 = list_obj2.get_target_quality_score()
        assert score2 == 30
    
    @pytest.mark.asyncio
    async def test_target_quality_score_property_value_tiers(self, db_session: AsyncSession):
        """Test target quality score property value tiers."""
        from app.models.list import List
        from app.models.user import User
        
        # Create user first
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        user_email = f"value_tiers_{unique_id}@example.com"
        
        user = User(email=user_email, name="Test User")
        db_session.add(user)
        await db_session.commit()
        
        # Test $500k+ = 25 points
        high_value_list = List(
            name=f"High Value {unique_id}",
            properties_created=1,
            avg_property_value=600000,
            user_id=user.id
        )
        assert high_value_list.get_target_quality_score() == 25
        
        # Test $300k-$499k = 20 points
        medium_value_list = List(
            name=f"Medium Value {unique_id}",
            properties_created=1,
            avg_property_value=400000,
            user_id=user.id
        )
        assert medium_value_list.get_target_quality_score() == 20
        
        # Test $200k-$299k = 15 points
        lower_value_list = List(
            name=f"Lower Value {unique_id}",
            properties_created=1,
            avg_property_value=250000,
            user_id=user.id
        )
        assert lower_value_list.get_target_quality_score() == 15
        
        # Test $100k-$199k = 10 points
        low_value_list = List(
            name=f"Low Value {unique_id}",
            properties_created=1,
            avg_property_value=150000,
            user_id=user.id
        )
        assert low_value_list.get_target_quality_score() == 10
    
    @pytest.mark.asyncio
    async def test_target_quality_score_equity_percentage_tiers(self, db_session: AsyncSession):
        """Test target quality score equity percentage tiers."""
        from app.models.list import List
        from app.models.user import User
        
        # Create user first
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        user_email = f"equity_pct_{unique_id}@example.com"
        
        user = User(email=user_email, name="Test User")
        db_session.add(user)
        await db_session.commit()
        
        # Test 70%+ equity = 25 points
        high_equity_list = List(
            name=f"High Equity Pct {unique_id}",
            properties_created=1,
            avg_equity_percent=75,
            user_id=user.id
        )
        assert high_equity_list.get_target_quality_score() == 25
        
        # Test 50-69% equity = 20 points
        medium_equity_list = List(
            name=f"Medium Equity Pct {unique_id}",
            properties_created=1,
            avg_equity_percent=60,
            user_id=user.id
        )
        assert medium_equity_list.get_target_quality_score() == 20
        
        # Test 30-49% equity = 15 points
        lower_equity_list = List(
            name=f"Lower Equity Pct {unique_id}",
            properties_created=1,
            avg_equity_percent=40,
            user_id=user.id
        )
        assert lower_equity_list.get_target_quality_score() == 15
        
        # Test 10-29% equity = 10 points
        low_equity_list = List(
            name=f"Low Equity Pct {unique_id}",
            properties_created=1,
            avg_equity_percent=20,
            user_id=user.id
        )
        assert low_equity_list.get_target_quality_score() == 10
    
    @pytest.mark.asyncio
    async def test_target_quality_score_contact_coverage(self, db_session: AsyncSession):
        """Test target quality score contact coverage component."""
        from app.models.list import List
        from app.models.user import User
        
        # Create user first
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        user_email = f"contact_cov_{unique_id}@example.com"
        
        user = User(email=user_email, name="Test User")
        db_session.add(user)
        await db_session.commit()
        
        # Test 100% contact coverage = 20 points
        full_coverage_list = List(
            name=f"Full Coverage {unique_id}",
            properties_created=100,
            contacts_created=100,  # 1:1 ratio
            user_id=user.id
        )
        assert full_coverage_list.get_target_quality_score() == 20
        
        # Test 50% contact coverage = 10 points
        half_coverage_list = List(
            name=f"Half Coverage {unique_id}",
            properties_created=100,
            contacts_created=50,  # 0.5:1 ratio
            user_id=user.id
        )
        assert half_coverage_list.get_target_quality_score() == 10
    
    @pytest.mark.asyncio
    async def test_target_quality_score_zero_properties(self, db_session: AsyncSession):
        """Test target quality score returns 0 for lists with no properties."""
        from app.models.list import List
        from app.models.user import User
        
        # Create user first
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        user_email = f"zero_props_{unique_id}@example.com"
        
        user = User(email=user_email, name="Test User")
        db_session.add(user)
        await db_session.commit()
        
        # List with no properties created
        empty_list = List(
            name=f"Empty List {unique_id}",
            properties_created=0,
            high_equity_count=100,      # This won't matter
            avg_property_value=500000,  # This won't matter
            contacts_created=100,       # This won't matter
            user_id=user.id
        )
        
        score = empty_list.get_target_quality_score()
        assert score == 0


class TestListSummaryStats:
    """Test List summary statistics generation."""
    
    @pytest.mark.asyncio
    async def test_get_summary_stats(self, db_session: AsyncSession):
        """Test List.get_summary_stats() returns comprehensive statistics."""
        from app.models.list import List, ListStatus
        from app.models.user import User
        
        # Create user first
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        user_email = f"summary_stats_{unique_id}@example.com"
        
        user = User(email=user_email, name="Test User")
        db_session.add(user)
        await db_session.commit()
        
        # Create list with complete data
        start_time = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        end_time = datetime(2024, 1, 15, 10, 45, 0, tzinfo=timezone.utc)  # 15 minutes
        
        list_obj = List(
            name=f"Summary Test {unique_id}",
            status=ListStatus.COMPLETED,
            total_rows_imported=1000,
            properties_created=950,
            contacts_created=800,
            high_equity_count=300,
            avg_property_value=425000,
            avg_equity_percent=55,
            errors_count=50,  # 95% success rate
            import_started_at=start_time,
            import_completed_at=end_time,
            primary_city="Atlanta",
            primary_state="GA",
            user_id=user.id
        )
        
        stats = list_obj.get_summary_stats()
        
        # Test all returned statistics
        assert stats['total_properties'] == 950
        assert stats['total_contacts'] == 800
        assert stats['high_equity_properties'] == 300
        assert stats['avg_property_value'] == 425000
        assert stats['avg_equity_percent'] == 55
        assert stats['import_success_rate'] == 95.0  # (1000-50)/1000*100
        assert stats['target_quality_score'] > 0  # Calculated by algorithm
        assert stats['import_duration_minutes'] == 15  # 900 seconds / 60
        assert stats['primary_location'] == "Atlanta, GA"
        assert stats['ready_for_campaigns'] is True
    
    @pytest.mark.asyncio
    async def test_get_summary_stats_minimal(self, db_session: AsyncSession):
        """Test get_summary_stats() handles missing optional data."""
        from app.models.list import List, ListStatus
        from app.models.user import User
        
        # Create user first
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        user_email = f"minimal_stats_{unique_id}@example.com"
        
        user = User(email=user_email, name="Test User")
        db_session.add(user)
        await db_session.commit()
        
        # Create minimal list
        list_obj = List(
            name=f"Minimal Stats {unique_id}",
            status=ListStatus.UPLOADING,  # Not completed
            total_rows_imported=0,
            properties_created=0,
            contacts_created=0,
            user_id=user.id
        )
        
        stats = list_obj.get_summary_stats()
        
        # Test handling of missing/zero data
        assert stats['total_properties'] == 0
        assert stats['total_contacts'] == 0
        assert stats['high_equity_properties'] == 0
        assert stats['avg_property_value'] is None
        assert stats['avg_equity_percent'] is None
        assert stats['import_success_rate'] == 0.0
        assert stats['target_quality_score'] == 0
        assert stats['import_duration_minutes'] is None
        assert stats['primary_location'] is None
        assert stats['ready_for_campaigns'] is False


class TestListRelationships:
    """Test List model relationships."""
    
    @pytest.mark.asyncio
    async def test_list_user_relationship(self, db_session: AsyncSession):
        """Test List belongs to User relationship."""
        from app.models.list import List
        from app.models.user import User
        
        # Create user first
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        user_email = f"list_user_rel_{unique_id}@example.com"
        
        user = User(email=user_email, name="Test User")
        db_session.add(user)
        await db_session.commit()
        
        # Create list
        list_obj = List(
            name=f"User Relationship Test {unique_id}",
            user_id=user.id
        )
        db_session.add(list_obj)
        await db_session.commit()
        
        # Test relationship loading
        await db_session.refresh(list_obj, ["user"])
        assert list_obj.user is not None
        assert list_obj.user.email == user_email
        assert list_obj.user_id == user.id
    
    @pytest.mark.asyncio
    async def test_list_properties_relationship(self, db_session: AsyncSession):
        """Test List has many Properties relationship."""
        from app.models.list import List
        from app.models.property import Property
        from app.models.user import User
        
        # Create user and list first
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        user_email = f"list_props_rel_{unique_id}@example.com"
        
        user = User(email=user_email, name="Test User")
        db_session.add(user)
        await db_session.commit()
        
        list_obj = List(
            name=f"Properties Relationship Test {unique_id}",
            user_id=user.id
        )
        db_session.add(list_obj)
        await db_session.commit()
        
        # Create properties linked to this list
        for i in range(3):
            property_obj = Property(
                address=f"{random.randint(100, 9999)} List Property St {unique_id} {i}",
                city="Atlanta",
                zip_code="30309",
                source_list_id=list_obj.id
            )
            db_session.add(property_obj)
        
        await db_session.commit()
        
        # Test relationship loading
        await db_session.refresh(list_obj, ["properties"])
        assert len(list_obj.properties) == 3
        
        # All properties should reference this list
        for prop in list_obj.properties:
            assert prop.source_list_id == list_obj.id
            assert unique_id in prop.address
    
    @pytest.mark.asyncio
    async def test_list_cascade_delete_properties(self, db_session: AsyncSession):
        """Test List deletion cascades to Properties."""
        from app.models.list import List
        from app.models.property import Property
        from app.models.user import User
        
        # Create user and list first
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        user_email = f"cascade_test_{unique_id}@example.com"
        
        user = User(email=user_email, name="Test User")
        db_session.add(user)
        await db_session.commit()
        
        list_obj = List(
            name=f"Cascade Test {unique_id}",
            user_id=user.id
        )
        db_session.add(list_obj)
        await db_session.commit()
        
        # Create properties
        property_ids = []
        for i in range(2):
            property_obj = Property(
                address=f"{random.randint(100, 9999)} Cascade St {unique_id} {i}",
                city="Atlanta",
                zip_code="30309",
                source_list_id=list_obj.id
            )
            db_session.add(property_obj)
            await db_session.commit()
            await db_session.refresh(property_obj)
            property_ids.append(property_obj.id)
        
        # Delete the list
        await db_session.delete(list_obj)
        await db_session.commit()
        
        # Properties should be deleted (cascade)
        for prop_id in property_ids:
            result = await db_session.execute(
                select(Property).where(Property.id == prop_id)
            )
            deleted_property = result.scalar_one_or_none()
            assert deleted_property is None


class TestListStringRepresentation:
    """Test List model string representation."""
    
    @pytest.mark.asyncio
    async def test_list_repr(self, db_session: AsyncSession):
        """Test List __repr__ includes name, properties count, and status."""
        from app.models.list import List, ListStatus
        from app.models.user import User
        
        # Create user first
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        user_email = f"repr_test_{unique_id}@example.com"
        
        user = User(email=user_email, name="Test User")
        db_session.add(user)
        await db_session.commit()
        
        list_obj = List(
            name=f"Repr Test List {unique_id}",
            status=ListStatus.COMPLETED,
            properties_created=450,
            user_id=user.id
        )
        
        repr_str = repr(list_obj)
        assert f"name='Repr Test List {unique_id}'" in repr_str
        assert "properties=450" in repr_str
        assert "status='completed'" in repr_str


class TestListIndexes:
    """Test List model database indexes are working."""
    
    @pytest.mark.asyncio
    async def test_list_user_index_query(self, db_session: AsyncSession):
        """Test queries using user_id index perform efficiently."""
        from app.models.list import List
        from app.models.user import User
        
        # Create two users with lists each
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        
        user1_email = f"index_user1_{unique_id}@example.com"
        user1 = User(email=user1_email, name="User 1")
        db_session.add(user1)
        await db_session.commit()
        
        user2_email = f"index_user2_{unique_id}@example.com"
        user2 = User(email=user2_email, name="User 2")
        db_session.add(user2)
        await db_session.commit()
        
        # Create 3 lists for user1, 2 for user2
        for i in range(3):
            list_obj = List(
                name=f"User1 List {i} {unique_id}",
                user_id=user1.id
            )
            db_session.add(list_obj)
        
        for i in range(2):
            list_obj = List(
                name=f"User2 List {i} {unique_id}",
                user_id=user2.id
            )
            db_session.add(list_obj)
        
        await db_session.commit()
        
        # Query should use user_id index
        result = await db_session.execute(
            select(List).where(List.user_id == user1.id)
        )
        user1_lists = result.scalars().all()
        
        # Should find exactly 3 lists for user1
        user1_count = sum(1 for lst in user1_lists if unique_id in lst.name)
        assert user1_count == 3
    
    @pytest.mark.asyncio
    async def test_list_status_index_query(self, db_session: AsyncSession):
        """Test queries using status index for filtering."""
        from app.models.list import List, ListStatus
        from app.models.user import User
        
        # Create user first
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        user_email = f"status_index_{unique_id}@example.com"
        
        user = User(email=user_email, name="Test User")
        db_session.add(user)
        await db_session.commit()
        
        # Create lists with different statuses
        statuses_to_create = [
            (ListStatus.COMPLETED, 3),  # 3 completed
            (ListStatus.PROCESSING, 2), # 2 processing
            (ListStatus.FAILED, 1)      # 1 failed
        ]
        
        for status, count in statuses_to_create:
            for i in range(count):
                list_obj = List(
                    name=f"{status.value} List {i} {unique_id}",
                    status=status,
                    user_id=user.id
                )
                db_session.add(list_obj)
        
        await db_session.commit()
        
        # Query for completed lists (should use status index)
        result = await db_session.execute(
            select(List).where(List.status == ListStatus.COMPLETED)
        )
        completed_lists = result.scalars().all()
        
        # Should find exactly 3 completed lists
        completed_count = sum(1 for lst in completed_lists if unique_id in lst.name)
        assert completed_count == 3