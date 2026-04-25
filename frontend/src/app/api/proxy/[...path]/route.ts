import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth/next";
import { authOptions } from "@/lib/auth";

// Environment variable for the Python Backend URL
const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function POST(
  req: NextRequest,
  { params }: { params: { path: string[] } }
) {
  // Check auth
  const session = await getServerSession(authOptions);
  
  if (!session) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    const pathName = params.path.join("/");
    const body = await req.json();

    // Include the backend URL and the specific path requested
    const targetUrl = `${BACKEND_URL}/api/${pathName}`;

    // Here we can securely attach the Google OAuth access token and user info
    // without ever sending the token back to the React client
    const backendReqHeaders = new Headers({
      'Content-Type': 'application/json',
      // @ts-ignore
      'Authorization': `Bearer ${session.accessToken || ''}`,
      'X-User-Email': session.user?.email || '' // Identity info
    });

    const response = await fetch(targetUrl, {
      method: "POST",
      headers: backendReqHeaders,
      body: JSON.stringify(body)
    });

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });

  } catch (error: any) {
    console.error("BFF Proxy Error:", error);
    return NextResponse.json(
      { error: "Internal Server Error or Backend Unreachable" },
      { status: 500 }
    );
  }
}
