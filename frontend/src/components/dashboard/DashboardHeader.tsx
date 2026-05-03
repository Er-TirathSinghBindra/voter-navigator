"use client";

import { signOut, Session } from "next-auth/react";

interface DashboardHeaderProps {
  session: Session;
}

/**
 * Header component for the dashboard.
 * Displays the application title and user controls (email badge and sign-out button).
 * 
 * @param {DashboardHeaderProps} props - The component props containing the session data.
 */
export default function DashboardHeader({ session }: DashboardHeaderProps) {
  return (
    <header className="dashboard-header" role="banner">
      <h2>The Civic Navigator</h2>
      <div className="user-controls">
        <span 
          className="user-email-badge" 
          aria-label={`Signed in as ${session.user?.email}`}
        >
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
  );
}
