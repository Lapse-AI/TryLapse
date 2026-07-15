#!/usr/bin/env node
/**
 * Pre-render the initial HTML at build time using TanStack Start SSR.
 * This generates a properly server-rendered index.html so the client-side app
 * hydrates without errors, avoiding "Invariant failed" crashes.
 */

import { fileURLToPath } from "url";
import { dirname, join } from "path";
import fs from "fs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

async function prerender() {
  const clientDir = join(__dirname, "dist/client");
  const serverEntry = join(__dirname, "dist/server/server.js");

  if (!fs.existsSync(serverEntry)) {
    console.error('❌ Server entry not found. Run "npm run build" first.');
    process.exit(1);
  }

  try {
    const { default: serverHandler } = await import(serverEntry);

    // Create a fake request for the root path
    const request = new Request("http://localhost/", {
      method: "GET",
      headers: {
        "user-agent": "prerender-bot",
      },
    });

    // Render the page
    console.log("🔄 Pre-rendering initial HTML...");
    const response = await serverHandler.fetch(request);
    const html = await response.text();

    // Write to client/index.html
    const indexPath = join(clientDir, "index.html");
    fs.writeFileSync(indexPath, html, "utf-8");

    console.log(`✅ Pre-rendered HTML written to ${indexPath}`);
    console.log(`   Size: ${(html.length / 1024).toFixed(1)}KB`);
  } catch (error) {
    console.error("❌ Pre-render failed:", error);
    process.exit(1);
  }
}

prerender();
