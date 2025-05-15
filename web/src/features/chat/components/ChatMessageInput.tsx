"use client";

import React, { useState, useRef, useEffect } from 'react';
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Mic, Send } from "lucide-react";

interface ChatMessageInputProps {
  onSendMessage: (messageText: string) => void; // Uncommented and defined
  // onStartRecording: () => void; // For voice memo later
  // onStopRecording: () => void; // For voice memo later
  // isRecording: boolean; // For voice memo later
}

export default function ChatMessageInput({ onSendMessage }: ChatMessageInputProps) { // Added onSendMessage to destructuring
  const [inputText, setInputText] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleInputChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputText(event.target.value);
    // Removed adjustTextareaHeight from here to avoid calling it on every keystroke if not needed
    // It will be called via useEffect or after sending a message
  };

  const adjustTextareaHeight = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'; // Reset height
      const scrollHeight = textareaRef.current.scrollHeight;
      const maxHeight = 120; // As defined by max-h-[120px]
      textareaRef.current.style.height = `${Math.min(scrollHeight, maxHeight)}px`;
    }
  };

  useEffect(() => {
    adjustTextareaHeight();
  }, [inputText]);

  const handleSend = () => {
    const trimmedInput = inputText.trim();
    if (trimmedInput) {
      onSendMessage(trimmedInput); // Use the prop
      setInputText("");
      // After sending, explicitly reset height to auto, then let useEffect adjust if needed
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleVoiceMemo = () => {
    console.log("Voice memo clicked");
    // onStartRecording(); // Implement later
  };

  const handleKeyPress = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault(); // Prevent newline in textarea
      handleSend();
    }
  };

  // Removed redundant useEffect for adjustTextareaHeight as it's covered by the one dependent on inputText

  return (
    <div className="flex items-end gap-2 p-2 sm:p-3 border-t border-border bg-background">
      <Button 
        variant="ghost" 
        size="icon" 
        className="p-2 h-10 w-10 shrink-0" 
        onClick={handleVoiceMemo}
        aria-label="Start voice memo"
      >
        <Mic className="h-5 w-5" />
      </Button>
      <Textarea
        ref={textareaRef}
        value={inputText}
        onChange={handleInputChange}
        onKeyPress={handleKeyPress}
        onInput={adjustTextareaHeight} // Added onInput for better responsiveness while typing/pasting
        placeholder="Type your message..."
        className="flex-1 resize-none overflow-y-hidden rounded-lg border border-input p-2.5 text-sm min-h-[40px] max-h-[120px]"
        rows={1} // Start with 1 row, will auto-grow
      />
      <Button 
        variant="default" // Or your primary variant
        size="icon" 
        className="p-2 h-10 w-10 shrink-0" 
        onClick={handleSend}
        disabled={!inputText.trim()}
        aria-label="Send message"
      >
        <Send className="h-5 w-5" />
      </Button>
    </div>
  );
} 