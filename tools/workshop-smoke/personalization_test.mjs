// Personalization smoke: the page's whole premise is "every industry in the
// library runs through this same page". An adversarial review found Steps 3, 6
// and 7 silently describing Field Service Dispatch for all 104 agents — including
// 7/7 copy-paste CLI blocks that would scaffold a project with the wrong name.
// Confident, specific, wrong content is worse than a visible break, so this test
// asserts that NOTHING outside the selected agent's own vocabulary survives.
//
//   node personalization_test.mjs [pageUrl]
import { chromium } from 'playwright';

const url = process.argv[2] ||
  'https://microsoft.github.io/aibast-agents-library/docs/workshop.html';
const b = await chromium.launch();
const pg = await b.newPage();
const errs = []; pg.on('pageerror', e => errs.push(String(e)));
const fail = m => { throw new Error(m); };

// agents deliberately far from the default (energy field service)
const CASES = [
  { slug: 'patient-intake',          cat: 'healthcare' },
  { slug: 'it-helpdesk',             cat: 'cross-industry' },
  { slug: 'store-associate-copilot', cat: 'retail' },
];
// Vocabulary that can ONLY come from Field Service Dispatch. Bare "dispatch" and
// "technician" are deliberately excluded: IT Helpdesk's own authored scaffold uses
// both, so flagging them reported the page for correctly showing the right agent.
const LEAK = /field[- ]service|SCADA|fsd10\d|per-dispatcher|dispatch dashboard|route[- ]optimization|technician[- ]assignment|bookableresource|msdyn_workorder|technicians\.csv|service_requests\.csv/i;

for (const c of CASES) {
  await pg.goto(url + '?agent=' + c.slug);
  await pg.waitForTimeout(4500);

  const sel = await pg.locator('#pickName').textContent();
  if (LEAK.test(sel)) fail(`${c.slug}: selection line names the default agent`);

  // open every collapsible so hidden panels are in scope
  const n = await pg.locator('details').count();
  for (let i = 0; i < n; i++)
    await pg.locator('details').nth(i).evaluate(d => d.open = true);
  await pg.waitForTimeout(600);

  // NOTE: the "hard way" panels are <details class="uh"> siblings of #underhood,
  // not children — scoping to the section alone silently skips every CLI block.
  for (const sec of ['#understand', '#mission', '#underhood', 'details.uh',
                     '#verify', '#production']) {
    const txt = (await pg.locator(sec).allInnerTexts().catch(() => [])).join('\n');
    const hit = txt.match(LEAK);
    if (hit) fail(`${c.slug}: ${sec} still says "${hit[0]}" — page describes the wrong agent`);
  }

  // the copy-paste commands are the sharpest edge: a wrong --project-dir
  // scaffolds a project literally named after someone else's agent
  const code = await pg.locator('details.uh pre').allInnerTexts();
  for (const blk of code) {
    const hit = blk.match(LEAK);
    if (hit) fail(`${c.slug}: a CLI block still targets "${hit[0]}"`);
  }
  if (!code.join('\n').includes(c.slug))
    fail(`${c.slug}: no CLI block references this agent's own project dir`);

  // the sentence the participant says out loud must keep its authored casing
  const say = await pg.locator('#missionSay').textContent();
  if (/\bit helpdesk\b|\bfoia\b|\bhr\b(?! )/.test(say))
    fail(`${c.slug}: mission sentence lower-cased an acronym: ${say}`);
  if (/ agent agent /.test(say)) fail(`${c.slug}: doubled noun in mission: ${say}`);

  // the tally must not claim "five" for a stack with a different check count
  const cards = await pg.locator('#rcHost .rc').count();
  if (cards < 3) fail(`${c.slug}: verification questions did not load (${cards})`);
  for (let i = 1; i <= cards; i++)
    await pg.locator(`.rc[data-rc="${i}"] button.p`).click();
  await pg.waitForTimeout(300);
  const tally = await pg.locator('#rc-tally').textContent();
  if (!tally.includes(`all ${cards} green`))
    fail(`${c.slug}: tally hardcodes a count — "${tally}" with ${cards} checks`);

  // the architecture diagram's skill count must match the real skill count
  const labels = await pg.locator('[data-dyn=skillCount]').allTextContents();
  if (new Set(labels).size !== 1)
    fail(`${c.slug}: skill-count labels disagree: ${labels.join('/')}`);
}

// a share link the page cannot read back must say so, not die silently
for (const bad of ['?agent=totally-bogus-xyz', '?fp=not-a-real-id']) {
  await pg.goto(url + bad);
  await pg.waitForTimeout(4000);
  const t = await pg.locator('#pickName').textContent();
  if (!/didn’t match|didn't match/.test(t))
    fail(`${bad}: no explanation shown — "${t.trim().slice(0, 70)}"`);
  if ((await pg.locator('#rcHost .rc').count()) < 1 &&
      !(await pg.locator('#fpTrack').isVisible()))
    fail(`${bad}: fell back to an empty page`);
}

// switching picker modes must never strand the participant on an empty room
await pg.goto(url);
await pg.waitForTimeout(4500);
for (const mode of ['product', 'industry', 'firstparty', 'industry']) {
  await pg.locator(`#modeTabs button[data-mode="${mode}"]`).click();
  await pg.waitForTimeout(1800);
  const t = (await pg.locator('#pickName').textContent() || '').trim();
  if (/nothing yet/.test(t)) fail(`mode "${mode}" left the room empty: "${t}"`);
  if ((await pg.locator('#agentCards button').count()) === 0)
    fail(`mode "${mode}" rendered no agent cards`);
}

if (errs.length) fail('JS errors: ' + errs.join('; '));
console.log('personalization_test: PASS');
await b.close();
