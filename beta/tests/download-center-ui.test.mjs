import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const betaRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const read = (name) => readFileSync(path.join(betaRoot, name), "utf8").replace(/\r\n/g, "\n");
const pages = new Map([
  ["index.html", read("index.html")],
  ["show-mode.html", read("show-mode.html")],
]);

const retirementCopy = [
  "The Frontier desktop app is no longer offered or updated. Two paths replace it.",
  "GitHub Copilot in VS Code is all you need.",
  "install the Brainstem with one line, then build agents and learn how they work.",
  "Already installed the desktop app? It no longer receives updates.",
  "Your Brainstem, its agents and its memories live in a separate folder and are not affected.",
];

test("both retired public aliases carry the complete replacement guidance", () => {
  for (const [name, page] of pages) {
    assert.match(page, /<title>RAPP Brainstem Frontier has been retired<\/title>/, name);
    assert.match(page, /<h1>RAPP Brainstem Frontier has been retired<\/h1>/, name);
    for (const sentence of retirementCopy) {
      assert.ok(page.includes(sentence), `${name}: missing ${sentence}`);
    }
    assert.match(
      page,
      /<strong>Workshops:<\/strong>[\s\S]*href="\.\.\/index\.html\?view=solutions#workshops">Browse the workshops<\/a>/,
      name,
    );
    assert.match(
      page,
      /<strong>Build from scratch on your own device:<\/strong>[\s\S]*href="\.\.\/docs\/installer\.html">Install the Brainstem<\/a>/,
      name,
    );
  }
});

test("the two aliases render the same retirement content", () => {
  const main = (page) => page.match(/<main>([\s\S]*?)<\/main>/)?.[1].trim();
  assert.equal(main(pages.get("index.html")), main(pages.get("show-mode.html")));
});

test("retirement pages keep the shared design and consent stamps exactly once", () => {
  for (const [name, page] of pages) {
    assert.equal(page.match(/<!-- aibast-design:start -->/g)?.length, 1, name);
    assert.equal(page.match(/<!-- aibast-design:end -->/g)?.length, 1, name);
    assert.equal(page.match(/<!-- clarity:start -->/g)?.length, 1, name);
    assert.equal(page.match(/<!-- clarity:end -->/g)?.length, 1, name);
    assert.match(page, /background: var\(--cp-bg\)/, name);
    assert.match(page, /color: var\(--cp-text\)/, name);
    assert.match(page, /@media \(prefers-color-scheme: dark\)/, name);
  }
});

test("retirement pages remain readable at 390px without the retired UI", () => {
  for (const [name, page] of pages) {
    assert.match(page, /<meta name="viewport" content="width=device-width, initial-scale=1">/, name);
    assert.match(page, /width: min\(100%, 46rem\)/, name);
    assert.match(page, /overflow-wrap: anywhere/, name);
    assert.match(page, /@media \(max-width: 390px\)/, name);
    assert.doesNotMatch(page, /download-center\.js|download-dialog|release-status|show-mode-tour\.js/, name);
  }
});

test("all stamped inline scripts remain valid JavaScript", () => {
  for (const [name, page] of pages) {
    const scripts = [...page.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)];
    assert.ok(scripts.length >= 1, name);
    for (const [, source] of scripts) {
      assert.doesNotThrow(() => new Function(source), name);
    }
  }
});
