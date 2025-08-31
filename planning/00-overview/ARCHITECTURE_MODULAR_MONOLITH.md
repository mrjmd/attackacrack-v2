# Modular Monolith Architecture for Attack-a-Crack v2

## Executive Summary

We're adopting a **split architecture** for v2:
- **Backend**: FastAPI modular monolith with clear module boundaries
- **Frontend**: SvelteKit application consuming the backend API

This gives us the simplicity of a monolithic backend with the flexibility of a decoupled frontend, learning from companies like GitHub, Shopify, and Stripe who successfully use modular monoliths at scale.

## Architecture Overview

### The Two-Application Model

```
┌─────────────────────────────────────┐
│       SvelteKit Frontend            │
│   (Separate Client Application)      │
│                                      │
│  • Server-side rendering (SSR)      │
│  • Client-side interactivity        │
│  • Consumes backend API             │
│  • Own deployment pipeline          │
└─────────────────────────────────────┘
                   │
                   │ HTTPS/JSON API
                   │
┌─────────────────────────────────────┐
│     FastAPI Backend                 │
│    (Modular Monolith)              │
│                                     │
│  ┌─────────┐ ┌─────────┐          │
│  │Contacts │ │Campaigns│          │
│  │ Module  │ │ Module  │          │
│  └─────────┘ └─────────┘          │
│  ┌─────────┐ ┌─────────┐          │
│  │Messaging│ │Properties│         │
│  │ Module  │ │ Module  │          │
│  └─────────┘ └─────────┘          │
│                                    │
│  All modules in single deployment  │
└────────────────────────────────────┘
                   │
                   │
         ┌─────────────────┐
         │   PostgreSQL    │
         │    Database     │
         └─────────────────┘
```

## Why This Architecture?

### Problems with v1's Architecture
- **Service Soup**: 49 services with unclear boundaries
- **Dependency Hell**: Circular dependencies everywhere
- **Test Complexity**: Required complex mocking and isolation
- **Duplication**: Same logic in multiple places
- **No Clear Boundaries**: Everything imports everything

### Benefits of Our Split Architecture

#### Backend (Modular Monolith)
- **Single Deployment**: One backend to deploy and monitor
- **Shared Database**: ACID transactions, no distributed transactions
- **Clear Boundaries**: Modules communicate through defined interfaces
- **Progressive Extraction**: Can extract modules to microservices if needed
- **Simple Testing**: No complex service mocking required
- **Fast Development**: No network calls between modules

#### Frontend (SvelteKit)
- **Independent Deployment**: Frontend can be updated without backend changes
- **Modern DX**: Hot module replacement, TypeScript, component architecture
- **Optimal Performance**: Static generation, edge deployment, client-side routing
- **Technology Freedom**: Can switch frontend frameworks without touching backend

## Core Principles

### 1. Backend Module Independence
Each backend module is self-contained with its own:
- Models (SQLAlchemy ORM)
- Schemas (Pydantic validation)
- Services (business logic)
- API routes (FastAPI endpoints)
- Tests (pytest)

### 2. API-First Design
The backend exposes a RESTful API that:
- Uses consistent naming conventions
- Returns predictable JSON structures
- Includes proper HTTP status codes
- Provides OpenAPI documentation
- Supports versioning when needed

### 3. Frontend-Backend Separation
- Frontend never directly accesses the database
- All data flows through the API
- Authentication via JWT tokens
- Real-time updates via WebSockets

### 4. Storage Abstraction (Future-Proofing)
To enable smooth transition from single-server to multi-server deployment:

```python
# backend/app/core/storage.py
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO

class StorageService(ABC):
    """Abstract storage interface for media/files"""
    
    @abstractmethod
    async def store(self, key: str, data: bytes) -> str:
        """Store data and return URL/path"""
        pass
    
    @abstractmethod
    async def retrieve(self, key: str) -> bytes:
        """Retrieve data by key"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete data by key"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        pass

# MVP Implementation - Local filesystem
class LocalFileStorage(StorageService):
    """Local filesystem storage for MVP"""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    async def store(self, key: str, data: bytes) -> str:
        file_path = self.base_path / key
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(data)
        return f"/media/{key}"  # URL path for retrieval
    
    async def retrieve(self, key: str) -> bytes:
        file_path = self.base_path / key
        return file_path.read_bytes()
    
    async def delete(self, key: str) -> bool:
        file_path = self.base_path / key
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    
    async def exists(self, key: str) -> bool:
        return (self.base_path / key).exists()

# Future Implementation - DigitalOcean Spaces
class SpacesStorage(StorageService):
    """DigitalOcean Spaces storage for production"""
    
    def __init__(self, bucket_name: str, region: str):
        # Implementation for S3-compatible storage
        pass
    
    # ... implement abstract methods
```

**Why This Matters:**
- MVP uses local storage (simple, fast)
- Production can switch to Spaces/S3 with one-line change
- No code changes needed in services using storage
- Enables horizontal scaling later

## Project Structure

### Complete Application Structure
```
attackacrack-v2/
├── backend/                          # FastAPI Modular Monolith
│   ├── app/
│   │   ├── core/                    # Shared kernel (minimal)
│   │   │   ├── config.py           # Configuration management
│   │   │   ├── database.py         # Database connection
│   │   │   ├── dependencies.py     # FastAPI dependencies
│   │   │   ├── events.py           # Event bus
│   │   │   ├── exceptions.py       # Base exceptions
│   │   │   ├── security.py         # JWT, password hashing
│   │   │   └── types.py            # Shared type definitions
│   │   │
│   │   ├── modules/
│   │   │   ├── contacts/           # Contact Management Module
│   │   │   │   ├── __init__.py     # Module initialization
│   │   │   │   ├── models.py       # SQLAlchemy models
│   │   │   │   ├── schemas.py      # Pydantic schemas
│   │   │   │   ├── service.py      # Business logic
│   │   │   │   ├── repository.py   # Data access layer
│   │   │   │   ├── api.py          # FastAPI routes
│   │   │   │   ├── events.py       # Module events
│   │   │   │   └── tests/
│   │   │   │       ├── test_service.py
│   │   │   │       ├── test_api.py
│   │   │   │       └── test_integration.py
│   │   │   │
│   │   │   ├── campaigns/          # Campaign Module
│   │   │   ├── messaging/          # OpenPhone Integration
│   │   │   ├── properties/         # PropertyRadar Integration
│   │   │   └── billing/            # QuickBooks Integration
│   │   │
│   │   └── main.py                 # FastAPI app initialization
│   │
│   ├── migrations/                  # Alembic database migrations
│   ├── tests/                       # Cross-module integration tests
│   └── requirements.txt
│
├── frontend/                        # SvelteKit Application
│   ├── src/
│   │   ├── routes/                 # File-based routing
│   │   │   ├── +layout.svelte     # Root layout
│   │   │   ├── +page.svelte       # Home page
│   │   │   ├── contacts/
│   │   │   │   ├── +page.svelte   # Contact list
│   │   │   │   ├── [id]/
│   │   │   │   │   └── +page.svelte # Contact detail
│   │   │   │   └── new/
│   │   │   │       └── +page.svelte # New contact form
│   │   │   └── campaigns/
│   │   │       └── ...
│   │   │
│   │   ├── lib/
│   │   │   ├── api/               # API client layer
│   │   │   │   ├── client.ts      # Base API client
│   │   │   │   ├── contacts.ts    # Contact API calls
│   │   │   │   └── campaigns.ts   # Campaign API calls
│   │   │   ├── components/        # Reusable components
│   │   │   ├── stores/            # Svelte stores (state)
│   │   │   └── utils/             # Helper functions
│   │   │
│   │   └── app.html               # HTML template
│   │
│   ├── static/                    # Static assets
│   ├── tests/                     # Frontend tests
│   └── package.json
│
└── docker-compose.yml             # Development environment
```

## Backend: FastAPI Modular Monolith

### Module Interface Pattern (Python)

Each backend module exposes a clean interface:

```python
# backend/app/modules/contacts/__init__.py
from typing import Optional, List
from uuid import UUID
from .schemas import ContactCreate, ContactUpdate, ContactResponse
from .service import ContactService
from .repository import ContactRepository

class ContactsModule:
    """Public interface for the Contacts module"""
    
    def __init__(self, db_session):
        self.repository = ContactRepository(db_session)
        self.service = ContactService(self.repository)
    
    async def create_contact(self, data: ContactCreate) -> ContactResponse:
        """Create a new contact"""
        return await self.service.create(data)
    
    async def get_contact(self, contact_id: UUID) -> Optional[ContactResponse]:
        """Get contact by ID"""
        return await self.service.get_by_id(contact_id)
    
    async def find_by_phone(self, phone: str) -> Optional[ContactResponse]:
        """Find contact by phone number"""
        return await self.service.find_by_phone(phone)
    
    async def update_contact(
        self, 
        contact_id: UUID, 
        data: ContactUpdate
    ) -> ContactResponse:
        """Update existing contact"""
        return await self.service.update(contact_id, data)
```

### API Route Definition (Python)

```python
# backend/app/modules/contacts/api.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from .schemas import ContactCreate, ContactUpdate, ContactResponse
from . import ContactsModule

router = APIRouter(prefix="/api/v1/contacts", tags=["contacts"])

@router.post("/", response_model=ContactResponse)
async def create_contact(
    data: ContactCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new contact"""
    module = ContactsModule(db)
    return await module.create_contact(data)

@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get contact by ID"""
    module = ContactsModule(db)
    contact = await module.get_contact(contact_id)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    return contact

@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: UUID,
    data: ContactUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update existing contact"""
    module = ContactsModule(db)
    return await module.update_contact(contact_id, data)
```

### Cross-Module Communication (Python)

```python
# backend/app/modules/campaigns/service.py
from typing import List
from uuid import UUID
from app.modules.contacts import ContactsModule
from app.core.events import publish

class CampaignService:
    def __init__(self, db_session):
        self.db = db_session
        self.contacts = ContactsModule(db_session)
    
    async def add_recipients_by_phone(
        self, 
        campaign_id: UUID, 
        phone_numbers: List[str]
    ):
        """Add recipients to campaign by phone number"""
        for phone in phone_numbers:
            # Use contacts module through its public interface
            contact = await self.contacts.find_by_phone(phone)
            if not contact:
                # Create contact if doesn't exist
                contact = await self.contacts.create_contact({
                    "phone": phone,
                    "source": "campaign_import"
                })
            
            # Add to campaign (local operation)
            await self._add_recipient(campaign_id, contact.id)
        
        # Publish event for other modules
        await publish("campaign.recipients.added", {
            "campaign_id": campaign_id,
            "count": len(phone_numbers)
        })
```

## Frontend: SvelteKit Application

### API Client Layer (TypeScript)

```typescript
// frontend/src/lib/api/client.ts
import { browser } from '$app/environment';
import { goto } from '$app/navigation';

interface ApiConfig {
    baseURL: string;
    headers?: Record<string, string>;
}

class ApiClient {
    private config: ApiConfig;
    
    constructor(config: ApiConfig) {
        this.config = config;
    }
    
    private async request<T>(
        endpoint: string,
        options: RequestInit = {}
    ): Promise<T> {
        const url = `${this.config.baseURL}${endpoint}`;
        const token = browser ? localStorage.getItem('token') : null;
        
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...(token ? { Authorization: `Bearer ${token}` } : {}),
                ...this.config.headers,
                ...options.headers,
            },
        });
        
        if (response.status === 401) {
            // Redirect to login on unauthorized
            if (browser) {
                goto('/login');
            }
            throw new Error('Unauthorized');
        }
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'API request failed');
        }
        
        return response.json();
    }
    
    async get<T>(endpoint: string): Promise<T> {
        return this.request<T>(endpoint, { method: 'GET' });
    }
    
    async post<T>(endpoint: string, data: any): Promise<T> {
        return this.request<T>(endpoint, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }
    
    async put<T>(endpoint: string, data: any): Promise<T> {
        return this.request<T>(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }
    
    async delete<T>(endpoint: string): Promise<T> {
        return this.request<T>(endpoint, { method: 'DELETE' });
    }
}

export const api = new ApiClient({
    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
});
```

### Contact API Service (TypeScript)

```typescript
// frontend/src/lib/api/contacts.ts
import { api } from './client';

export interface Contact {
    id: string;
    phone: string;
    email?: string;
    firstName?: string;
    lastName?: string;
    tags: string[];
    createdAt: string;
    updatedAt: string;
}

export interface CreateContactData {
    phone: string;
    email?: string;
    firstName?: string;
    lastName?: string;
    tags?: string[];
}

export interface UpdateContactData {
    email?: string;
    firstName?: string;
    lastName?: string;
    tags?: string[];
}

export const contactsApi = {
    async list(params?: { 
        skip?: number; 
        limit?: number; 
        search?: string 
    }): Promise<{ items: Contact[]; total: number }> {
        const queryString = new URLSearchParams(
            params as Record<string, string>
        ).toString();
        return api.get(`/contacts${queryString ? `?${queryString}` : ''}`);
    },
    
    async get(id: string): Promise<Contact> {
        return api.get(`/contacts/${id}`);
    },
    
    async create(data: CreateContactData): Promise<Contact> {
        return api.post('/contacts', data);
    },
    
    async update(id: string, data: UpdateContactData): Promise<Contact> {
        return api.put(`/contacts/${id}`, data);
    },
    
    async delete(id: string): Promise<void> {
        return api.delete(`/contacts/${id}`);
    },
    
    async importCSV(file: File): Promise<{ imported: number; errors: string[] }> {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/api/v1/contacts/import', {
            method: 'POST',
            body: formData,
            headers: {
                Authorization: `Bearer ${localStorage.getItem('token')}`,
            },
        });
        
        return response.json();
    },
};
```

### SvelteKit Page Component (TypeScript)

```svelte
<!-- frontend/src/routes/contacts/+page.svelte -->
<script lang="ts">
    import { onMount } from 'svelte';
    import { contactsApi, type Contact } from '$lib/api/contacts';
    import ContactList from '$lib/components/ContactList.svelte';
    import SearchBar from '$lib/components/SearchBar.svelte';
    import Pagination from '$lib/components/Pagination.svelte';
    
    let contacts: Contact[] = [];
    let total = 0;
    let loading = true;
    let error: string | null = null;
    let currentPage = 1;
    let searchQuery = '';
    const pageSize = 20;
    
    async function loadContacts() {
        loading = true;
        error = null;
        
        try {
            const response = await contactsApi.list({
                skip: (currentPage - 1) * pageSize,
                limit: pageSize,
                search: searchQuery,
            });
            contacts = response.items;
            total = response.total;
        } catch (err) {
            error = err instanceof Error ? err.message : 'Failed to load contacts';
        } finally {
            loading = false;
        }
    }
    
    function handleSearch(event: CustomEvent<string>) {
        searchQuery = event.detail;
        currentPage = 1;
        loadContacts();
    }
    
    function handlePageChange(event: CustomEvent<number>) {
        currentPage = event.detail;
        loadContacts();
    }
    
    onMount(() => {
        loadContacts();
    });
</script>

<div class="container mx-auto px-4 py-8">
    <header class="mb-8">
        <h1 class="text-3xl font-bold mb-4">Contacts</h1>
        <div class="flex justify-between items-center">
            <SearchBar on:search={handleSearch} />
            <a 
                href="/contacts/new" 
                class="btn btn-primary"
            >
                Add Contact
            </a>
        </div>
    </header>
    
    {#if loading}
        <div class="flex justify-center py-12">
            <div class="spinner" />
        </div>
    {:else if error}
        <div class="alert alert-error">
            {error}
        </div>
    {:else}
        <ContactList {contacts} />
        <Pagination 
            {total}
            {pageSize}
            current={currentPage}
            on:change={handlePageChange}
        />
    {/if}
</div>
```

### Svelte Store for State Management (TypeScript)

```typescript
// frontend/src/lib/stores/contacts.ts
import { writable, derived } from 'svelte/store';
import { contactsApi, type Contact } from '$lib/api/contacts';

interface ContactsState {
    items: Contact[];
    loading: boolean;
    error: string | null;
    selectedId: string | null;
}

function createContactsStore() {
    const { subscribe, set, update } = writable<ContactsState>({
        items: [],
        loading: false,
        error: null,
        selectedId: null,
    });
    
    return {
        subscribe,
        
        async load() {
            update(state => ({ ...state, loading: true, error: null }));
            
            try {
                const response = await contactsApi.list();
                update(state => ({
                    ...state,
                    items: response.items,
                    loading: false,
                }));
            } catch (error) {
                update(state => ({
                    ...state,
                    error: error instanceof Error ? error.message : 'Unknown error',
                    loading: false,
                }));
            }
        },
        
        async create(data: any) {
            const contact = await contactsApi.create(data);
            update(state => ({
                ...state,
                items: [...state.items, contact],
            }));
            return contact;
        },
        
        select(id: string | null) {
            update(state => ({ ...state, selectedId: id }));
        },
    };
}

export const contacts = createContactsStore();

// Derived store for selected contact
export const selectedContact = derived(
    contacts,
    $contacts => $contacts.items.find(c => c.id === $contacts.selectedId)
);
```

## Database Design

### Module-Owned Tables
Each backend module owns its tables with clear prefixes:

```sql
-- Contacts module tables
CREATE TABLE contacts_contact (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(255),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE contacts_tag (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE contacts_contact_tag (
    contact_id UUID REFERENCES contacts_contact(id) ON DELETE CASCADE,
    tag_id UUID REFERENCES contacts_tag(id) ON DELETE CASCADE,
    PRIMARY KEY (contact_id, tag_id)
);

-- Campaigns module tables
CREATE TABLE campaigns_campaign (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    message_template TEXT NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE campaigns_recipient (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES campaigns_campaign(id) ON DELETE CASCADE,
    contact_id UUID NOT NULL,  -- Reference to contacts module, no FK
    status VARCHAR(20) NOT NULL,
    sent_at TIMESTAMP,
    responded_at TIMESTAMP
);

-- Notice: No foreign key from campaigns to contacts table
-- This maintains module independence
```

## Real-time Communication

### WebSocket Integration (Backend - Python)

```python
# backend/app/core/websocket.py
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        if client_id not in self.active_connections:
            self.active_connections[client_id] = set()
        self.active_connections[client_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, client_id: str):
        if client_id in self.active_connections:
            self.active_connections[client_id].discard(websocket)
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]
    
    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            for connection in self.active_connections[client_id]:
                await connection.send_json(message)
    
    async def broadcast(self, message: dict):
        for connections in self.active_connections.values():
            for connection in connections:
                await connection.send_json(message)

manager = ConnectionManager()

# backend/app/modules/campaigns/api.py
@router.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    client_id: str,
    current_user = Depends(get_current_user_ws)
):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id)
```

### WebSocket Client (Frontend - TypeScript)

```typescript
// frontend/src/lib/websocket.ts
import { writable } from 'svelte/store';

export interface WebSocketMessage {
    type: string;
    payload: any;
}

class WebSocketClient {
    private ws: WebSocket | null = null;
    private reconnectInterval = 5000;
    private shouldReconnect = true;
    public messages = writable<WebSocketMessage[]>([]);
    public connected = writable(false);
    
    connect(clientId: string) {
        const token = localStorage.getItem('token');
        const wsUrl = `ws://localhost:8000/api/v1/campaigns/ws/${clientId}?token=${token}`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.connected.set(true);
        };
        
        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.messages.update(msgs => [...msgs, message]);
            
            // Handle specific message types
            this.handleMessage(message);
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.connected.set(false);
            
            if (this.shouldReconnect) {
                setTimeout(() => this.connect(clientId), this.reconnectInterval);
            }
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }
    
    private handleMessage(message: WebSocketMessage) {
        switch (message.type) {
            case 'campaign.progress':
                // Update campaign progress in UI
                break;
            case 'message.received':
                // Show new message notification
                break;
            case 'contact.updated':
                // Refresh contact data
                break;
        }
    }
    
    send(message: WebSocketMessage) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        }
    }
    
    disconnect() {
        this.shouldReconnect = false;
        if (this.ws) {
            this.ws.close();
        }
    }
}

export const wsClient = new WebSocketClient();
```

## Testing Strategy

### Backend Testing (Python)

```python
# backend/app/modules/contacts/tests/test_api.py
import pytest
from httpx import AsyncClient
from uuid import uuid4

@pytest.mark.asyncio
async def test_create_contact(client: AsyncClient, auth_headers):
    """Test contact creation through API"""
    response = await client.post(
        "/api/v1/contacts",
        json={
            "phone": "+1234567890",
            "firstName": "John",
            "lastName": "Doe",
            "email": "john@example.com"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["phone"] == "+1234567890"
    assert data["firstName"] == "John"
    assert "id" in data

@pytest.mark.asyncio
async def test_get_contact(client: AsyncClient, auth_headers, contact_factory):
    """Test retrieving a contact"""
    contact = await contact_factory()
    
    response = await client.get(
        f"/api/v1/contacts/{contact.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(contact.id)
```

### Frontend Testing (TypeScript)

```typescript
// frontend/src/lib/api/contacts.test.ts
import { describe, it, expect, vi } from 'vitest';
import { contactsApi } from './contacts';

describe('Contacts API', () => {
    it('should create a contact', async () => {
        const mockFetch = vi.fn().mockResolvedValue({
            ok: true,
            json: async () => ({
                id: '123',
                phone: '+1234567890',
                firstName: 'John',
            }),
        });
        
        global.fetch = mockFetch;
        
        const contact = await contactsApi.create({
            phone: '+1234567890',
            firstName: 'John',
        });
        
        expect(contact.id).toBe('123');
        expect(mockFetch).toHaveBeenCalledWith(
            expect.stringContaining('/contacts'),
            expect.objectContaining({
                method: 'POST',
                body: JSON.stringify({
                    phone: '+1234567890',
                    firstName: 'John',
                }),
            })
        );
    });
});
```

## Deployment Architecture

### Docker Compose for Development

```yaml
# docker-compose.yml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: attackacrack
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: secret
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  # Redis for Celery
  redis:
    image: redis:7
    ports:
      - "6379:6379"

  # FastAPI Backend
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://admin:secret@postgres:5432/attackacrack
      REDIS_URL: redis://redis:6379
    depends_on:
      - postgres
      - redis
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --reload --host 0.0.0.0

  # Celery Worker
  celery:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql://admin:secret@postgres:5432/attackacrack
      REDIS_URL: redis://redis:6379
    depends_on:
      - postgres
      - redis
    volumes:
      - ./backend:/app
    command: celery -A app.tasks worker --loglevel=info

  # SvelteKit Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      VITE_API_URL: http://localhost:8000/api/v1
    volumes:
      - ./frontend:/app
      - /app/node_modules
    command: npm run dev

volumes:
  postgres_data:
```

### Production Deployment

```yaml
# Production architecture uses separate deployments
Backend API:
  - DigitalOcean App Platform (FastAPI)
  - Auto-scaling based on load
  - PostgreSQL managed database
  - Redis managed instance

Frontend:
  - Vercel/Netlify (SvelteKit)
  - Edge deployment for low latency
  - Static assets on CDN
  - Server-side rendering at edge

Benefits:
  - Independent scaling of frontend/backend
  - Frontend can be updated without API downtime
  - CDN distribution for global performance
  - Separate deployment pipelines
```

## Migration Path from v1

### Parallel Development Strategy
1. Build v2 alongside v1 (no migration needed)
2. Start with new customers on v2
3. Gradually move existing customers
4. Use external systems (OpenPhone, QuickBooks) as source of truth

### API Compatibility Layer (if needed)
```python
# backend/app/legacy/compatibility.py
from fastapi import APIRouter

router = APIRouter(prefix="/legacy/api")

@router.get("/contacts")
async def legacy_contacts_endpoint():
    """Compatibility endpoint for v1 clients"""
    # Transform to v1 format if needed
    pass
```

## Performance Considerations

### Backend Optimizations
- **Async Everywhere**: FastAPI's native async for all I/O
- **Connection Pooling**: SQLAlchemy async with proper pool settings
- **Query Optimization**: Eager loading, proper indexes
- **Caching**: Redis for frequently accessed data

### Frontend Optimizations
- **Code Splitting**: Automatic with SvelteKit routes
- **Lazy Loading**: Components loaded on demand
- **Image Optimization**: Next-gen formats, responsive images
- **Bundle Size**: 50-70% smaller than React equivalents

## Security Architecture

### API Security (Backend)
```python
# backend/app/core/security.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
```

### Frontend Security
```typescript
// frontend/src/hooks.server.ts
import type { Handle } from '@sveltejs/kit';

export const handle: Handle = async ({ event, resolve }) => {
    // Check authentication for protected routes
    if (event.url.pathname.startsWith('/app')) {
        const token = event.cookies.get('token');
        
        if (!token) {
            return Response.redirect('/login');
        }
        
        // Verify token with backend
        try {
            const user = await verifyToken(token);
            event.locals.user = user;
        } catch {
            return Response.redirect('/login');
        }
    }
    
    return resolve(event);
};
```

## Success Metrics

### Architecture Health
- **Module Coupling**: < 3 dependencies per backend module
- **API Response Time**: < 100ms p95
- **Frontend Bundle Size**: < 200KB gzipped
- **Test Coverage**: > 90% for both frontend and backend

### Development Velocity
- **Feature Development**: 50% faster than v1
- **Independent Deployments**: Frontend and backend deployed separately
- **Onboarding Time**: New developer productive in 1 week

## Conclusion

This split architecture gives us:
1. **Backend Simplicity**: Modular monolith with clear boundaries
2. **Frontend Flexibility**: Modern SvelteKit with optimal performance
3. **Independent Evolution**: Frontend and backend can evolve separately
4. **Clear API Contract**: Well-defined interface between frontend and backend
5. **Scalability Path**: Can scale frontend and backend independently

The key insight: The modular monolith architecture applies to the **backend** (FastAPI), providing simplicity and clear boundaries, while the **frontend** (SvelteKit) remains a separate, modern client application consuming the API.

---

*Architecture Version: 2.0*
*Updated: December 2024*
*Status: Corrected for FastAPI Backend + SvelteKit Frontend*