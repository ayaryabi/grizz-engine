# Grizz Engine - Phase 1: Database & Authentication

This document outlines the specific steps for implementing the foundation of Grizz Engine: the database structure and authentication system.

## 1. Database Setup

### 1.1 Schema Implementation

1. **Set up Supabase project**
   - Create new Supabase project
   - Configure database settings (region, pricing plan)
   - Enable required extensions (particularly `pgvector`)

2. **Create tables with SQL migrations**
   ```sql
   -- Enable the pgvector extension
   CREATE EXTENSION IF NOT EXISTS vector;

   -- Users/profiles tables
   -- (Note: users table is created automatically by Supabase Auth)
   CREATE TABLE profiles (
     user_id UUID PRIMARY KEY REFERENCES auth.users(id),
     display_name TEXT,
     avatar_url TEXT,
     plan_tier TEXT DEFAULT 'free',
     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );

   -- Bytes table
   CREATE TABLE bytes (
     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
     user_id UUID NOT NULL REFERENCES auth.users(id),
     parent_id UUID REFERENCES bytes(id),
     item_type TEXT NOT NULL CHECK (item_type IN ('note', 'document', 'recipe', 'paystub')),
     title TEXT NOT NULL,
     content TEXT NOT NULL,
     properties JSONB DEFAULT '{}',
     embedding VECTOR(1536),
     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );

   -- Entities table
   CREATE TABLE entities (
     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
     user_id UUID REFERENCES auth.users(id),
     entity_type TEXT NOT NULL CHECK (entity_type IN ('person', 'organization', 'project', 'event', 'location', 'thing', 'topic', 'process', 'time_period')),
     name TEXT NOT NULL,
     properties JSONB DEFAULT '{}',
     embedding VECTOR(1536),
     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
     UNIQUE(entity_type, name)
   );

   -- Byte-entity links
   CREATE TABLE byte_entity_links (
     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
     byte_id UUID NOT NULL REFERENCES bytes(id) ON DELETE CASCADE,
     entity_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
     relationship_type TEXT DEFAULT 'about',
     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );

   -- Byte-to-byte links
   CREATE TABLE byte_links (
     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
     source_byte_id UUID NOT NULL REFERENCES bytes(id) ON DELETE CASCADE,
     target_byte_id UUID NOT NULL REFERENCES bytes(id) ON DELETE CASCADE,
     link_type TEXT NOT NULL DEFAULT 'inline_reference',
     position INTEGER,
     properties JSONB DEFAULT '{}',
     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );

   -- Entity-entity links
   CREATE TABLE entity_entity_links (
     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
     source_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
     target_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
     rel_type TEXT NOT NULL,
     props JSONB DEFAULT '{}',
     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
     PRIMARY KEY(source_id, target_id, rel_type)
   );

   -- Conversations
   CREATE TABLE conversations (
     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
     user_id UUID NOT NULL REFERENCES auth.users(id),
     context_byte_id UUID REFERENCES bytes(id),
     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );

   -- Messages
   CREATE TABLE messages (
     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
     conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
     role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'tool')),
     content TEXT NOT NULL,
     tool_name TEXT,
     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );
   ```

3. **Apply Row-Level Security (RLS)**
   ```sql
   -- Bytes table RLS
   ALTER TABLE bytes ENABLE ROW LEVEL SECURITY;
   CREATE POLICY "bytes_owner_rls" ON bytes
     FOR ALL USING (user_id = auth.uid());

   -- Similar policies for other tables: entities, byte_entity_links, etc.
   ALTER TABLE entities ENABLE ROW LEVEL SECURITY;
   CREATE POLICY "entities_owner_rls" ON entities
     FOR ALL USING (user_id = auth.uid() OR user_id IS NULL);
   
   -- Continue for remaining tables
   ```

### 1.2 Indexing

1. **Set up pgvector index**
   ```sql
   -- Create ivfflat index on bytes.embedding
   CREATE INDEX bytes_embedding_idx ON bytes 
     USING ivfflat (embedding vector_ip_ops) WITH (lists = 100);
     
   -- Create composite index on user_id, item_type
   CREATE INDEX bytes_user_item_idx ON bytes(user_id, item_type);
   ```

### 1.3 Test Database Setup

1. Create basic script to insert test data
2. Verify all tables and relationships work correctly
3. Test RLS policies to ensure data isolation

## 2. Authentication Implementation

### 2.1 Clerk Authentication (Frontend)

1. **Set up Clerk project**
   - Create Clerk account and project
   - Configure authentication methods (email/password, magic links, OAuth providers)
   - Set up JWT templates and callback URLs

2. **Integrate Clerk with Next.js**
   - Install Clerk SDK
   ```bash
   npm install @clerk/nextjs
   ```
   
   - Add Clerk provider to `_app.tsx` or layout
   ```tsx
   import { ClerkProvider } from '@clerk/nextjs';
   
   function MyApp({ Component, pageProps }) {
     return (
       <ClerkProvider>
         <Component {...pageProps} />
       </ClerkProvider>
     );
   }
   ```

   - Implement protected routes with `withAuth` HOC or middleware
   - Add sign-in, sign-up, and user profile components

### 2.2 JWT Authentication (Backend)

1. **Set up FastAPI JWT validation**
   - Install required packages
   ```bash
   pip install fastapi python-jose[cryptography] python-multipart
   ```

   - Implement JWT validation middleware
   ```python
   from fastapi import Depends, FastAPI, HTTPException, status
   from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
   from jose import jwt, JWTError
   import requests

   security = HTTPBearer()
   app = FastAPI()

   async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
       try:
           # Verify JWT with Clerk
           # (In production, should verify locally using Clerk's public key)
           token = credentials.credentials
           # Decode and verify the token
           payload = jwt.decode(
               token, 
               options={"verify_signature": False}  # In production, set to True and use proper verification
           )
           user_id = payload.get("sub")
           if user_id is None:
               raise HTTPException(status_code=401, detail="Invalid authentication token")
           return {"user_id": user_id}
       except JWTError:
           raise HTTPException(status_code=401, detail="Invalid authentication token")
   ```

2. **Secure endpoints with auth dependency**
   ```python
   @app.get("/api/bytes")
   async def get_bytes(current_user: dict = Depends(get_current_user)):
       # Access current_user["user_id"] to get the authenticated user's ID
       # Use this ID to filter database queries
       return {"message": f"Fetching bytes for user {current_user['user_id']}"}
   ```

### 2.3 Connect User Signup to Database

1. **Create user profile on signup**
   - Implement webhook or trigger to create profile entry when user signs up
   - Set up Supabase functions or FastAPI endpoint to handle user creation

2. **Test authentication flow**
   - Verify sign-up creates appropriate database records
   - Confirm JWT authentication works with FastAPI endpoints
   - Test RLS to ensure proper data isolation

## 3. Validation & Testing

1. **Database validation script**
   - Create script to verify all tables exist with correct schemas
   - Test inserting and retrieving records with proper relationships

2. **Authentication flow tests**
   - Test signup → database record creation
   - Test login → JWT issuance
   - Test JWT validation in FastAPI
   - Test data access with RLS

## 4. Next Steps After Phase 1

- Implement basic chat UI
- Set up frontend-backend communication
- Begin building core AI Engine tools (ByteCreate, ByteSearch)
