import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
};

// Startup Secret Validation
const requiredSecrets = ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "NEXTAUTH_SECRET"];
const missingSecrets = requiredSecrets.filter((secret) => !process.env[secret]);

if (missingSecrets.length > 0) {
  console.error(`\n❌ CRITICAL STARTUP ERROR: Missing required secrets: ${missingSecrets.join(", ")}`);
  console.error("Ensure these are injected via GCP Secret Manager or .env.local file.\n");
  process.exit(1);
}

console.log("✅ Startup validation passed. All required Next.js secrets are present.");

export default nextConfig;
