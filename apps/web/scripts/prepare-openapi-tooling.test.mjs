import assert from "node:assert/strict";
import { test } from "node:test";
import {
  mkdirSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  symlinkSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";
import {
  compatibleImport,
  originalImport,
  prepareOpenApiTooling,
} from "./prepare-openapi-tooling.mjs";

const webRoot = dirname(dirname(fileURLToPath(import.meta.url)));
const installed = join(
  webRoot,
  "node_modules/@redocly/openapi-core/lib/utils.js",
);

function fixture(run) {
  const root = mkdtempSync(join(tmpdir(), "norskallstars-tooling-"));
  const target = join(root, "node_modules/@redocly/openapi-core/lib/utils.js");
  mkdirSync(dirname(target), { recursive: true });
  const source = readFileSync(installed, "utf8").replace(
    compatibleImport,
    originalImport,
  );
  writeFileSync(target, source);
  try {
    run(root, target, source);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
}

test("reviewed dependency adapts once and remains idempotent", () => {
  fixture((root, target, source) => {
    prepareOpenApiTooling(root);
    const adapted = readFileSync(target, "utf8");
    assert.equal(adapted, source.replace(originalImport, compatibleImport));
    prepareOpenApiTooling(root);
    assert.equal(readFileSync(target, "utf8"), adapted);
  });
});

test("unknown vendor bytes fail closed without modifying the file", () => {
  fixture((root, target, source) => {
    const changed = source + "\n// changed dependency\n";
    writeFileSync(target, changed);
    assert.throws(() => prepareOpenApiTooling(root), /dependency changed/);
    assert.equal(readFileSync(target, "utf8"), changed);
  });
});

test("a symlink cannot redirect dependency preparation", () => {
  fixture((root, target, source) => {
    const outside = join(root, "outside.js");
    writeFileSync(outside, source);
    rmSync(target);
    symlinkSync(outside, target);
    assert.throws(
      () => prepareOpenApiTooling(root),
      /unexpected dependency file/,
    );
    assert.equal(readFileSync(outside, "utf8"), source);
  });
});

test("real Redocly URL matching preserves header scope with minimatch 11", async () => {
  prepareOpenApiTooling(webRoot);
  const load = createRequire(import.meta.url);
  const { readFileFromUrl } = load(installed);
  const observed = [];
  const config = {
    headers: [
      {
        name: "X-Synthetic",
        value: "fixture",
        matches: "https://example.invalid/specs/**",
      },
    ],
    customFetch: async (url, options) => {
      observed.push({ url, headers: options.headers });
      return { ok: true, text: async () => "synthetic", headers: new Map() };
    },
  };
  assert.equal(
    (await readFileFromUrl("https://example.invalid/specs/a.json", config))
      .body,
    "synthetic",
  );
  await readFileFromUrl("https://other.invalid/specs/a.json", config);
  await readFileFromUrl("https://example.invalid/unrelated/a.json", config);
  assert.deepEqual(
    observed.map((x) => x.headers),
    [{ "X-Synthetic": "fixture" }, {}, {}],
  );
});
