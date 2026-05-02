"use client";

import { useSession, signIn, signOut } from "next-auth/react";
import { useState } from "react";

export default function Dashboard() {
  const { data: session, status } = useSession();
  const [messages, setMessages] = useState<{role: 'user'|'assistant', content: string}[]>([
    { role: 'assistant', content: "Hello! I'm The Civic Navigator. How can I help you prepare for the upcoming election?" }
  ]);
  const [inputVal, setInputVal] = useState("");

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputVal.trim()) return;
    
    const userMessage = { role: 'user' as const, content: inputVal };
    setMessages(prev => [...prev, userMessage]);
    setInputVal("");

    // Add a placeholder assistant response
    const assistantPlaceholder = { role: 'assistant' as const, content: "..." };
    setMessages(prev => [...prev, assistantPlaceholder]);

    try {
      const response = await fetch("/api/proxy/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          messages: [...messages, userMessage] 
        })
      });

      const data = await response.json();

      if (data.error) {
        setMessages(prev => {
          const updated = [...prev];
          updated[updated.length - 1] = { 
            role: 'assistant', 
            content: `Error: ${data.error}` 
          };
          return updated;
        });
      } else {
        setMessages(prev => {
          const updated = [...prev];
          updated[updated.length - 1] = { 
            role: 'assistant', 
            content: data.content 
          };
          return updated;
        });
      }
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
    }
  };

  if (status === "loading") {
    return (
      <div className="layout-container center-content">
        <p aria-live="polite">Loading session data...</p>
      </div>
    );
  }

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
      <header className="dashboard-header" role="banner">
        <h2>The Civic Navigator</h2>
        <div className="user-controls">
          <span className="user-email-badge" aria-label={`Signed in as ${session.user?.email}`}>
            {session.user?.email}
          </span>
          <button 
            className="secondary-button" 
            onClick={() => signOut({ callbackUrl: '/' })}
            aria-label="Sign out from your account"
          >
            Sign out
          </button>
        </div>
      </header>

      <main className="chat-container-main" role="main" aria-label="Conversational UI">
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

        <form 
          className="chat-input-form" 
          onSubmit={handleSend} 
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
          />
          <button 
            type="submit" 
            className="send-button"
            aria-label="Send message"
            disabled={!inputVal.trim()}
          >
            Send
          </button>
        </form>
      </main>
    </div>
  );
}
