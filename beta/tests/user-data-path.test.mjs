import assert from "node:assert/strict";
import test from "node:test";

import {
  resolveUserDataDirectory,
} from "../electron/user-data-path.mjs";

test("empty userData overrides remain ignored", () => {
  assert.equal(resolveUserDataDirectory(undefined), null);
  assert.equal(resolveUserDataDirectory("   "), null);
});

test("relative and POSIX root userData overrides are rejected", () => {
  for (const value of [".", "..", "relative/path", "/"]) {
    assert.throws(
      () => resolveUserDataDirectory(value, { platform: "darwin" }),
      /absolute non-root|filesystem root/,
      value,
    );
  }
});

test("Windows drive and UNC roots are rejected", () => {
  for (const value of [
    "C:\\",
    "\\\\server\\share\\",
  ]) {
    assert.throws(
      () => resolveUserDataDirectory(value, { platform: "win32" }),
      /filesystem root/,
      value,
    );
  }
});

test("absolute non-root userData overrides are normalized", () => {
  assert.equal(
    resolveUserDataDirectory(
      "/Users/example/app/../frontier-user-data",
      { platform: "darwin" },
    ),
    "/Users/example/frontier-user-data",
  );
  assert.equal(
    resolveUserDataDirectory(
      String.raw`C:\Users\example\AppData\..\Frontier`,
      { platform: "win32" },
    ),
    String.raw`C:\Users\example\Frontier`,
  );
  assert.equal(
    resolveUserDataDirectory(
      String.raw`\\server\share\frontier`,
      { platform: "win32" },
    ),
    String.raw`\\server\share\frontier`,
  );
});
