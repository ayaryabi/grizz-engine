## 🗓️ Today — Refactor `ChatMessageInput` into a Modular Input System

### 🚩 Why
The current `ChatMessageInput.tsx` (~300 LOC) mixes text-input logic, drag-and-drop, file upload state, previews, and send-message plumbing in one component.  Splitting these concerns will:
• simplify maintenance & tests
• let us reuse the file-upload zone elsewhere (profile pics, bytes, etc.)
• unlock easier UI tweaks (e.g. mobile-only input)

### ✅ Success Criteria
1. Message send UX identical (Enter to send, Shift+Enter newline, optimistic UI).
2. Drag-and-drop + file-button still work and show previews.
3. No regression in WebSocket send logic.
4. Unit tests cover new hooks; Cypress happy-path passes.

### 📂 Target File/Folder Layout (9 files, ~250 LOC total)
```
src/features/chat/components/message-input/
├─ index.tsx                 # Orchestrator: assembles parts & exposes <ChatMessageInput />
├─ context/
│   └─ FileUploadContext.tsx # React context + provider with file state & helpers
├─ hooks/
│   ├─ useFileUpload.ts      # Convenience hook for the context
│   ├─ useAutoHeight.ts      # Shared textarea-auto-grow logic
│   └─ useDragAndDrop.ts     # Handles drag state, returns { isDragging, … }
└─ components/
    ├─ MessageInputBase.tsx  # Textarea only; props: value, onChange, onSend, disabled
    ├─ FileUploadZone.tsx    # Wrapper handling drag events; shows <DragOverlay />
    ├─ FilePreviewList.tsx   # Flex grid of <FilePreview />
    ├─ FilePreview.tsx       # Single preview w/ remove-button
    └─ DragOverlay.tsx       # Dashed border overlay shown while dragging
```

### 🛠️ Implementation Steps
1. **Scaffold directories** (`message-input/`, `components/`, `hooks/`, `context/`).
2. **Create `FileUploadContext`**
   • `files: FilePreview[]`, `isDragging: boolean`
   • helpers: `addFiles(FileList)`, `removeFile(id)`, `clear()`
3. **Hook: `useFileUpload`** → just `return useContext(FileUploadContext)`.
4. **Hook: `useAutoHeight`**
   • takes `value` string, resizes a forwarded `textareaRef` between 24-120 px.
5. **Hook: `useDragAndDrop`**
   • centralises `dragenter / leave / over / drop` logic → emits `setIsDragging`, `addFiles`.
6. **Component: `MessageInputBase`**
   • wraps `<Textarea />`, handles Enter/Shift+Enter, calls `onSend`.
7. **Component: `FileUploadZone`**
   • uses `useDragAndDrop` + renders `{children}`; attaches hidden `<input type=file />` on click of 📎 icon.
8. **Component: `FilePreview[List]`**
   • shows image thumb or generic icon; 32×32 and filename; x-button to remove.
9. **Component: `DragOverlay`**
   • translucent primary/10 background + dashed border.
10. **`index.tsx` Orchestrator**
    • local state: `text`.
    • pulls `{files, clear}` from context.
    • `handleSend` → `onSendMessage(text, files)` (prop) then `clear()` & `setText("")`.
    • layout: `FileUploadZone` → stack `MessageInputBase` + `FilePreviewList`.
11. **Replace Old Import**
    • Update `ChatView.tsx` (or wherever) to import the new path.
12. **Delete legacy file** `ChatMessageInput.tsx` once tests pass.
13. **Unit tests**
    • `useFileUpload` adds/removes files, cleans ObjectURLs.
    • `MessageInputBase` sends on Enter.
14. **Cypress smoke**: send text, attach jpg, drag png → previews show, message arrives.

### 🧹 Post-refactor Cleanup
• Run `eslint --fix` & `pnpm test`.
• Update storybook snapshot (if any).
• Docs: add short snippet in `README.md` about reusing `FileUploadZone`.

---
_Assignee: Frontend agent • Est. effort: 2-3 hrs (coding) + 30 min testing._
