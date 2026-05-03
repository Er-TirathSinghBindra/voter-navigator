"use client";

import { useState, FormEvent } from "react";

interface ChatInputProps {
  onSendMessage: (content: string) => void;
  disabled?: boolean;
}

/**
 * Input form for sending new messages in the chat.
 * 
 * @param {ChatInputProps} props - The component props.
 */
export default function ChatInput({ onSendMessage, disabled = false }: ChatInputProps) {
  const [inputVal, setInputVal] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!inputVal.trim() || disabled) return;
    
    onSendMessage(inputVal.trim());
    setInputVal("");
  };

  return (
    <form 
      className="chat-input-form" 
      onSubmit={handleSubmit} 
      aria-label="Message submission form"
    >
      <label htmlFor="chat-input" className="visually-hidden">
        Type your message here
      </label>
      <input
        id="chat-input"
        type="text"
        className="chat-input-field"
        value={inputVal}
        onChange={(e) => setInputVal(e.target.value)}
        placeholder="Ask about polling locations, deadlines, or civic terms..."
        aria-required="true"
        autoComplete="off"
        disabled={disabled}
      />
      <button 
        type="submit" 
        className="send-button"
        aria-label="Send message"
        disabled={disabled || !inputVal.trim()}
      >
        Send
      </button>
    </form>
  );
}
