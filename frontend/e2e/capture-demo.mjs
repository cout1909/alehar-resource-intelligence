import { chromium } from "@playwright/test";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const output = path.join(root, "docs/screenshots");
await mkdir(output, { recursive: true });
const apiBase = process.env.DEMO_API_URL || "http://127.0.0.1:8000";
const base = process.env.DEMO_UI_URL || "http://localhost:5173";
const lenders = await (await fetch(`${apiBase}/lenders`)).json();
const latest = await (await fetch(`${apiBase}/dashboard/latest`)).json();
const history = await (await fetch(`${apiBase}/verification-results?limit=100`)).json();
if (lenders.total !== 8 || lenders.lenders.some(row => !row.alehar_url || !row.retrieved_at)) throw Error("Expected eight curated, attributed records");
const verified = history.find(row => row.status === "VERIFIED" && row.ai_status === "success") || latest.find(row => row.status === "VERIFIED");
const review = latest.find(row => row.status === "REVIEW_REQUIRED");
if (!verified || !review) throw Error("Actual saved verified and review-required examples are needed");
const browser = await chromium.launch({ channel: process.platform === "win32" ? "msedge" : undefined });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, timezoneId: "Asia/Kolkata" });
const errors = [];
const requests = [];
page.on("pageerror", error => errors.push(error.message));
page.on("request", request => { if (request.url().startsWith(apiBase)) requests.push({ method: request.method(), path: new URL(request.url()).pathname }); });
async function capture(route, heading, name) {
  await page.goto(`${base}${route}`);
  await page.getByRole("heading", { name: heading, exact: true }).waitFor();
  await page.waitForLoadState("networkidle");
  await page.screenshot({ path: path.join(output, `${name}.png`), fullPage: true });
}
try {
  await capture("/", "Recent Verification Activity", "dashboard");
  const verifiedRoute = `/lenders/${verified.lender_id}?result=${verified.id}`;
  const reviewRoute = `/lenders/${review.lender_id}?result=${review.id}`;
  await capture(verifiedRoute, "Data Provenance", "lender-detail");
  await page.getByRole("region", { name: "Data Provenance" }).screenshot({ path: path.join(output, "provenance.png") });
  await capture(reviewRoute, "Why this was flagged", "review-required");
  await capture("/reviews", "Review queue", "review-queue");
  await capture("/system", "System status", "system");
  await capture("/lenders", "Lenders", "lenders");
  await capture("/history", "Verification history", "history");
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(base);
  await page.getByRole("heading", { name: "Recent Verification Activity" }).waitFor();
  if (!await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)) throw Error("Mobile page overflows");
  if (errors.length || requests.some(request => request.method !== "GET")) throw Error("Unexpected browser error or mutation while browsing");
  await writeFile(path.join(root, "docs/demo-examples.json"), JSON.stringify({ verified: verifiedRoute, review_required: reviewRoute, screenshot_date: new Date().toISOString(), browser_errors: errors.length, browsing_mutations: 0 }, null, 2) + "\n");
  console.log("Captured eight actual application screenshots; mobile fit, provenance and read-only browsing checks passed.");
} finally {
  await browser.close();
}
