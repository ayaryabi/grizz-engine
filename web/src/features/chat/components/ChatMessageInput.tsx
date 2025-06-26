"use client";

import React, { useRef, useEffect, useState } from 'react';
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { ArrowUp, Paperclip, X, FileIcon } from "lucide-react";
import { useMessageComposer } from '@/features/chat/hooks/useMessageComposer';

import { FileAttachment } from '@/lib/types';

interface ChatMessageInputProps {
  onSendMessage: (messageText: string, files?: FileAttachment[]) => void;
  isLoading?: boolean;
  disabled?: boolean;
}

interface FilePreview {
  file: File;
  id: string;
  preview?: string;
}

export default function ChatMessageInput({ onSendMessage, isLoading = false, disabled = false }: ChatMessageInputProps) {
  // Business logic handled by the composer hook
  const {
    inputText,
    setInputText,
    selectedFiles,
    addFiles,
    removeFile,
    handleSend,
  } = useMessageComposer(onSendMessage);

  const [isDragging, setIsDragging] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dragCounter = useRef(0);

  const handleInputChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputText(event.target.value);
  };

  const adjustTextareaHeight = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'; // Reset height first
      const scrollHeight = textareaRef.current.scrollHeight;
      // A common min-height for the textarea itself (e.g. one line)
      // The overall component height will be larger due to padding in the wrapper
      const minTextareaHeight = 24; // Approx 1.5rem or line-height
      const maxHeight = 120; // Max height for textarea content before scrolling
      textareaRef.current.style.height = `${Math.max(minTextareaHeight, Math.min(scrollHeight, maxHeight))}px`;
    }
  };

  useEffect(() => {
    adjustTextareaHeight();
  }, [inputText]);

  const handleFileSelect = (files: FileList) => {
    addFiles(files);
  };

  const handleFileInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      handleFileSelect(files);
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  // Drag and drop handlers
  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter.current++;
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      setIsDragging(true);
    }
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter.current--;
    if (dragCounter.current === 0) {
      setIsDragging(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    dragCounter.current = 0;

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelect(e.dataTransfer.files);
    }
  };

  return (
    <div 
      className={`p-3 sm:p-4 bg-background transition-colors ${isDragging ? 'bg-muted/50' : ''}`}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
    >
      {/* Drag overlay */}
      {isDragging && (
        <div className="absolute inset-0 bg-primary/10 border-2 border-dashed border-primary rounded-lg flex items-center justify-center z-10">
          <div className="text-center">
            <Paperclip className="w-8 h-8 mx-auto mb-2 text-primary" />
            <p className="text-sm text-primary font-medium">Drop files here</p>
          </div>
        </div>
      )}

      {/* File previews */}
      {selectedFiles.length > 0 && (
        <div className="mb-3 space-y-2">
          <p className="text-xs text-muted-foreground font-medium">Files to upload ({selectedFiles.length}):</p>
          <div className="flex flex-wrap gap-2">
            {selectedFiles.map((filePreview: FilePreview) => (
              <div key={filePreview.id} className="flex items-center gap-2 bg-muted px-3 py-2 rounded-lg border">
                {filePreview.preview ? (
                  <img 
                    src={filePreview.preview} 
                    alt={filePreview.file.name}
                    className="w-6 h-6 object-cover rounded"
                  />
                ) : (
                  <FileIcon className="w-4 h-4" />
                )}
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium truncate">{filePreview.file.name}</p>
                  <p className="text-xs text-muted-foreground">{Math.round(filePreview.file.size / 1024)}KB</p>
                </div>
                <button 
                  onClick={() => removeFile(filePreview.id)}
                  className="text-muted-foreground hover:text-destructive transition-colors"
                  type="button"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
      
      <div className="flex items-end w-full p-1 rounded-xl border border-input bg-muted focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2 focus-within:ring-offset-background transition-shadow duration-200 shadow-sm min-h-[56px]">
        <Textarea
          ref={textareaRef}
          value={inputText}
          onChange={handleInputChange}
          onKeyPress={handleKeyPress}
          onInput={adjustTextareaHeight}
          className="appearance-none flex-1 resize-none overflow-y-hidden bg-transparent dark:bg-transparent text-sm
                     border-none focus:ring-0 focus:outline-none focus-visible:ring-0 
                     py-2.5 px-3 min-h-[24px] max-h-[120px] placeholder:text-muted-foreground/80"
          rows={1}
                  disabled={isLoading || disabled}
        placeholder={isLoading ? "Waiting for response..." : "Type your message..."}
        />
        
        {/* File upload button */}
        <Button 
          variant="ghost"
          size="icon" 
          className="shrink-0 w-9 h-9 sm:w-10 sm:h-10 mr-1 mb-0.5 self-end"
          onClick={() => fileInputRef.current?.click()}
          disabled={isLoading || disabled}
          aria-label="Upload file"
        >
          <Paperclip className="w-4 h-4 sm:w-5 sm:h-5" />
        </Button>
        
        {/* Send button */}
        <Button 
          variant="default"
          size="icon" 
          className="shrink-0 rounded-full w-9 h-9 sm:w-10 sm:h-10 mr-1 mb-0.5 self-end"
          onClick={handleSend}
          disabled={(!inputText.trim() && selectedFiles.length === 0) || isLoading || disabled}
          aria-label="Send message"
        >
          <ArrowUp className="w-4 h-4 sm:w-5 sm:h-5" />
        </Button>
      </div>
      
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept="image/*,application/pdf,text/plain,text/markdown,audio/*,video/*"
        onChange={handleFileInputChange}
        className="hidden"
      />
    </div>
  );
} 