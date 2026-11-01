// Temporary, fail-closed API adapter; never alters the patched minimatch algorithm.
import { createHash } from "node:crypto";
import {
  constants,
  closeSync,
  fstatSync,
  ftruncateSync,
  lstatSync,
  openSync,
  readFileSync,
  writeSync,
} from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { Buffer } from "node:buffer";
import process from "node:process";
import { error } from "node:console";

export const originalImport = 'const minimatch = require("minimatch");';
export const compatibleImport = 'const { minimatch } = require("minimatch");';
const originalHash =
  "896a9acce92e3e5905aa267e895985d57888a87f500d58c29da9c8f9d488ff1c";
const compatibleHash =
  "825736f13fb67dc4a1e2157bb51396209c7343cfd00376ed5d923e3e9ff82a18";
const hash = (text) => createHash("sha256").update(text).digest("hex");

export function prepareOpenApiTooling(webRoot) {
  let directory = resolve(webRoot);
  for (const name of ["node_modules", "@redocly", "openapi-core", "lib"]) {
    directory = join(directory, name);
    const entry = lstatSync(directory);
    if (!entry.isDirectory() || entry.isSymbolicLink()) {
      throw new Error("OpenAPI adapter: unexpected dependency directory");
    }
  }
  const target = join(directory, "utils.js");
  const entry = lstatSync(target);
  if (!entry.isFile() || entry.isSymbolicLink()) {
    throw new Error("OpenAPI adapter: unexpected dependency file");
  }
  const fd = openSync(target, constants.O_RDWR | (constants.O_NOFOLLOW ?? 0));
  try {
    const info = fstatSync(fd);
    if (!info.isFile() || info.size > 128 * 1024) {
      throw new Error("OpenAPI adapter: unexpected dependency size/type");
    }
    const source = readFileSync(fd, "utf8");
    if (hash(source) === compatibleHash) return;
    if (
      hash(source) !== originalHash ||
      source.split(originalImport).length !== 2
    ) {
      throw new Error(
        "OpenAPI adapter: dependency changed; review compatibility",
      );
    }
    const adapted = source.replace(originalImport, compatibleImport);
    if (hash(adapted) !== compatibleHash) {
      throw new Error("OpenAPI adapter: unexpected adapted bytes");
    }
    const bytes = Buffer.from(adapted);
    let written = 0;
    while (written < bytes.length) {
      const count = writeSync(
        fd,
        bytes,
        written,
        bytes.length - written,
        written,
      );
      if (!count) throw new Error("OpenAPI adapter: incomplete write");
      written += count;
    }
    ftruncateSync(fd, bytes.length);
  } finally {
    closeSync(fd);
  }
}

if (
  process.argv[1] &&
  resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  try {
    prepareOpenApiTooling(dirname(dirname(fileURLToPath(import.meta.url))));
  } catch {
    error(
      "OpenAPI compatibility preparation failed; review the dependency adapter.",
    );
    process.exitCode = 1;
  }
}
