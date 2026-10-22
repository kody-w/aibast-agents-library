import assert from "node:assert/strict";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import {
  BROWSER_STARTUP_TIMEOUT_MS,
  closeResources,
  launchBrowser,
  startStaticServer,
} from "./helpers/download-center-browser.mjs";

const betaRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../../beta");

async function navigate(cdp, sessionId, url, { width, scripts, theme }) {
  await cdp.send(
    "Emulation.setDeviceMetricsOverride",
    { width, height: 800, deviceScaleFactor: 1, mobile: true },
    sessionId,
  );
  await cdp.send(
    "Emulation.setEmulatedMedia",
    { features: [{ name: "prefers-color-scheme", value: theme }] },
    sessionId,
  );
  await cdp.send(
    "Emulation.setScriptExecutionDisabled",
    { value: !scripts },
    sessionId,
  );
  const loaded = cdp.waitFor("Page.loadEventFired", sessionId);
  await Promise.all([loaded, cdp.send("Page.navigate", { url }, sessionId)]);
  if (!scripts) {
    await cdp.send(
      "Emulation.setScriptExecutionDisabled",
      { value: false },
      sessionId,
    );
  }
}

async function evaluate(cdp, sessionId, expression) {
  const result = await cdp.send(
    "Runtime.evaluate",
    { expression, awaitPromise: true, returnByValue: true },
    sessionId,
  );
  assert.equal(
    result.exceptionDetails,
    undefined,
    result.exceptionDetails?.exception?.description || result.exceptionDetails?.text,
  );
  return result.result.value;
}

test("retired Frontier URLs stay readable and point to both replacement paths", {
  timeout: BROWSER_STARTUP_TIMEOUT_MS + 30000,
}, async (t) => {
  const site = await startStaticServer(betaRoot);
  let browser;
  t.after(() => closeResources([browser, site]));
  try {
    browser = await launchBrowser({ signal: t.signal });
    t.diagnostic(
      `Frontier retirement browser: ${browser.executablePath} (${browser.version}); ${process.platform}/${process.arch}`,
    );

    for (const relative of ["index.html", "show-mode.html"]) {
      for (const width of [320, 390, 640]) {
        for (const theme of ["light", "dark"]) {
          for (const scripts of [false, true]) {
            const url = new URL(relative, site.pageUrl).href;
            await navigate(browser.cdp, browser.sessionId, url, {
              width,
              scripts,
              theme,
            });
            const page = await evaluate(
              browser.cdp,
              browser.sessionId,
              `(() => {
                const styles = getComputedStyle(document.documentElement);
                const main = document.querySelector("main");
                return {
                  title: document.title,
                  heading: document.querySelector("h1")?.textContent.trim(),
                  viewport: innerWidth,
                  overflow: document.documentElement.scrollWidth - innerWidth,
                  content: main?.innerText,
                  workshops: main?.querySelector('a[href="../index.html?view=solutions#workshops"]')
                    ?.textContent.trim(),
                  installer: main?.querySelector('a[href="../docs/installer.html"]')
                    ?.textContent.trim(),
                  colorScheme: styles.colorScheme,
                  background: styles.backgroundColor,
                  text: styles.color,
                  retiredControls: Boolean(document.querySelector(
                    "#download-dialog, #download-form, #release-status, #explorer, #surgeon",
                  )),
                };
              })()`,
            );

            assert.equal(page.title, "RAPP Brainstem Frontier has been retired");
            assert.equal(page.heading, "RAPP Brainstem Frontier has been retired");
            assert.equal(page.viewport, width);
            assert.equal(page.overflow, 0);
            assert.match(
              page.content,
              /The Frontier desktop app is no longer offered or updated\. Two paths replace it\./,
            );
            assert.match(
              page.content,
              /Your Brainstem, its agents and its memories live in a separate folder and are not affected\./,
            );
            assert.equal(page.workshops, "Browse the workshops");
            assert.equal(page.installer, "Install the Brainstem");
            assert.match(page.colorScheme, new RegExp(theme));
            assert.notEqual(page.background, page.text);
            assert.equal(page.retiredControls, false);
          }
        }
      }
    }
  } finally {
    await closeResources([browser, site]);
  }
});
