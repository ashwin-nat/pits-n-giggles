import { unzipSync } from "fflate";
import { NotAZipFileError } from "./pngtErrors";

export type ZipEntries = Record<string, Uint8Array>;

// Thin wrapper around fflate.unzipSync -- unzips the full archive in one pass
// and normalizes fflate's throw into our own NotAZipFileError, per the
// pngt header-validation sequence ("fflate throwing on unzip already covers
// 'not a ZIP file' -- no separate magic-byte check needed in JS").
export function unzipArchive(bytes: Uint8Array, label: string): ZipEntries {
  try {
    return unzipSync(bytes);
  } catch (err) {
    throw new NotAZipFileError(label);
  }
}

const textDecoder = new TextDecoder("utf-8");

export function decodeText(bytes: Uint8Array): string {
  return textDecoder.decode(bytes);
}

export function readJsonEntry<T>(entries: ZipEntries, path: string): T | undefined {
  const bytes = entries[path];
  if (bytes === undefined) {
    return undefined;
  }
  return JSON.parse(decodeText(bytes)) as T;
}
