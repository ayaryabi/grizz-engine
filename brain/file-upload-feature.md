# File Upload Feature Implementation Plan

## 🎯 **High-Level Overview**

Add file upload capability to Grizz AI chat system. Users upload files → Files go to Supabase Storage → URLs sent to Redis → LLM processes files → AI responds with file analysis.

**Simple Goal**: Let users upload images/documents in chat and have the AI analyze them.

---

## 🗂️ **STEP 0: Create Supabase Buckets (MUST DO FIRST)**

Before implementing file uploads, you need to create the storage buckets in Supabase.

### **Create the chat-files bucket**

```javascript
// Run this in your Supabase project (SQL Editor or via client)
const { data, error } = await supabase.storage.createBucket('chat-files', {
  public: false,                    // Private bucket (requires JWT)
  allowedMimeTypes: [
    'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp',
    'application/pdf', 
    'text/plain', 'text/markdown',
    'audio/mpeg', 'audio/wav', 'audio/mp4',
    'video/mp4', 'video/quicktime'
  ],
  fileSizeLimit: '50MB'            // 50MB max file size
});

if (error) {
  console.error('Error creating bucket:', error);
} else {
  console.log('Bucket created successfully:', data);
}
```

### **Alternative: Via Supabase Dashboard**

1. Go to **Storage** in your Supabase dashboard
2. Click **"New bucket"**
3. Name: `chat-files`
4. **Make it private** (uncheck "Public bucket")
5. Set file size limit: `50MB`
6. Add allowed MIME types in restrictions

### **Set up Row Level Security (RLS) Policies**

```sql
-- Enable RLS on storage.objects table (if not already enabled)
ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access their own files
CREATE POLICY "Users can manage their own files" ON storage.objects
  FOR ALL USING (
    bucket_id = 'chat-files' AND 
    (storage.foldername(name))[1] = auth.uid()::text
  )
  WITH CHECK (
    bucket_id = 'chat-files' AND 
    (storage.foldername(name))[1] = auth.uid()::text
  );
```

**File path structure will be**: `chat-files/{user_id}/filename.ext`

---

## 🛠️ **What We Need to Build**

### **Current Architecture (Works):**
```
User types → WebSocket + JWT → Redis Queue → LLM Worker → Response
```

### **Enhanced Architecture (What We're Adding):**
```
User uploads files → Supabase Storage → URLs → WebSocket + JWT → 
Redis Queue (with file URLs) → LLM Worker (analyzes files) → Response
```

---

## 📋 **Implementation Steps**

### **Step 1: Frontend File Upload (web folder)**
```typescript
// Add to: web/src/components/chat/MessageInput.tsx
- File upload button + drag & drop
- Upload files to Supabase → get URLs
- Send {text, file_urls} via WebSocket

// New file: web/src/lib/storage.ts  
export async function uploadToSupabase(file: File, userId: string): Promise<string>
```

### **Step 2: Backend Message Parsing (ai-engine folder)**
```python
# Modify: ai-engine/app/api/ws.py
# Change from: user_message = await websocket.receive_text()
# To: Parse JSON with file_urls

message_data = await websocket.receive_text()
if message_data.startswith('{'):
    parsed = json.loads(message_data)
    user_message = parsed.get('text', '')
    file_urls = parsed.get('file_urls', [])
```

### **Step 3: Redis Queue Enhancement**
```python
# Modify: ai-engine/app/services/queue_service.py
# Add file_urls parameter to queue_chat_message()

async def queue_chat_message(
    user_id: str,
    conversation_id: str, 
    message: str,
    client_id: str,
    file_urls: List[str] = None  # NEW
):
```

### **Step 4: LLM Worker File Processing**
```python
# Modify: ai-engine/app/agents/chat_agent.py
# Add file processing to build_prompt()

def build_prompt(context_messages, user_message, file_urls=None):
    # If image URLs → add to OpenAI vision prompt
    # If document URLs → extract text and include in prompt
```

---

## 🗂️ **Supabase Storage Setup**

### **Simple Bucket Structure:**
```
chat-files/           # Private bucket for all uploaded files
├── user_123/
│   ├── image1.jpg
│   ├── document.pdf
│   └── audio.mp3
├── user_456/
│   └── ...
```

### **Bucket Configuration:**
- **Private bucket** with Row Level Security (RLS)
- **JWT authentication** required
- **File size limits**: 50MB max
- **Allowed types**: images, PDFs, audio, text files

---

## 🔐 **Security (Already Handled)**

- ✅ **JWT Auth**: Your existing auth system works unchanged
- ✅ **RLS Policies**: Users can only access their own files  
- ✅ **Private Buckets**: Files are not publicly accessible
- ✅ **File Validation**: Frontend validates file types/sizes

---

## ⚡ **Performance & Integration**

### **Why This Works Well:**
- **No Redis changes**: Your current queue system handles file URLs perfectly
- **No auth changes**: JWT tokens work for both chat and file storage
- **URLs vs Base64**: 33% faster than encoding files directly
- **Supabase CDN**: Fast global file delivery

### **File Processing:**
- **Images**: OpenAI Vision API analyzes directly from URLs
- **PDFs**: Extract text → include in prompt
- **Audio**: Transcribe → include in prompt

---

## 🚀 **Implementation Timeline**

### **Phase 0: Setup (30 minutes):**
1. **Create Supabase bucket** (10 mins)
2. **Set up RLS policies** (20 mins)

### **Phase 1 (MVP - 4-6 hours total):**
1. **Frontend file upload UI** (2-3 hours)
2. **Backend message parsing** (1 hour)  
3. **Redis queue enhancement** (30 mins)
4. **LLM worker file processing** (1-2 hours)

### **Testing:**
- Upload image → AI describes it
- Upload PDF → AI summarizes it
- Upload with text → AI responds using both

---

## ✅ **Success Criteria**

When done, users should be able to:
1. **Upload files** in chat interface
2. **See upload progress** and previews
3. **Get AI analysis** of their files
4. **Chat normally** while files are attached

**That's it!** Simple file upload + AI analysis integrated with your existing Redis architecture.

---

## 📁 **Key Files to Modify**

### Frontend:
- `web/src/components/chat/MessageInput.tsx` - Add upload button
- `web/src/lib/storage.ts` - New Supabase upload function
- `web/src/hooks/useWebSocket.ts` - Send files with messages

### Backend:  
- `ai-engine/app/api/ws.py` - Parse file URLs from messages
- `ai-engine/app/services/queue_service.py` - Add file_urls to queue
- `ai-engine/app/agents/chat_agent.py` - Process files in prompts

**No changes needed to**: Redis setup, auth system, database, or core architecture. 