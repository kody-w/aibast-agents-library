// Workshop page smoke: picker from raw registry, personalization, deep links.
// Run from a folder with playwright installed: node workshop_page_test.mjs [pageUrl]
import { chromium } from 'playwright';
const url = process.argv[2] ||
  'https://microsoft.github.io/aibast-agents-library/docs/workshop.html';
const b = await chromium.launch();
const pg = await b.newPage();
const errs = []; pg.on('pageerror', e => errs.push(String(e)));
await pg.goto(url); await pg.waitForTimeout(4000);
const pills = await pg.locator('#indPills button').count();
if (pills < 10) throw new Error('industry pills missing: ' + pills);
await pg.locator('#indPills button[data-cat="energy"]').click();
await pg.waitForTimeout(400);
await pg.locator('#agentCards button[data-slug="field-service-dispatch"]').click();
await pg.waitForTimeout(3000);
const mission = await pg.locator('#missionSay').textContent();
const rc = await pg.locator('#rcHost .rc').count();
if (!mission.includes('field service dispatch')) throw new Error('mission not personalized');
if (rc < 4) throw new Error('verification cards missing: ' + rc);
if (errs.length) throw new Error('JS errors: ' + errs.join('; '));
console.log('workshop_page_test: PASS —', pills, 'industries,', rc, 'checks for field-service');
await b.close();
