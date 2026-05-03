"use client";

import { ChatMessage } from "@/types/chat";

interface ChatHistoryProps {
  messages: ChatMessage[];
}

/**
 * Renders the sequence of messages in the chat session.
 * 
 * @param {ChatHistoryProps} props - The component props containing the list of messages.
 */
export default function ChatHistory({ messages }: ChatHistoryProps) {
  return (
    <section 
      className="chat-history" 
      aria-live="polite" 
      aria-atomic="false" 
      aria-label="Chat messages history"
    >
      {messages.map((m, idx) => (
        <article 
          key={idx} 
          className={`chat-bubble ${m.role === 'user' ? 'bubble-user' : 'bubble-assistant'}`}
          aria-label={`Message from ${m.role}`}
        >
          <p>{m.content}</p>
        </article>
      ))}
    </section>
  );
}
