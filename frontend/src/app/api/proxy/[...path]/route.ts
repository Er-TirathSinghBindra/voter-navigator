import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth/next";
import { authOptions } from "@/lib/auth";

// Environment variable for the Python Backend URL
const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

/**
 * Backend-for-Frontend (BFF) Proxy Route.
 * Securely forwards requests from the React client to the Python backend.
 * Automatically attaches the Google OAuth access token and identity headers.
 */
export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  // 1. Authenticate the user session via NextAuth
  const session = await getServerSession(authOptions);
  
  if (!session) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    const { path } = await params;
    const pathName = path.join("/");
    const body = await req.json();

    // 2. Construct the target URL for the microservice
    const targetUrl = `${BACKEND_URL}/api/${pathName}`;

    // 3. Prepare secure headers
    // We attach the access token here, keeping it hidden from the browser client.
    const backendReqHeaders = new Headers({
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${session.accessToken || ''}`,
      'X-User-Email': session.user?.email || ''
    });

    // 4. Forward the request
    const response = await fetch(targetUrl, {
      method: "POST",
      headers: backendReqHeaders,
      body: JSON.stringify(body)
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return NextResponse.json(
        { error: errorData.detail || "Backend Service Error" }, 
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data, { status: 200 });

  } catch (error: unknown) {
    console.error("BFF Proxy Exception:", error);
    return NextResponse.json(
      { error: "Internal Server Error: Backend unreachable or malformed request." },
      { status: 500 }
    );
  }
}
