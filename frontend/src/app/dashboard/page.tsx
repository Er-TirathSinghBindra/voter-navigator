"use client";

import { useSession, signIn } from "next-auth/react";
import { useState } from "react";
import { ChatMessage, ChatResponse, ChatErrorResponse } from "@/types/chat";
import DashboardHeader from "@/components/dashboard/DashboardHeader";
import ChatHistory from "@/components/dashboard/ChatHistory";
import ChatInput from "@/components/dashboard/ChatInput";

/**
 * Main Dashboard Page component.
 * Handles the high-level state management for the chat interface,
 * session validation, and API communication with the BFF proxy.
 */
export default function Dashboard() {
  const { data: session, status } = useSession();
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: 'assistant', content: "Hello! I'm The Civic Navigator. How can I help you prepare for the upcoming election?" }
  ]);
  const [isProcessing, setIsProcessing] = useState(false);

  /**
   * Sends a message to the backend and updates the chat history.
   * 
   * @param {string} content - The user's message content.
   */
  const handleSendMessage = async (content: string) => {
    if (!content.trim()) return;
    
    const userMessage: ChatMessage = { role: 'user', content };
    const assistantPlaceholder: ChatMessage = { role: 'assistant', content: "..." };
    
    setMessages(prev => [...prev, userMessage, assistantPlaceholder]);
    setIsProcessing(true);

    try {
      const response = await fetch("/api/proxy/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          messages: [...messages, userMessage] 
        })
      });

      const data: ChatResponse | ChatErrorResponse = await response.json();

      setMessages(prev => {
        const updated = [...prev];
        const lastIndex = updated.length - 1;
        
        if ('error' in data) {
          updated[lastIndex] = { role: 'assistant', content: `Error: ${data.error}` };
        } else {
          updated[lastIndex] = { role: 'assistant', content: (data as ChatResponse).content };
        }
        return updated;
      });
    } catch (err) {
      console.error("Chat error:", err);
      setMessages(prev => {
        const updated = [...prev];
        updated[updated.length - 1] = { 
          role: 'assistant', 
          content: "Sorry, I encountered an error connecting to the service. Please try again." 
        };
        return updated;
      });
    } finally {
      setIsProcessing(false);
    }
  };

  // Loading state
  if (status === "loading") {
    return (
      <div className="layout-container center-content">
        <p aria-live="polite">Loading session data...</p>
      </div>
    );
  }

  // Authentication Required state
  if (!session) {
    return (
      <div className="layout-container center-content">
        <div className="auth-card">
          <h1>Authentication Required</h1>
          <p>Please sign in to access your personalized election assistant.</p>
          <button 
            className="primary-button" 
            onClick={() => signIn("google")}
            aria-label="Sign in with Google to access the dashboard"
          >
            Sign in with Google
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-layout">
      <DashboardHeader session={session} />

      <main className="chat-container-main" role="main" aria-label="Conversational UI">
        <ChatHistory messages={messages} />
        <ChatInput onSendMessage={handleSendMessage} disabled={isProcessing} />
      </main>
    </div>
  );
}
