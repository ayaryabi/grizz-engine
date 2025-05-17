"use client";

import React, { useState, useRef, useEffect } from 'react';
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { ArrowUp } from "lucide-react";

interface ChatMessageInputProps {
  onSendMessage: (messageText: string) => void;
  isLoading?: boolean;
  disabled?: boolean;
}

export default function ChatMessageInput({ onSendMessage, isLoading = false, disabled = false }: ChatMessageInputProps) {
  const [inputText, setInputText] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

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

  const handleSend = () => {
    const trimmedInput = inputText.trim();
    if (trimmedInput) {
      onSendMessage(trimmedInput);
      setInputText("");
      if (textareaRef.current) {
        // Reset to auto and let useEffect adjust, or set to a defined initial height
        textareaRef.current.style.height = 'auto'; 
      }
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="p-3 sm:p-4 bg-background">
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
        <Button 
          variant="default"
          size="icon" 
          className="shrink-0 rounded-full w-9 h-9 sm:w-10 sm:h-10 mr-1 mb-0.5 self-end"
          onClick={handleSend}
          disabled={!inputText.trim() || isLoading || disabled}
          aria-label="Send message"
        >
          <ArrowUp className="w-4 h-4 sm:w-5 sm:h-5" />
        </Button>
      </div>
    </div>
  );
} 