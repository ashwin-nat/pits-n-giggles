// Mirrors lib/pngt/exceptions.py -- same file format, same validation sequence,
// so the same failure modes apply on the JS read side.

export class PngtError extends Error {}

export class NotAZipFileError extends PngtError {
  constructor(path: string) {
    super(`Not a valid ZIP file: ${path}`);
  }
}

export class InvalidHeaderError extends PngtError {
  constructor(path: string, reason: string) {
    super(`Invalid header.json in ${path}: ${reason}`);
  }
}

export class InvalidManifestError extends PngtError {
  constructor(path: string, reason: string) {
    super(`Invalid manifest.json in ${path}: ${reason}`);
  }
}

export class UnsupportedFormatError extends PngtError {
  constructor(path: string, actualFormat: string) {
    super(`Unsupported format '${actualFormat}' in ${path} (expected 'pngt')`);
  }
}

export class UnsupportedVersionError extends PngtError {
  constructor(path: string, actualVersion: unknown, expectedVersion: number) {
    super(`Unsupported pngt version '${actualVersion}' in ${path} (expected '${expectedVersion}')`);
  }
}

export class MalformedSessionError extends PngtError {
  constructor(path: string, reason: string) {
    super(`Malformed session data in ${path}: ${reason}`);
  }
}

export class DriverNotFoundError extends PngtError {
  constructor(path: string, driverIndex: number) {
    super(`No telemetry found for driver_index ${driverIndex} in ${path}`);
  }
}
