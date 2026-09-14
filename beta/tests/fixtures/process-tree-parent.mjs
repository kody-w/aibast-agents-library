import { spawn } from "node:child_process";
import path from "node:path";

const grandchild = path.join(import.meta.dirname, "process-tree-grandchild.mjs");
spawn(process.execPath, [grandchild, process.argv[2]], {
  stdio: "ignore",
});
setInterval(() => {}, 1_000);
