"""
Test suite for PropertyRadar CSV parser implementation.

Tests comprehensive parsing of PropertyRadar CSV files with 39 columns,
creating Property and Contact objects with proper validation and error handling.
"""

import pytest
import asyncio
import io
from decimal import Decimal
from datetime import datetime
from typing import List, Dict, Any
from unittest.mock import AsyncMock, Mock, patch

from sqlalchemy.ext.asyncio import AsyncSession

# These imports will fail initially - expected in RED phase
try:
    from app.services.property_radar_parser import PropertyRadarParser, PropertyRadarParseResult
except ImportError:
    # Expected during RED phase - parser doesn't exist yet
    PropertyRadarParser = None
    PropertyRadarParseResult = None

# Import models that exist
from app.models import Property, Contact, User
from app.models.list import List as PropertyList


@pytest.fixture
def sample_csv_header():
    """PropertyRadar CSV header with 39 columns."""
    return "Type,Address,City,ZIP,Subdivision,Longitude,Latitude,APN,Yr Built,Purchase Date,Purchase Mos Since,Sq Ft,Beds,Baths,Est Value,Est Equity $,Owner,Mail Address,Mail City,Mail State,Mail ZIP,Owner Occ?,Listed for Sale?,Listing Status,Foreclosure?,Est Equity %,High Equity?,Primary Name,Primary Mobile Phone1,Primary Mobile 1 Status,Primary Email1,Primary Email 1 Status,Primary Email1 Hash,Secondary Name,Secondary Mobile Phone1,Secondary Mobile 1 Status,Secondary Email1,Secondary Email 1 Status,Secondary Email1 Hash"

@pytest.fixture
def sample_csv_row():
    """Sample PropertyRadar CSV row with complete data."""
    return "SFR,455 MIDDLE ST,BRAINTREE,02184,BRAINTREE,-70.987754,42.211216,BRAI-001001-000000-000018,1954,2017-07-28,66,2050,4,2,767509,402357,\"LINKER,JON J & AIMEE C\",455 MIDDLE ST,BRAINTREE,MA,02184,1,0,,0,52,1,JON LINKER,339-222-4624,Active,linkeraimee@hotmail.com,Active,dd03ca8fe8f7c75977cde9f8bec35b0cedc0e6f918166da3ab60a3ea9d8c41c7,AIMEE LINKER,781-316-1658,Active,,,"

@pytest.fixture
def minimal_csv_row():
    """Minimal CSV row with required fields only."""
    return "SFR,123 TEST ST,TESTCITY,12345,,,,,,,,,,,,,\"TEST,OWNER\",,,,,,,,,,,,,,,,,,,"

@pytest.fixture
def invalid_csv_row():
    """CSV row with invalid data types."""
    return "INVALID_TYPE,123 TEST ST,TESTCITY,INVALID_ZIP,,-200.0,91.0,APN123,INVALID_YEAR,INVALID_DATE,INVALID_MONTHS,INVALID_SQFT,INVALID_BEDS,INVALID_BATHS,INVALID_VALUE,INVALID_EQUITY,\"OWNER,NAME\",,,,,INVALID_BOOL,INVALID_BOOL,,INVALID_BOOL,INVALID_PERCENT,INVALID_BOOL,,,,,,,,"

@pytest.fixture
def complete_csv_data(sample_csv_header, sample_csv_row, minimal_csv_row):
    """Complete CSV data for testing."""
    return f"{sample_csv_header}\n{sample_csv_row}\n{minimal_csv_row}"


class TestPropertyRadarCSVParsing:
    """Test CSV parsing functionality."""
    
    @pytest.fixture
    def sample_csv_header(self):
        """PropertyRadar CSV header with 39 columns."""
        return "Type,Address,City,ZIP,Subdivision,Longitude,Latitude,APN,Yr Built,Purchase Date,Purchase Mos Since,Sq Ft,Beds,Baths,Est Value,Est Equity $,Owner,Mail Address,Mail City,Mail State,Mail ZIP,Owner Occ?,Listed for Sale?,Listing Status,Foreclosure?,Est Equity %,High Equity?,Primary Name,Primary Mobile Phone1,Primary Mobile 1 Status,Primary Email1,Primary Email 1 Status,Primary Email1 Hash,Secondary Name,Secondary Mobile Phone1,Secondary Mobile 1 Status,Secondary Email1,Secondary Email 1 Status,Secondary Email1 Hash"
    
    @pytest.fixture
    def sample_csv_row(self):
        """Sample PropertyRadar CSV row with complete data."""
        return "SFR,455 MIDDLE ST,BRAINTREE,02184,BRAINTREE,-70.987754,42.211216,BRAI-001001-000000-000018,1954,2017-07-28,66,2050,4,2,767509,402357,\"LINKER,JON J & AIMEE C\",455 MIDDLE ST,BRAINTREE,MA,02184,1,0,,0,52,1,JON LINKER,339-222-4624,Active,linkeraimee@hotmail.com,Active,dd03ca8fe8f7c75977cde9f8bec35b0cedc0e6f918166da3ab60a3ea9d8c41c7,AIMEE LINKER,781-316-1658,Active,,,"
    
    @pytest.fixture
    def minimal_csv_row(self):
        """Minimal CSV row with required fields only."""
        return "SFR,123 TEST ST,TESTCITY,12345,,,,,,,,,,,,,\"TEST,OWNER\",,,,,,,,,,,,,,,,,,,,"
    
    @pytest.fixture
    def invalid_csv_row(self):
        """CSV row with invalid data types."""
        return "INVALID_TYPE,123 TEST ST,TESTCITY,INVALID_ZIP,,-200.0,91.0,APN123,INVALID_YEAR,INVALID_DATE,INVALID_MONTHS,INVALID_SQFT,INVALID_BEDS,INVALID_BATHS,INVALID_VALUE,INVALID_EQUITY,\"OWNER,NAME\",,,,,INVALID_BOOL,INVALID_BOOL,,INVALID_BOOL,INVALID_PERCENT,INVALID_BOOL,,,,,,,,,,"
    
    @pytest.fixture
    def complete_csv_data(self, sample_csv_header, sample_csv_row, minimal_csv_row):
        """Complete CSV data for testing."""
        return f"{sample_csv_header}\n{sample_csv_row}\n{minimal_csv_row}"
    
    @pytest.mark.asyncio
    async def test_parser_initialization(self, db_session: AsyncSession):
        """Test PropertyRadarParser initialization."""
        # Will fail initially - parser doesn't exist
        parser = PropertyRadarParser(db_session)
        
        assert parser is not None
        assert hasattr(parser, 'parse_csv')
        assert hasattr(parser, 'validate_csv_structure')
    
    @pytest.mark.asyncio
    async def test_csv_header_validation(self, db_session: AsyncSession, sample_csv_header):
        """Test CSV header validation with correct 39 columns."""
        parser = PropertyRadarParser(db_session)
        csv_content = io.StringIO(f"{sample_csv_header}\n")
        
        # Should validate successfully
        is_valid = await parser.validate_csv_structure(csv_content)
        assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_csv_header_validation_wrong_columns(self, db_session: AsyncSession):
        """Test CSV header validation with incorrect columns."""
        parser = PropertyRadarParser(db_session)
        invalid_header = "Col1,Col2,Col3"  # Only 3 columns instead of 39
        csv_content = io.StringIO(f"{invalid_header}\n")
        
        # Should fail validation
        is_valid = await parser.validate_csv_structure(csv_content)
        assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_csv_header_validation_missing_required_columns(self, db_session: AsyncSession):
        """Test CSV header validation with missing required columns."""
        parser = PropertyRadarParser(db_session)
        # Missing 'Address' column
        invalid_header = "Type,City,ZIP,Subdivision,Longitude,Latitude,APN,Yr Built,Purchase Date,Purchase Mos Since,Sq Ft,Beds,Baths,Est Value,Est Equity $,Owner,Mail Address,Mail City,Mail State,Mail ZIP,Owner Occ?,Listed for Sale?,Listing Status,Foreclosure?,Est Equity %,High Equity?,Primary Name,Primary Mobile Phone1,Primary Mobile 1 Status,Primary Email1,Primary Email 1 Status,Primary Email1 Hash,Secondary Name,Secondary Mobile Phone1,Secondary Mobile 1 Status,Secondary Email1,Secondary Email 1 Status,Secondary Email1 Hash"
        csv_content = io.StringIO(f"{invalid_header}\n")
        
        # Should fail validation
        is_valid = await parser.validate_csv_structure(csv_content)
        assert is_valid is False


class TestPropertyObjectCreation:
    """Test Property object creation from CSV data."""
    
    @pytest.mark.asyncio
    async def test_create_property_from_complete_row(self, db_session: AsyncSession):
        """Test Property creation from complete CSV row."""
        parser = PropertyRadarParser(db_session)
        row_data = {
            'Type': 'SFR',
            'Address': '455 MIDDLE ST',
            'City': 'BRAINTREE', 
            'ZIP': '02184',
            'Subdivision': 'BRAINTREE',
            'Longitude': '-70.987754',
            'Latitude': '42.211216',
            'APN': 'BRAI-001001-000000-000018',
            'Yr Built': '1954',
            'Purchase Date': '2017-07-28',
            'Purchase Mos Since': '66',
            'Sq Ft': '2050',
            'Beds': '4',
            'Baths': '2',
            'Est Value': '767509',
            'Est Equity $': '402357',
            'Owner': 'LINKER,JON J & AIMEE C',
            'Mail Address': '455 MIDDLE ST',
            'Mail City': 'BRAINTREE',
            'Mail State': 'MA',
            'Mail ZIP': '02184',
            'Owner Occ?': '1',
            'Listed for Sale?': '0',
            'Listing Status': '',
            'Foreclosure?': '0',
            'Est Equity %': '52',
            'High Equity?': '1'
        }
        
        property_obj = await parser._create_property_from_row(row_data)
        
        # Test Property fields
        assert property_obj.property_type == 'SFR'
        assert property_obj.address == '455 MIDDLE ST'
        assert property_obj.city == 'BRAINTREE'
        assert property_obj.zip_code == '02184'
        assert property_obj.subdivision == 'BRAINTREE'
        assert property_obj.longitude == Decimal('-70.987754')
        assert property_obj.latitude == Decimal('42.211216')
        assert property_obj.apn == 'BRAI-001001-000000-000018'
        assert property_obj.year_built == 1954
        assert property_obj.purchase_date.year == 2017
        assert property_obj.purchase_date.month == 7
        assert property_obj.purchase_date.day == 28
        assert property_obj.purchase_months_since == 66
        assert property_obj.square_feet == 2050
        assert property_obj.bedrooms == 4
        assert property_obj.bathrooms == Decimal('2')
        assert property_obj.est_value == Decimal('767509')
        assert property_obj.est_equity_dollar == Decimal('402357')
        assert property_obj.owner_name == 'LINKER,JON J & AIMEE C'
        assert property_obj.mail_address == '455 MIDDLE ST'
        assert property_obj.mail_city == 'BRAINTREE'
        assert property_obj.mail_state == 'MA'
        assert property_obj.mail_zip == '02184'
        assert property_obj.owner_occupied is True
        assert property_obj.listed_for_sale is False
        assert property_obj.listing_status == ''
        assert property_obj.foreclosure is False
        assert property_obj.est_equity_percent == Decimal('52')
        assert property_obj.high_equity is True
    
    @pytest.mark.asyncio
    async def test_create_property_from_minimal_row(self, db_session: AsyncSession):
        """Test Property creation from minimal CSV row (only required fields)."""
        parser = PropertyRadarParser(db_session)
        row_data = {
            'Type': 'SFR',
            'Address': '123 TEST ST',
            'City': 'TESTCITY',
            'ZIP': '12345',
            'Owner': 'TEST,OWNER',
            # All other fields empty or missing
        }
        
        property_obj = await parser._create_property_from_row(row_data)
        
        # Test required fields
        assert property_obj.property_type == 'SFR'
        assert property_obj.address == '123 TEST ST'
        assert property_obj.city == 'TESTCITY'
        assert property_obj.zip_code == '12345'
        assert property_obj.owner_name == 'TEST,OWNER'
        
        # Test optional fields are None/default
        assert property_obj.longitude is None
        assert property_obj.latitude is None
        assert property_obj.year_built is None
        assert property_obj.square_feet is None
        assert property_obj.bedrooms is None
        assert property_obj.bathrooms is None
        assert property_obj.est_value is None
        assert property_obj.owner_occupied is None
        assert property_obj.listed_for_sale is False  # Default
        assert property_obj.foreclosure is False  # Default
    
    @pytest.mark.asyncio
    async def test_property_validation_invalid_coordinates(self, db_session: AsyncSession):
        """Test Property validation with invalid coordinates."""
        parser = PropertyRadarParser(db_session)
        row_data = {
            'Type': 'SFR',
            'Address': '123 TEST ST',
            'City': 'TESTCITY',
            'ZIP': '12345',
            'Longitude': '200.0',  # Invalid longitude (> 180)
            'Latitude': '91.0',    # Invalid latitude (> 90)
            'Owner': 'TEST,OWNER'
        }
        
        with pytest.raises(ValueError, match="Invalid coordinates"):
            await parser._create_property_from_row(row_data)
    
    @pytest.mark.asyncio
    async def test_property_validation_invalid_year(self, db_session: AsyncSession):
        """Test Property validation with invalid year built."""
        parser = PropertyRadarParser(db_session)
        row_data = {
            'Type': 'SFR',
            'Address': '123 TEST ST',
            'City': 'TESTCITY',
            'ZIP': '12345',
            'Yr Built': '1800',  # Too old
            'Owner': 'TEST,OWNER'
        }
        
        with pytest.raises(ValueError, match="Invalid year"):
            await parser._create_property_from_row(row_data)


class TestContactExtraction:
    """Test Contact extraction from owner fields."""
    
    @pytest.mark.asyncio
    async def test_extract_primary_contact_complete(self, db_session: AsyncSession, test_user: User):
        """Test extraction of primary contact with complete data."""
        parser = PropertyRadarParser(db_session)
        row_data = {
            'Primary Name': 'JON LINKER',
            'Primary Mobile Phone1': '339-222-4624',
            'Primary Mobile 1 Status': 'Active',
            'Primary Email1': 'linkeraimee@hotmail.com',
            'Primary Email 1 Status': 'Active'
        }
        
        contact = await parser._extract_primary_contact(row_data, test_user.id)
        
        assert contact is not None
        assert contact.name == 'JON LINKER'
        assert contact.phone_number == '+13392224624'  # Normalized
        assert contact.email == 'linkeraimee@hotmail.com'
        assert contact.user_id == test_user.id
    
    @pytest.mark.asyncio
    async def test_extract_secondary_contact_complete(self, db_session: AsyncSession, test_user: User):
        """Test extraction of secondary contact with complete data."""
        parser = PropertyRadarParser(db_session)
        row_data = {
            'Secondary Name': 'AIMEE LINKER',
            'Secondary Mobile Phone1': '781-316-1658',
            'Secondary Mobile 1 Status': 'Active'
        }
        
        contact = await parser._extract_secondary_contact(row_data, test_user.id)
        
        assert contact is not None
        assert contact.name == 'AIMEE LINKER'
        assert contact.phone_number == '+17813161658'  # Normalized
        assert contact.user_id == test_user.id
    
    @pytest.mark.asyncio
    async def test_extract_contact_name_only(self, db_session: AsyncSession, test_user: User):
        """Test contact extraction with name only (no phone/email)."""
        parser = PropertyRadarParser(db_session)
        row_data = {
            'Primary Name': 'JOHN DOE',
            'Primary Mobile Phone1': '',
            'Primary Email1': ''
        }
        
        contact = await parser._extract_primary_contact(row_data, test_user.id)
        
        assert contact is not None
        assert contact.name == 'JOHN DOE'
        assert contact.phone_number is None
        assert contact.email is None
    
    @pytest.mark.asyncio
    async def test_extract_contact_phone_normalization(self, db_session: AsyncSession, test_user: User):
        """Test phone number normalization in contact extraction."""
        parser = PropertyRadarParser(db_session)
        
        test_cases = [
            ('(555) 123-4567', '+15551234567'),
            ('555-123-4567', '+15551234567'),
            ('555 123 4567', '+15551234567'),
            ('5551234567', '+15551234567'),
            ('+1 555 123 4567', '+15551234567'),
            ('', None),
        ]
        
        for input_phone, expected in test_cases:
            row_data = {
                'Primary Name': 'TEST USER',
                'Primary Mobile Phone1': input_phone
            }
            
            contact = await parser._extract_primary_contact(row_data, test_user.id)
            
            if expected is None:
                assert contact.phone_number is None
            else:
                assert contact.phone_number == expected
    
    @pytest.mark.asyncio
    async def test_extract_contact_invalid_phone(self, db_session: AsyncSession, test_user: User):
        """Test contact extraction with invalid phone number."""
        parser = PropertyRadarParser(db_session)
        row_data = {
            'Primary Name': 'TEST USER',
            'Primary Mobile Phone1': '123'  # Too short
        }
        
        # Should create contact but with None phone (validation handled at API level)
        contact = await parser._extract_primary_contact(row_data, test_user.id)
        
        assert contact is not None
        assert contact.name == 'TEST USER'
        # Parser should attempt normalization, API validation will catch invalid phones
    
    @pytest.mark.asyncio
    async def test_extract_contacts_from_owner_field(self, db_session: AsyncSession, test_user: User):
        """Test extracting contacts from the combined Owner field."""
        parser = PropertyRadarParser(db_session)
        
        test_cases = [
            ('SMITH,JOHN J & JANE M', ['JOHN J SMITH', 'JANE M SMITH']),
            ('JOHNSON,ROBERT', ['ROBERT JOHNSON']),
            ('DOE,JOHN & JANE DOE', ['JOHN DOE', 'JANE DOE']),
            ('BROWN,MICHAEL J & SARAH K BROWN', ['MICHAEL J BROWN', 'SARAH K BROWN']),
        ]
        
        for owner_text, expected_names in test_cases:
            contacts = await parser._extract_contacts_from_owner(owner_text, test_user.id)
            
            assert len(contacts) == len(expected_names)
            for contact, expected_name in zip(contacts, expected_names):
                assert contact.name == expected_name
                assert contact.user_id == test_user.id


class TestDataValidationAndTransformation:
    """Test data validation and transformation during parsing."""
    
    @pytest.mark.asyncio
    async def test_boolean_field_parsing(self, db_session: AsyncSession):
        """Test parsing of boolean fields from CSV strings."""
        parser = PropertyRadarParser(db_session)
        
        test_cases = [
            ('1', True),
            ('0', False),
            ('', None),
            ('True', True),
            ('False', False),
            ('yes', True),
            ('no', False),
            ('Y', True),
            ('N', False),
        ]
        
        for input_value, expected in test_cases:
            result = parser._parse_boolean(input_value)
            assert result == expected
    
    @pytest.mark.asyncio
    async def test_numeric_field_parsing(self, db_session: AsyncSession):
        """Test parsing of numeric fields with proper type conversion."""
        parser = PropertyRadarParser(db_session)
        
        # Test integer parsing
        assert parser._parse_integer('123') == 123
        assert parser._parse_integer('') is None
        assert parser._parse_integer('0') == 0
        
        # Test decimal parsing
        assert parser._parse_decimal('123.45') == Decimal('123.45')
        assert parser._parse_decimal('') is None
        assert parser._parse_decimal('0') == Decimal('0')
        
        # Test invalid numbers
        with pytest.raises(ValueError):
            parser._parse_integer('invalid')
        
        with pytest.raises(ValueError):
            parser._parse_decimal('invalid')
    
    @pytest.mark.asyncio
    async def test_date_parsing(self, db_session: AsyncSession):
        """Test date parsing from various formats."""
        parser = PropertyRadarParser(db_session)
        
        test_cases = [
            ('2017-07-28', datetime(2017, 7, 28)),
            ('2023-12-31', datetime(2023, 12, 31)),
            ('', None),
        ]
        
        for input_date, expected in test_cases:
            result = parser._parse_date(input_date)
            if expected is None:
                assert result is None
            else:
                assert result.year == expected.year
                assert result.month == expected.month
                assert result.day == expected.day
    
    @pytest.mark.asyncio
    async def test_coordinate_validation(self, db_session: AsyncSession):
        """Test coordinate validation and range checking."""
        parser = PropertyRadarParser(db_session)
        
        # Valid coordinates
        lat, lng = parser._validate_coordinates('42.211216', '-70.987754')
        assert lat == Decimal('42.211216')
        assert lng == Decimal('-70.987754')
        
        # Empty coordinates
        lat, lng = parser._validate_coordinates('', '')
        assert lat is None
        assert lng is None
        
        # Invalid latitude (out of range)
        with pytest.raises(ValueError, match="Invalid latitude"):
            parser._validate_coordinates('91.0', '-70.0')
        
        # Invalid longitude (out of range)
        with pytest.raises(ValueError, match="Invalid longitude"):
            parser._validate_coordinates('42.0', '181.0')


class TestBatchProcessing:
    """Test batch processing for large CSV files."""
    
    @pytest.mark.asyncio
    async def test_parse_small_csv_file(self, db_session: AsyncSession, complete_csv_data: str, test_user: User):
        """Test parsing a small CSV file completely."""
        parser = PropertyRadarParser(db_session)
        csv_file = io.StringIO(complete_csv_data)
        
        result = await parser.parse_csv(csv_file, test_user.id)
        
        assert isinstance(result, PropertyRadarParseResult)
        assert result.total_rows == 2  # Header + 2 data rows
        assert result.processed_rows == 2
        assert result.failed_rows == 0
        assert len(result.properties) == 2
        assert len(result.contacts) >= 2  # At least one contact per property
        assert len(result.errors) == 0
    
    @pytest.mark.asyncio
    async def test_parse_csv_with_batch_size(self, db_session: AsyncSession, test_user: User):
        """Test CSV parsing with custom batch size."""
        parser = PropertyRadarParser(db_session)
        
        # Create CSV with 5 rows
        header = "Type,Address,City,ZIP,Subdivision,Longitude,Latitude,APN,Yr Built,Purchase Date,Purchase Mos Since,Sq Ft,Beds,Baths,Est Value,Est Equity $,Owner,Mail Address,Mail City,Mail State,Mail ZIP,Owner Occ?,Listed for Sale?,Listing Status,Foreclosure?,Est Equity %,High Equity?,Primary Name,Primary Mobile Phone1,Primary Mobile 1 Status,Primary Email1,Primary Email 1 Status,Primary Email1 Hash,Secondary Name,Secondary Mobile Phone1,Secondary Mobile 1 Status,Secondary Email1,Secondary Email 1 Status,Secondary Email1 Hash"
        rows = []
        for i in range(5):
            rows.append(f'SFR,{i} TEST ST,TESTCITY,1234{i},,,,,,,,,,,,,"OWNER{i},TEST",,,,,,,,,,,,,,,,,,,')
        
        csv_content = f"{header}\n" + "\n".join(rows)
        csv_file = io.StringIO(csv_content)
        
        # Parse with batch size of 2
        result = await parser.parse_csv(csv_file, test_user.id, batch_size=2)
        
        assert result.total_rows == 5
        assert result.processed_rows == 5
        assert len(result.properties) == 5
    
    @pytest.mark.asyncio
    async def test_parse_csv_with_errors(self, db_session: AsyncSession, test_user: User):
        """Test CSV parsing with some invalid rows."""
        parser = PropertyRadarParser(db_session)
        
        header = "Type,Address,City,ZIP,Subdivision,Longitude,Latitude,APN,Yr Built,Purchase Date,Purchase Mos Since,Sq Ft,Beds,Baths,Est Value,Est Equity $,Owner,Mail Address,Mail City,Mail State,Mail ZIP,Owner Occ?,Listed for Sale?,Listing Status,Foreclosure?,Est Equity %,High Equity?,Primary Name,Primary Mobile Phone1,Primary Mobile 1 Status,Primary Email1,Primary Email 1 Status,Primary Email1 Hash,Secondary Name,Secondary Mobile Phone1,Secondary Mobile 1 Status,Secondary Email1,Secondary Email 1 Status,Secondary Email1 Hash"
        
        # Mix valid and invalid rows
        rows = [
            'SFR,123 VALID ST,TESTCITY,12345,,,,,,,,,,,,,"VALID,OWNER",,,,,,,,,,,,,,,,,,,',
            # Missing required field (address)
            'SFR,,TESTCITY,12345,,,,,,,,,,,,,"INVALID,OWNER",,,,,,,,,,,,,,,,,,,',
            'CONDO,456 ANOTHER ST,TESTCITY,67890,,,,,,,,,,,,,"ANOTHER,OWNER",,,,,,,,,,,,,,,,,,,',
        ]
        
        csv_content = f"{header}\n" + "\n".join(rows)
        csv_file = io.StringIO(csv_content)
        
        result = await parser.parse_csv(csv_file, test_user.id)
        
        assert result.total_rows == 3
        assert result.processed_rows == 2  # 2 valid rows
        assert result.failed_rows == 1    # 1 invalid row
        assert len(result.properties) == 2
        assert len(result.errors) == 1
        assert "Missing required field" in result.errors[0]
    
    @pytest.mark.asyncio
    async def test_parse_large_csv_performance(self, db_session: AsyncSession, test_user: User):
        """Test performance with large CSV file (1000+ rows)."""
        parser = PropertyRadarParser(db_session)
        
        # Generate large CSV in memory
        header = "Type,Address,City,ZIP,Subdivision,Longitude,Latitude,APN,Yr Built,Purchase Date,Purchase Mos Since,Sq Ft,Beds,Baths,Est Value,Est Equity $,Owner,Mail Address,Mail City,Mail State,Mail ZIP,Owner Occ?,Listed for Sale?,Listing Status,Foreclosure?,Est Equity %,High Equity?,Primary Name,Primary Mobile Phone1,Primary Mobile 1 Status,Primary Email1,Primary Email 1 Status,Primary Email1 Hash,Secondary Name,Secondary Mobile Phone1,Secondary Mobile 1 Status,Secondary Email1,Secondary Email 1 Status,Secondary Email1 Hash"
        
        # Generate 1000 rows
        rows = []
        for i in range(1000):
            rows.append(f'SFR,{i} PERFORMANCE ST,TESTCITY,{12345 + i % 100},,,,,,,,,,,,,"OWNER{i},TEST",,,,,,,,,,,,,,,,,,,')
        
        csv_content = f"{header}\n" + "\n".join(rows)
        csv_file = io.StringIO(csv_content)
        
        import time
        start_time = time.time()
        
        result = await parser.parse_csv(csv_file, test_user.id, batch_size=100)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Verify results
        assert result.total_rows == 1000
        assert result.processed_rows == 1000
        assert len(result.properties) == 1000
        
        # Performance assertion - should process 1000 rows in < 10 seconds
        assert processing_time < 10.0, f"Processing took too long: {processing_time:.2f}s"
        
        # Memory efficiency - check memory usage doesn't grow excessively
        # This is a simple check - in real implementation might need more sophisticated memory monitoring
        assert len(result.properties) == 1000  # All objects created


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.mark.asyncio
    async def test_empty_csv_file(self, db_session: AsyncSession, test_user: User):
        """Test handling of empty CSV file."""
        parser = PropertyRadarParser(db_session)
        empty_csv = io.StringIO("")
        
        result = await parser.parse_csv(empty_csv, test_user.id)
        
        assert result.total_rows == 0
        assert result.processed_rows == 0
        assert len(result.properties) == 0
        assert len(result.errors) == 1
        assert "Empty CSV file" in result.errors[0]
    
    @pytest.mark.asyncio
    async def test_csv_header_only(self, db_session: AsyncSession, test_user: User, sample_csv_header: str):
        """Test CSV with header but no data rows."""
        parser = PropertyRadarParser(db_session)
        header_only_csv = io.StringIO(sample_csv_header)
        
        result = await parser.parse_csv(header_only_csv, test_user.id)
        
        assert result.total_rows == 0
        assert result.processed_rows == 0
        assert len(result.properties) == 0
        assert len(result.errors) == 1
        assert "No data rows" in result.errors[0]
    
    @pytest.mark.asyncio
    async def test_malformed_csv_row(self, db_session: AsyncSession, test_user: User, sample_csv_header: str):
        """Test handling of malformed CSV rows."""
        parser = PropertyRadarParser(db_session)
        
        # Row with too few columns
        malformed_row = "SFR,123 TEST ST,TESTCITY"  # Missing many columns
        csv_content = f"{sample_csv_header}\n{malformed_row}"
        csv_file = io.StringIO(csv_content)
        
        result = await parser.parse_csv(csv_file, test_user.id)
        
        assert result.total_rows == 1
        assert result.failed_rows == 1
        assert len(result.errors) == 1
        assert "Malformed CSV row" in result.errors[0]
    
    @pytest.mark.asyncio
    async def test_duplicate_properties_handling(self, db_session: AsyncSession, test_user: User, sample_csv_header: str):
        """Test handling of duplicate properties in CSV."""
        parser = PropertyRadarParser(db_session)
        
        # Two identical rows
        duplicate_row = 'SFR,123 TEST ST,TESTCITY,12345,,,,,,,,,,,,,"TEST,OWNER",,,,,,,,,,,,,,,,,,,,'
        csv_content = f"{sample_csv_header}\n{duplicate_row}\n{duplicate_row}"
        csv_file = io.StringIO(csv_content)
        
        result = await parser.parse_csv(csv_file, test_user.id)
        
        # Should handle duplicates gracefully
        assert result.total_rows == 2
        # Implementation detail: might merge or keep separate based on business rules
        assert len(result.properties) >= 1  # At least one property created
    
    @pytest.mark.asyncio
    async def test_database_transaction_rollback_on_error(self, db_session: AsyncSession, test_user: User):
        """Test that database transactions are rolled back properly on errors."""
        parser = PropertyRadarParser(db_session)
        
        # Mock database error during save
        with patch.object(db_session, 'commit', side_effect=Exception("Database error")):
            csv_content = 'Type,Address,City,ZIP,Owner\nSFR,123 TEST ST,TESTCITY,12345,"TEST,OWNER"'
            csv_file = io.StringIO(csv_content)
            
            result = await parser.parse_csv(csv_file, test_user.id)
            
            # Should handle database errors gracefully
            assert result.failed_rows > 0
            assert "Database error" in str(result.errors)
    
    @pytest.mark.asyncio
    async def test_memory_limit_handling(self, db_session: AsyncSession, test_user: User):
        """Test handling of very large CSV files that might exceed memory."""
        parser = PropertyRadarParser(db_session)
        
        # Test with a reasonable size CSV to simulate memory constraints
        # In real implementation, this would test streaming processing
        
        # Set a low batch size to simulate memory constraints
        small_batch_size = 5
        
        # Create CSV with moderate number of rows
        header = "Type,Address,City,ZIP,Owner"
        rows = [f'SFR,{i} MEMORY ST,TESTCITY,{12345 + i},"OWNER{i},TEST"' for i in range(50)]
        csv_content = f"{header}\n" + "\n".join(rows)
        csv_file = io.StringIO(csv_content)
        
        result = await parser.parse_csv(csv_file, test_user.id, batch_size=small_batch_size)
        
        # Should process all rows despite small batch size
        assert result.total_rows == 50
        assert result.processed_rows == 50


class TestPropertyRadarParseResult:
    """Test the PropertyRadarParseResult data class."""
    
    def test_parse_result_initialization(self):
        """Test PropertyRadarParseResult initialization."""
        result = PropertyRadarParseResult()
        
        assert result.total_rows == 0
        assert result.processed_rows == 0
        assert result.failed_rows == 0
        assert result.properties == []
        assert result.contacts == []
        assert result.errors == []
        assert result.warnings == []
    
    def test_parse_result_success_rate_calculation(self):
        """Test success rate calculation in PropertyRadarParseResult."""
        result = PropertyRadarParseResult()
        result.total_rows = 100
        result.processed_rows = 85
        result.failed_rows = 15
        
        assert result.success_rate == 0.85
    
    def test_parse_result_success_rate_zero_division(self):
        """Test success rate with zero total rows."""
        result = PropertyRadarParseResult()
        result.total_rows = 0
        
        assert result.success_rate == 0.0
    
    def test_parse_result_summary_generation(self):
        """Test summary generation in PropertyRadarParseResult."""
        result = PropertyRadarParseResult()
        result.total_rows = 100
        result.processed_rows = 95
        result.failed_rows = 5
        result.properties = ['prop1', 'prop2']  # Mock objects
        result.contacts = ['contact1', 'contact2', 'contact3']  # Mock objects
        result.errors = ['Error 1', 'Error 2']
        
        summary = result.get_summary()
        
        assert "Total rows: 100" in summary
        assert "Processed: 95" in summary
        assert "Failed: 5" in summary
        assert "Properties created: 2" in summary
        assert "Contacts created: 3" in summary
        assert "Success rate: 95.0%" in summary


class TestIntegrationWithDatabase:
    """Test integration with database operations."""
    
    @pytest.mark.asyncio
    async def test_property_saved_to_database(self, db_session: AsyncSession, test_user: User):
        """Test that parsed properties are actually saved to database."""
        parser = PropertyRadarParser(db_session)
        
        csv_content = '''Type,Address,City,ZIP,Subdivision,Longitude,Latitude,APN,Yr Built,Purchase Date,Purchase Mos Since,Sq Ft,Beds,Baths,Est Value,Est Equity $,Owner,Mail Address,Mail City,Mail State,Mail ZIP,Owner Occ?,Listed for Sale?,Listing Status,Foreclosure?,Est Equity %,High Equity?,Primary Name,Primary Mobile Phone1,Primary Mobile 1 Status,Primary Email1,Primary Email 1 Status,Primary Email1 Hash,Secondary Name,Secondary Mobile Phone1,Secondary Mobile 1 Status,Secondary Email1,Secondary Email 1 Status,Secondary Email1 Hash
SFR,123 DATABASE ST,TESTCITY,12345,,,,,,,,,,,,,"TEST,OWNER",,,,,,,,,,,,,,,,,,,'''
        
        csv_file = io.StringIO(csv_content)
        result = await parser.parse_csv(csv_file, test_user.id)
        
        # Verify property saved to database
        from sqlalchemy import select
        query = select(Property).where(Property.address == '123 DATABASE ST')
        result_db = await db_session.execute(query)
        property_from_db = result_db.scalar_one_or_none()
        
        assert property_from_db is not None
        assert property_from_db.address == '123 DATABASE ST'
        assert property_from_db.city == 'TESTCITY'
        assert property_from_db.zip_code == '12345'
    
    @pytest.mark.asyncio
    async def test_contacts_saved_to_database(self, db_session: AsyncSession, test_user: User):
        """Test that parsed contacts are saved to database."""
        parser = PropertyRadarParser(db_session)
        
        csv_content = '''Type,Address,City,ZIP,Subdivision,Longitude,Latitude,APN,Yr Built,Purchase Date,Purchase Mos Since,Sq Ft,Beds,Baths,Est Value,Est Equity $,Owner,Mail Address,Mail City,Mail State,Mail ZIP,Owner Occ?,Listed for Sale?,Listing Status,Foreclosure?,Est Equity %,High Equity?,Primary Name,Primary Mobile Phone1,Primary Mobile 1 Status,Primary Email1,Primary Email 1 Status,Primary Email1 Hash,Secondary Name,Secondary Mobile Phone1,Secondary Mobile 1 Status,Secondary Email1,Secondary Email 1 Status,Secondary Email1 Hash
SFR,123 CONTACT ST,TESTCITY,12345,,,,,,,,,,,,,"TEST,OWNER",,,,,,,,,,,JOHN TESTER,555-123-4567,Active,john@test.com,Active,,JANE TESTER,555-987-6543,Active,jane@test.com,Active,'''
        
        csv_file = io.StringIO(csv_content)
        result = await parser.parse_csv(csv_file, test_user.id)
        
        # Verify contacts saved to database
        from sqlalchemy import select
        query = select(Contact).where(Contact.name == 'JOHN TESTER')
        result_db = await db_session.execute(query)
        contact_from_db = result_db.scalar_one_or_none()
        
        assert contact_from_db is not None
        assert contact_from_db.name == 'JOHN TESTER'
        assert contact_from_db.phone_number == '+15551234567'
        assert contact_from_db.email == 'john@test.com'
        assert contact_from_db.user_id == test_user.id
    
    @pytest.mark.asyncio
    async def test_property_contact_relationships(self, db_session: AsyncSession, test_user: User):
        """Test that property-contact relationships are established."""
        parser = PropertyRadarParser(db_session)
        
        csv_content = '''Type,Address,City,ZIP,Subdivision,Longitude,Latitude,APN,Yr Built,Purchase Date,Purchase Mos Since,Sq Ft,Beds,Baths,Est Value,Est Equity $,Owner,Mail Address,Mail City,Mail State,Mail ZIP,Owner Occ?,Listed for Sale?,Listing Status,Foreclosure?,Est Equity %,High Equity?,Primary Name,Primary Mobile Phone1,Primary Mobile 1 Status,Primary Email1,Primary Email 1 Status,Primary Email1 Hash,Secondary Name,Secondary Mobile Phone1,Secondary Mobile 1 Status,Secondary Email1,Secondary Email 1 Status,Secondary Email1 Hash
SFR,123 RELATIONSHIP ST,TESTCITY,12345,,,,,,,,,,,,,"DOE,JOHN & JANE",,,,,,,,,,,JOHN DOE,555-111-2222,Active,john@doe.com,Active,,JANE DOE,555-333-4444,Active,jane@doe.com,Active,'''
        
        csv_file = io.StringIO(csv_content)
        result = await parser.parse_csv(csv_file, test_user.id)
        
        # Get property from database
        from sqlalchemy import select
        query = select(Property).where(Property.address == '123 RELATIONSHIP ST')
        result_db = await db_session.execute(query)
        property_from_db = result_db.scalar_one_or_none()
        
        assert property_from_db is not None
        
        # Load relationships
        await db_session.refresh(property_from_db, ['contacts'])
        
        # Verify relationships
        assert len(property_from_db.contacts) >= 2  # At least primary and secondary contacts
        contact_names = [contact.name for contact in property_from_db.contacts]
        assert 'JOHN DOE' in contact_names or any('JOHN' in name for name in contact_names)
    
    @pytest.mark.asyncio
    async def test_property_list_assignment(self, db_session: AsyncSession, test_user: User):
        """Test that properties are assigned to a PropertyList."""
        # Create a PropertyList first
        from app.models.list import List
        
        from app.models.list import ListSource
        property_list = List(
            name="Test Import List",
            user_id=test_user.id,
            source=ListSource.PROPERTY_RADAR,
            total_rows_imported=0
        )
        db_session.add(property_list)
        await db_session.commit()
        await db_session.refresh(property_list)
        
        parser = PropertyRadarParser(db_session)
        
        csv_content = '''Type,Address,City,ZIP,Subdivision,Longitude,Latitude,APN,Yr Built,Purchase Date,Purchase Mos Since,Sq Ft,Beds,Baths,Est Value,Est Equity $,Owner,Mail Address,Mail City,Mail State,Mail ZIP,Owner Occ?,Listed for Sale?,Listing Status,Foreclosure?,Est Equity %,High Equity?,Primary Name,Primary Mobile Phone1,Primary Mobile 1 Status,Primary Email1,Primary Email 1 Status,Primary Email1 Hash,Secondary Name,Secondary Mobile Phone1,Secondary Mobile 1 Status,Secondary Email1,Secondary Email 1 Status,Secondary Email1 Hash
SFR,123 LIST ST,TESTCITY,12345,,,,,,,,,,,,,"LIST,OWNER",,,,,,,,,,,,,,,,,,,'''
        
        csv_file = io.StringIO(csv_content)
        result = await parser.parse_csv(csv_file, test_user.id, source_list_id=property_list.id)
        
        # Verify property assigned to list
        from sqlalchemy import select
        query = select(Property).where(Property.address == '123 LIST ST')
        result_db = await db_session.execute(query)
        property_from_db = result_db.scalar_one_or_none()
        
        assert property_from_db is not None
        assert property_from_db.source_list_id == property_list.id


class TestPerformanceBenchmarks:
    """Test performance benchmarks for CSV parsing."""
    
    @pytest.mark.asyncio
    async def test_parsing_speed_benchmark(self, db_session: AsyncSession, test_user: User):
        """Benchmark parsing speed for different file sizes."""
        parser = PropertyRadarParser(db_session)
        
        # Test different row counts
        row_counts = [100, 500, 1000]
        
        for row_count in row_counts:
            # Create fresh parser for each iteration to avoid session state issues
            parser = PropertyRadarParser(db_session)
            
            # Generate test CSV
            header = "Type,Address,City,ZIP,Owner"
            rows = [f'SFR,{i}_BENCH_{row_count}_ST,TESTCITY,{12345 + i},"OWNER{i},TEST"' for i in range(row_count)]
            csv_content = f"{header}\n" + "\n".join(rows)
            csv_file = io.StringIO(csv_content)
            
            import time
            start_time = time.time()
            
            result = await parser.parse_csv(csv_file, test_user.id)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Calculate rows per second
            rows_per_second = row_count / processing_time if processing_time > 0 else 0
            
            # Performance assertions
            assert result.processed_rows == row_count
            assert rows_per_second > 50, f"Too slow: {rows_per_second:.1f} rows/sec for {row_count} rows"
            
            print(f"Processed {row_count} rows in {processing_time:.2f}s ({rows_per_second:.1f} rows/sec)")
    
    @pytest.mark.asyncio
    async def test_memory_usage_large_file(self, db_session: AsyncSession, test_user: User):
        """Test memory usage with large CSV files."""
        parser = PropertyRadarParser(db_session)
        
        # Test with streaming approach for large files
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Process 5000 rows with streaming
        row_count = 5000
        header = "Type,Address,City,ZIP,Owner"
        rows = [f'SFR,{i} MEMORY ST,TESTCITY,{12345 + i},"OWNER{i},TEST"' for i in range(row_count)]
        csv_content = f"{header}\n" + "\n".join(rows)
        csv_file = io.StringIO(csv_content)
        
        result = await parser.parse_csv(csv_file, test_user.id, batch_size=100)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory efficiency assertions
        assert result.processed_rows == row_count
        assert memory_increase < 500, f"Memory usage too high: {memory_increase:.1f}MB increase"
        
        print(f"Memory increase: {memory_increase:.1f}MB for {row_count} rows")