import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { existsSync, mkdirSync, rmSync } from "node:fs";
import net from "node:net";
import path from "node:path";
import test from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";

const betaRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const pageUrl = pathToFileURL(path.join(betaRoot, "index.html")).href;

function findChrome() {
  const candidates = [
    process.env.CHROME_PATH,
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    process.env.PROGRAMFILES &&
      path.join(process.env.PROGRAMFILES, "Google", "Chrome", "Application", "chrome.exe"),
    process.env["PROGRAMFILES(X86)"] &&
      path.join(
        process.env["PROGRAMFILES(X86)"],
        "Google",
        "Chrome",
        "Application",
        "chrome.exe",
      ),
    process.env.LOCALAPPDATA &&
      path.join(
        process.env.LOCALAPPDATA,
        "Google",
        "Chrome",
        "Application",
        "chrome.exe",
      ),
  ].filter(Boolean);
  return candidates.find((candidate) => existsSync(candidate));
}

async function reservePort() {
  const server = net.createServer();
  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  const address = server.address();
  await new Promise((resolve) => server.close(resolve));
  return address.port;
}

function delay(milliseconds) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

class CdpConnection {
  constructor(socket) {
    this.socket = socket;
    this.nextId = 1;
    this.pending = new Map();
    this.waiters = new Map();
    socket.addEventListener("message", (event) => {
      const message = JSON.parse(event.data);
      if (message.id) {
        const pending = this.pending.get(message.id);
        if (!pending) return;
        this.pending.delete(message.id);
        if (message.error) {
          pending.reject(new Error(message.error.message));
        } else {
          pending.resolve(message.result);
        }
        return;
      }

      const key = `${message.sessionId || ""}:${message.method}`;
      const waiters = this.waiters.get(key) || [];
      this.waiters.delete(key);
      for (const waiter of waiters) waiter.resolve(message.params);
    });
  }

  static async connect(url) {
    const socket = new WebSocket(url);
    await new Promise((resolve, reject) => {
      socket.addEventListener("open", resolve, { once: true });
      socket.addEventListener("error", reject, { once: true });
    });
    return new CdpConnection(socket);
  }

  send(method, params = {}, sessionId) {
    const id = this.nextId;
    this.nextId += 1;
    const payload = { id, method, params };
    if (sessionId) payload.sessionId = sessionId;
    this.socket.send(JSON.stringify(payload));
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
    });
  }

  waitFor(method, sessionId, timeout = 10000) {
    const key = `${sessionId || ""}:${method}`;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        reject(new Error(`Timed out waiting for ${method}`));
      }, timeout);
      const waiters = this.waiters.get(key) || [];
      waiters.push({
        resolve: (value) => {
          clearTimeout(timer);
          resolve(value);
        },
      });
      this.waiters.set(key, waiters);
    });
  }

  close() {
    this.socket.close();
  }
}

async function launchBrowser() {
  const executable = findChrome();
  assert.ok(executable, "Chrome or Chromium is required for Download Center browser tests");
  const port = await reservePort();
  const profile = path.join(
    betaRoot,
    "node_modules",
    ".cache",
    `download-center-browser-${process.pid}-${Date.now()}`,
  );
  mkdirSync(profile, { recursive: true });
  const child = spawn(
    executable,
    [
      "--headless=new",
      "--disable-gpu",
      "--disable-background-networking",
      "--no-default-browser-check",
      "--no-first-run",
      "--no-sandbox",
      `--remote-debugging-port=${port}`,
      `--user-data-dir=${profile}`,
      "about:blank",
    ],
    { stdio: ["ignore", "ignore", "pipe"] },
  );
  child.stderr.resume();

  let browserMetadata;
  for (let attempt = 0; attempt < 100; attempt += 1) {
    if (child.exitCode !== null) break;
    try {
      const response = await fetch(`http://127.0.0.1:${port}/json/version`);
      if (response.ok) {
        browserMetadata = await response.json();
        break;
      }
    } catch {
      await delay(50);
    }
  }
  assert.ok(browserMetadata?.webSocketDebuggerUrl, "Chrome DevTools endpoint did not start");

  const cdp = await CdpConnection.connect(browserMetadata.webSocketDebuggerUrl);
  const { targetId } = await cdp.send("Target.createTarget", { url: "about:blank" });
  const { sessionId } = await cdp.send("Target.attachToTarget", {
    targetId,
    flatten: true,
  });
  await cdp.send("Page.enable", {}, sessionId);
  await cdp.send("Runtime.enable", {}, sessionId);
  await cdp.send("Network.enable", {}, sessionId);
  await cdp.send(
    "Network.setBlockedURLs",
    { urls: ["https://api.github.com/*"] },
    sessionId,
  );

  return {
    cdp,
    sessionId,
    async close() {
      cdp.close();
      if (child.exitCode === null) {
        child.kill("SIGTERM");
        await Promise.race([
          new Promise((resolve) => child.once("exit", resolve)),
          delay(2000).then(() => {
            if (child.exitCode === null) child.kill("SIGKILL");
          }),
        ]);
      }
      rmSync(profile, { recursive: true, force: true });
    },
  };
}

async function navigate(cdp, sessionId, url, { width, height, scripts }) {
  await cdp.send(
    "Emulation.setDeviceMetricsOverride",
    { width, height, deviceScaleFactor: 1, mobile: true },
    sessionId,
  );
  await cdp.send(
    "Emulation.setScriptExecutionDisabled",
    { value: !scripts },
    sessionId,
  );
  const loaded = cdp.waitFor("Page.loadEventFired", sessionId);
  await cdp.send("Page.navigate", { url }, sessionId);
  await loaded;
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
  assert.equal(result.exceptionDetails, undefined, result.exceptionDetails?.text);
  return result.result.value;
}

test("Download Center works without JavaScript and stays narrow under stress", {
  timeout: 30000,
}, async () => {
  const browser = await launchBrowser();
  try {
    for (const width of [320, 640]) {
      await navigate(browser.cdp, browser.sessionId, `${pageUrl}?no-js=${width}`, {
        width,
        height: 800,
        scripts: false,
      });
      const noJs = await evaluate(
        browser.cdp,
        browser.sessionId,
        `(() => ({
          viewport: innerWidth,
          overflow: document.documentElement.scrollWidth - innerWidth,
          fallbackVisible: document.querySelector("#no-js-download").getClientRects().length > 0,
          formVisible: document.querySelector("#download-form").getClientRects().length > 0,
          triggerVisible: document.querySelector("#trigger-install").getClientRects().length > 0,
          panelsVisible: [...document.querySelectorAll(".accordion-panel")]
            .every((panel) => panel.getClientRects().length > 0),
          downloads: [...document.querySelectorAll("#no-js-download a[download]")]
            .map((link) => ({ href: link.href, download: link.download })),
          source: document.querySelector("#source-link").href,
          release: document.querySelector("#release-link-top").href,
          goldenPath: document.querySelector("#golden-path-link").href,
        }))()`,
      );
      assert.equal(noJs.viewport, width);
      assert.equal(noJs.overflow, 0);
      assert.equal(noJs.fallbackVisible, true);
      assert.equal(noJs.formVisible, false);
      assert.equal(noJs.triggerVisible, false);
      assert.equal(noJs.panelsVisible, true);
      assert.equal(noJs.downloads.length, 2);
      assert.ok(noJs.downloads.every((download) => download.download));
      assert.match(noJs.downloads[0].href, /frontier\.ps1$/);
      assert.match(noJs.downloads[1].href, /frontier\.sh$/);
      assert.match(noJs.source, /github\.com\/microsoft\/aibast-agents-library\/tree\/main\/beta$/);
      assert.match(noJs.release, /github\.com\/microsoft\/aibast-agents-library\/releases$/);
      assert.match(
        noJs.goldenPath,
        /github\.com\/microsoft\/aibast-agents-library\/blob\/main\/beta\/GOLDEN_PATH\.md$/,
      );
    }

    for (const width of [320, 640]) {
      await navigate(
        browser.cdp,
        browser.sessionId,
        `${pageUrl}?scoutTheme=dark&scripts=${width}`,
        { width, height: 800, scripts: true },
      );
      const enhanced = await evaluate(
        browser.cdp,
        browser.sessionId,
        `(async () => {
          document.querySelector("#expand-all").click();
          const notice = document.querySelector("#load-error");
          notice.hidden = false;
          notice.textContent =
            "GitHub returned 403 for https://api.github.com/repos/microsoft/aibast-agents-library/releases?per_page=30";
          await new Promise((resolve) => setTimeout(resolve, 50));
          return {
            viewport: innerWidth,
            overflow: document.documentElement.scrollWidth - innerWidth,
            expanded: document.querySelectorAll(
              '.accordion-trigger[aria-expanded="true"]',
            ).length,
            noJsFallbackPresent: Boolean(document.querySelector("#no-js-download")),
          };
        })()`,
      );
      assert.equal(enhanced.viewport, width);
      assert.equal(enhanced.overflow, 0);
      assert.equal(enhanced.expanded, 4);
      assert.equal(enhanced.noJsFallbackPresent, false);
    }

    await browser.cdp.send(
      "Emulation.setEmulatedMedia",
      {
        features: [{ name: "prefers-reduced-motion", value: "reduce" }],
      },
      browser.sessionId,
    );
    const reducedMotion = await evaluate(
      browser.cdp,
      browser.sessionId,
      'getComputedStyle(document.documentElement).scrollBehavior',
    );
    assert.equal(reducedMotion, "auto");
  } finally {
    await browser.close();
  }
});
