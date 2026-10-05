import { expect, test } from "@playwright/test";

test("complete verification and human-review workflow without AI", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Alehar Resource Intelligence" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Verify All" }).click();
  await expect(
    page.getByRole("status").filter({ hasText: "Checked 8 lenders" }),
  ).toBeVisible();
  await page
    .getByRole("navigation")
    .getByRole("link", { name: "Lenders", exact: true })
    .click();
  await page.getByLabel("Search lenders").fill("HDFC");
  await expect(
    page.getByRole("link", { name: "HDFC Bank", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "ICICI Bank", exact: true }),
  ).toHaveCount(0);
  await page.getByRole("link", { name: "HDFC Bank", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Stored data" }),
  ).toBeVisible();
  await expect(
    page.getByText("AI analysis is not enabled.", { exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Verify Now" }).click();
  await expect(page.getByRole("button", { name: "Verify Now" })).toBeEnabled();
  await expect(
    page.getByRole("heading", { name: "Source evidence" }),
  ).toBeVisible();

  await page
    .getByRole("navigation")
    .getByRole("link", { name: "Review queue" })
    .click();
  const sidbi = page
    .locator("article")
    .filter({ has: page.getByRole("link", { name: "SIDBI", exact: true }) });
  await sidbi
    .getByRole("button", { name: "Approve Finding", exact: true })
    .click();
  await page
    .getByLabel("Reviewer note")
    .fill("Reviewed synthetic evidence in browser test.");
  await page.getByRole("button", { name: "Cancel", exact: true }).click();
  await expect(sidbi).toBeVisible();
  await sidbi
    .getByRole("button", { name: "Approve Finding", exact: true })
    .click();
  await page
    .getByLabel("Reviewer note")
    .fill("Reviewed synthetic evidence in browser test.");
  await page.getByRole("button", { name: "Confirm approve" }).click();
  await expect(sidbi).toHaveCount(0);
  const icici = page.locator("article").filter({
    has: page.getByRole("link", { name: "ICICI Bank", exact: true }),
  });
  await icici
    .getByRole("button", { name: "Reject Finding", exact: true })
    .click();
  await page.getByRole("button", { name: "Confirm reject" }).click();
  await expect(
    page.getByRole("heading", { name: "Review queue is clear" }),
  ).toBeVisible();

  await page
    .getByRole("navigation")
    .getByRole("link", { name: "History", exact: true })
    .click();
  await page.getByLabel("Review status").selectOption("APPROVED");
  await expect(
    page.getByRole("link", { name: "SIDBI", exact: true }),
  ).toBeVisible();
  await page.getByRole("link", { name: "SIDBI", exact: true }).click();
  await expect(
    page.getByText("Reviewed synthetic evidence in browser test."),
  ).toBeVisible();
  await page
    .getByRole("navigation")
    .getByRole("link", { name: "System", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "System status" }),
  ).toBeVisible();
  await expect(
    page.getByText(
      "AI analysis is not enabled. Deterministic verification is still active.",
    ),
  ).toBeVisible();
  await expect(page.locator("body")).not.toContainText("GROQ_API_KEY");
  expect(errors).toEqual([]);
});

test("mobile layout stays inside viewport and backend failure offers retry", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Recent Verification Activity" }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  await page.route("**/system/status", (route) => route.abort());
  await page
    .getByRole("navigation")
    .getByRole("link", { name: "System", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Backend offline" }),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: "Retry" })).toBeVisible();
});
