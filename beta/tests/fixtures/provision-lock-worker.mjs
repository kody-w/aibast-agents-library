import { appendFileSync, rmSync, writeFileSync } from "node:fs";

import { acquireProvisioningLock } from "../../electron/provision-lock.mjs";

const [brainstemHome, eventFile, readyFile, mode, holdText] =
  process.argv.slice(2);
const holdMs = Number.parseInt(holdText || "250", 10);
const lease = await acquireProvisioningLock({
  brainstemHome,
  pollIntervalMs: 20,
  timeoutMs: 10_000,
});

const record = (event) => appendFileSync(
  eventFile,
  `${JSON.stringify({
    event,
    pid: process.pid,
    reclaimed: lease.reclaimed,
    token: lease.token,
    at: Date.now(),
  })}\n`,
);
record("acquired");
const activeFile = `${eventFile}.active`;
writeFileSync(activeFile, lease.token, { flag: "wx" });
if (readyFile) writeFileSync(readyFile, `${process.pid}\n`);

if (mode === "hold") {
  setInterval(() => {}, 1_000);
} else {
  await new Promise((resolve) => setTimeout(resolve, holdMs));
  record("releasing");
  rmSync(activeFile);
  if (!lease.release()) throw new Error("Lock release lost ownership.");
  record("released");
}
