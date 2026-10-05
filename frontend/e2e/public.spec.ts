import { expect, test } from "@playwright/test";

test("public demo browses evidence and rejects every mutation", async ({
  page,
  request,
}) => {
  const requests: string[] = [];
  page.on("request", (req) => {
    if (req.url().includes(":8001"))
      requests.push(`${req.method()} ${new URL(req.url()).pathname}`);
  });
  await page.goto("/");
  await expect(page.getByText("Public demo · Read only.")).toBeVisible();
  await expect(page.getByRole("button", { name: "Verify All" })).toBeDisabled();
  expect(requests.filter((path) => path === "GET /system/status").length).toBe(
    1,
  );
  expect(requests.filter((path) => path.startsWith("POST"))).toEqual([]);
  await expect(page.getByText(/Saved public-demo snapshot/)).toBeVisible();
  await page.goto("/lenders/6");
  await expect(
    page.getByRole("heading", { name: "Data Provenance" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Why this was flagged" }),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: "Verify Now" })).toBeDisabled();
  await expect(
    page.getByRole("button", { name: "Approve Finding", exact: true }),
  ).toBeDisabled();
  await expect(
    page.getByRole("button", { name: "Reject Finding", exact: true }),
  ).toBeDisabled();
  await page.goto("/reviews");
  for (const button of await page
    .getByRole("button", { name: /Finding/ })
    .all())
    await expect(button).toBeDisabled();
  const before = await (
    await request.get("http://127.0.0.1:8001/verification-results")
  ).json();
  for (const path of [
    "/verify-all",
    "/lenders/1/verify",
    "/verification-results/3/approve",
    "/verification-results/3/reject",
  ]) {
    const response = await request.post(`http://127.0.0.1:8001${path}`, {
      data: { note: "must not persist" },
    });
    expect(response.status()).toBe(403);
  }
  expect(
    await (
      await request.get("http://127.0.0.1:8001/verification-results")
    ).json(),
  ).toEqual(before);
  const status = await (
    await request.get("http://127.0.0.1:8001/system/status")
  ).json();
  expect(status.scheduler_enabled).toBe(false);
});
