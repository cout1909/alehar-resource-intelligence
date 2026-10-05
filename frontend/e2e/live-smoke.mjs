// Read-only checks against the running workspace; no lender/review mutations.
import { chromium } from "@playwright/test";
import { mkdir } from "node:fs/promises";

const browser = await chromium.launch({ channel: "msedge", headless: true });
try {
  const page = await browser.newPage({
    viewport: { width: 1440, height: 1050 },
  });
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  for (const [route, title] of [
    ["/", "Alehar Resource Intelligence"],
    ["/lenders", "Lenders"],
    ["/lenders/4", "UGRO Capital"],
    ["/reviews", "Review queue"],
    ["/history", "Verification history"],
    ["/system", "System status"],
  ]) {
    await page.goto(`http://localhost:5173${route}`);
    await page.getByRole("heading", { name: title, exact: true }).waitFor();
    await page.waitForLoadState("networkidle");
    if (await page.getByRole("alert").count())
      throw new Error(`Page error on ${route}`);
    console.log(`PASS ${route}: ${title}`);
    if (route === "/") {
      await mkdir("../.runtime", { recursive: true });
      await page.screenshot({
        path: "../.runtime/phase2-dashboard.png",
        fullPage: true,
      });
    }
  }
  if (errors.length) throw new Error("Browser console reported errors");
  console.log("Live workspace: all six pages loaded without browser errors.");
} finally {
  await browser.close();
}
