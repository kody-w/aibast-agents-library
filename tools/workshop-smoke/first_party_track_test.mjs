// First-party track smoke: the 1P branch must be a real guide, not a dead end.
// Guards the regression the workshop shipped with — picking a Microsoft-built
// agent used to print one sentence and leave the seller with nowhere to go.
//
// Run from a folder with playwright installed:
//   node first_party_track_test.mjs [pageUrl] [repoRoot]
// repoRoot lets us test local first_party.json edits before they are pushed,
// since the page always reads library data from the raw.githubusercontent mirrors.
import { chromium } from 'playwright';
import { readFileSync } from 'node:fs';

const url = process.argv[2] ||
  'https://microsoft.github.io/aibast-agents-library/docs/workshop.html';
const root = process.argv[3] || null;

const b = await chromium.launch();
const pg = await b.newPage();
const errs = [];
pg.on('pageerror', e => errs.push(String(e)));

if (root) {
  await pg.route('**/first_party.json', r =>
    r.fulfill({ status: 200, contentType: 'application/json',
                body: readFileSync(root + '/twin/first_party.json', 'utf8') }));
}

const fail = m => { throw new Error(m); };
const vis = async sel => pg.locator(sel).isVisible();

await pg.goto(url);
await pg.waitForTimeout(4000);

// ── 1. first-party pick opens a real track ────────────────────────────────
await pg.locator('#modeTabs button[data-mode="firstparty"]').click();
await pg.waitForTimeout(600);
const groups = pg.locator('#indPills button');
if (await groups.count() < 2) fail('first-party group pills missing: ' + await groups.count());
await groups.first().click();
await pg.waitForTimeout(500);
const cards = pg.locator('#agentCards button');
if (await cards.count() < 5) fail('first-party cards missing: ' + await cards.count());
await cards.first().click();
await pg.waitForTimeout(800);

if (!await vis('#fpTrack')) fail('fpTrack hidden after a first-party pick');
for (const s of ['#understand', '#mission', '#underhood'])
  if (await vis(s)) fail(`custom-build section ${s} still shown on the 1P track`);

for (const id of ['fpSummary', 'fpSurface', 'fpStatusNote', 'fpSay']) {
  const t = (await pg.locator('#' + id).textContent() || '').trim();
  if (t.length < 25) fail(`#${id} empty or stub on the 1P track ("${t}")`);
}
const prereq = await pg.locator('#fpPrereq li').count();
if (prereq < 2) fail('prerequisites missing: ' + prereq);

// the whole point: the official docs must be present, labelled, and real
const docs = pg.locator('#fpDocs a.fpdoc');
if (await docs.count() !== 2) fail('expected 2 Learn doc links, got ' + await docs.count());
for (let i = 0; i < 2; i++) {
  const href = await docs.nth(i).getAttribute('href');
  if (!/^https:\/\/learn\.microsoft\.com\//.test(href || ''))
    fail('doc link is not a Microsoft Learn URL: ' + href);
  const label = (await docs.nth(i).textContent() || '').trim();
  if (label.length < 40) fail('doc link has no explanatory context: ' + label);
}
// step numbering must not read "Step 5" as the third thing you do
const pk = (await pg.locator('#verify .pk').textContent() || '').trim();
if (pk !== 'Step 4') fail('verify step not renumbered for the 1P track: ' + pk);
if ((await pg.locator('#rcHost li').count()) < 3) fail('1P exercise-once steps missing');

// ── 2. GA vs Preview is stated, and stated differently ────────────────────
// the card label carries "(GA)" / "(Preview)" — the caveat must track it
let sawPreview = false, sawGA = false;
const n = await cards.count();
for (let i = 0; i < n; i++) {
  const label = (await cards.nth(i).textContent()) || '';
  await cards.nth(i).click();
  await pg.waitForTimeout(300);
  const t = (await pg.locator('#fpStatusNote').textContent()) || '';
  if (/\(Preview\)/.test(label)) {
    sawPreview = true;
    if (!/in Preview/.test(t)) fail('Preview agent missing its caveat: ' + label.slice(0, 40));
    if (/don.t hang a customer commitment/.test(t) === false)
      fail('Preview caveat lost its commitment warning');
  } else if (/\(GA\)/.test(label)) {
    sawGA = true;
    if (!/is GA/.test(t)) fail('GA agent got the wrong status note: ' + label.slice(0, 40));
  }
}
if (!sawPreview || !sawGA) fail(`needed both GA and Preview in group 1 (GA=${sawGA} Preview=${sawPreview})`);

// ── 3. switching back to a custom agent fully restores the build track ────
await pg.locator('#modeTabs button[data-mode="industry"]').click();
await pg.waitForTimeout(500);
await pg.locator('#indPills button[data-cat="energy"]').click();
await pg.waitForTimeout(400);
await pg.locator('#agentCards button[data-slug="field-service-dispatch"]').click();
await pg.waitForTimeout(3000);

if (await vis('#fpTrack')) fail('fpTrack still shown after switching to a custom agent');
for (const s of ['#understand', '#mission', '#underhood'])
  if (!await vis(s)) fail(`custom-build section ${s} not restored`);
const h2 = await pg.locator('#verifyH2').textContent();
if (!/Copilot Studio/.test(h2)) fail('verify heading not restored: ' + h2);
const lead = await pg.locator('#verifyLead').textContent();
if (/first-party|Exercise it once/i.test(lead)) fail('verify lead still carries 1P copy');
if ((await pg.locator('#verify .pk').textContent()).trim() !== 'Step 5')
  fail('verify step number not restored');
if ((await pg.locator('#rcHost .rc').count()) < 4) fail('custom verification cards did not reload');

// ── 4. deep link straight into the 1P track ───────────────────────────────
await pg.goto(url + '?fp=sales-qualification-1p');
await pg.waitForTimeout(4000);
if (!await vis('#fpTrack')) fail('?fp= deep link did not open the 1P track');
if ((await pg.locator('#fpDocs a.fpdoc').count()) !== 2) fail('deep link produced no doc links');

if (errs.length) fail('JS errors: ' + errs.join('; '));
console.log('first_party_track_test: PASS');
await b.close();
