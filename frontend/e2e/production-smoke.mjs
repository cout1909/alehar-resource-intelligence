import { chromium, expect } from '@playwright/test';
import assert from 'node:assert/strict';

const api = process.env.DEMO_API_URL;
const ui = process.env.DEMO_UI_URL;
if (!api || !ui) throw Error('Set DEMO_API_URL and DEMO_UI_URL to the deployed endpoints.');
const json = async path => {
  const response = await fetch(`${api}${path}`);
  assert.equal(response.status, 200);
  return response.json();
};
assert.equal((await json('/health')).status, 'ok');
const status = await json('/system/status');
assert.equal(status.public_demo_mode, true);
assert.equal(status.public_demo_snapshot, true);
assert.equal(status.scheduler_enabled, false);
assert.equal(status.ai_enabled, false);
assert.equal((await json('/lenders')).total, 8);
const before = await json('/verification-results');
assert.equal(before.length, 8);
for (const path of ['/verify-all', '/lenders/1/verify', '/verification-results/22/approve', '/verification-results/22/reject']) {
  const response = await fetch(`${api}${path}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ note: 'must not persist' }) });
  assert.equal(response.status, 403, path);
}
assert.deepEqual(await json('/verification-results'), before);
for (const path of ['/docs', '/redoc', '/openapi.json']) assert.equal((await fetch(`${api}${path}`)).status, 404);
const allowed = await fetch(`${api}/health`, { headers: { Origin: ui } });
assert.equal(allowed.headers.get('access-control-allow-origin'), ui);
const foreign = await fetch(`${api}/health`, { headers: { Origin: 'https://example.invalid' } });
assert.equal(foreign.headers.get('access-control-allow-origin'), null);

const browser = await chromium.launch({ channel: process.platform === 'win32' ? 'msedge' : undefined });
try {
  const context = await browser.newContext(); // Fresh incognito context: no inherited login, cookies or cache.
  assert.equal((await context.cookies()).length, 0);
  const page = await context.newPage();
  const errors = [];
  const mutations = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('request', request => {
    if (request.url().startsWith(api) && !['GET', 'HEAD', 'OPTIONS'].includes(request.method())) mutations.push(request.url());
  });
  await page.goto(ui);
  await expect(page.getByText(/Public demo.*Read only/)).toBeVisible();
  await expect(page.getByText(/Saved public-demo snapshot/)).toBeVisible();
  await expect(page.getByRole('button', { name: /Verify All/ })).toBeDisabled();
  for (const lender of [3, 6]) {
    await page.goto(`${ui}/lenders/${lender}`);
    await expect(page.getByRole('heading', { name: 'Data Provenance', exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: /Verify Now/ })).toBeDisabled();
  }
  await expect(page.getByRole('heading', { name: 'Why this was flagged', exact: true })).toBeVisible();
  for (const name of ['Approve Finding', 'Reject Finding']) await expect(page.getByRole('button', { name, exact: true })).toBeDisabled();
  assert.deepEqual(errors, []);
  assert.deepEqual(mutations, []);
  console.log('PASS: production API, eight saved results, mutation guards, exact CORS, hidden API docs, anonymous incognito browsing, direct routes, and disabled controls.');
} finally {
  await browser.close();
}
