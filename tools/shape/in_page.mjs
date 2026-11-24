// Runs the Brainstem shape record inside Python compiled to WebAssembly: the engine a web page carries.
// The kernel and the agent files are the unchanged files; nothing is installed on the machine.
//
//   npm install pyodide@0.25.1          (Python 3.11, the kernel's own version)
//   node tools/shape/in_page.mjs <stage dir> <out name> <run list name>
//
// <stage dir> holds kernel/ (rapp_brainstem), agents/, site/ (the kernel's pure Python packages,
// unpacked), brainstem_shape.py, and the run list. The record is written into <stage dir>.
import { createRequire } from "node:module";
// The in-page Python package is looked up from the folder you run this in, where npm installed it.
const { loadPyodide } = createRequire(process.cwd() + "/")("pyodide");
import fs from "node:fs";
const [stage, out, runList] = process.argv.slice(2);
const py = await loadPyodide();
py.FS.mkdirTree("/stage"); py.FS.mount(py.FS.filesystems.NODEFS, { root: stage }, "/stage");
py.FS.mkdirTree("/home/pyodide/h");
const report = {};
for (const pkg of ["requests", "markupsafe", "pycryptodome", "beautifulsoup4", "ssl"]) {
  try { await py.loadPackage(pkg); report[pkg] = "ok"; } catch (e) { report[pkg] = String(e).slice(0, 160); }
}
console.log("carried packages:", JSON.stringify(report));
py.globals.set("ARGV", py.toPy(["record", "/stage/kernel", "/stage/agents", "/stage/" + out, "--run-list", "/stage/" + runList]));
await py.runPythonAsync(`
import os, sys, runpy
os.environ["HOME"] = "/home/pyodide/h"
sys.path.insert(0, "/stage"); sys.path.insert(0, "/stage/site")
import brainstem_shape
r = brainstem_shape.record_main(list(ARGV))
print("kernel import:", r["kernel_import"], "| agent files recorded:", len(r["agents"]), "| python", r["python"], r["platform"])
if r["kernel_import"] != "ok": print(r.get("trace"))
`);
