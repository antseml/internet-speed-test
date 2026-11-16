#!/usr/bin/env node

const { performance } = require("node:perf_hooks");

const DEFAULT_REQUEST_COUNT = 10;
const DEFAULT_TIMEOUT_SECONDS = 30;
const BYTES_IN_MIB = 1024 * 1024;

function printUsage() {
  console.log(`Usage: node speed_test.js URL [--count NUMBER] [--timeout SECONDS]

Options:
  --count NUMBER     number of sequential requests (default: 10)
  --timeout SECONDS  timeout for each request (default: 30)
  -h, --help         show this help message`);
}

function parseArguments(args) {
  if (args.includes("-h") || args.includes("--help")) {
    printUsage();
    return null;
  }

  const options = {
    url: null,
    count: DEFAULT_REQUEST_COUNT,
    timeout: DEFAULT_TIMEOUT_SECONDS,
  };

  for (let index = 0; index < args.length; index += 1) {
    const argument = args[index];
    if (argument === "--count" || argument === "--timeout") {
      const value = Number(args[index + 1]);
      if (!Number.isFinite(value) || value <= 0) {
        throw new Error(`${argument} must be greater than zero`);
      }
      if (argument === "--count" && !Number.isInteger(value)) {
        throw new Error("--count must be an integer");
      }
      options[argument.slice(2)] = value;
      index += 1;
    } else if (argument.startsWith("--")) {
      throw new Error(`unknown option: ${argument}`);
    } else if (options.url === null) {
      options.url = argument;
    } else {
      throw new Error(`unexpected argument: ${argument}`);
    }
  }

  if (options.url === null) {
    throw new Error("URL is required");
  }

  try {
    new URL(options.url);
  } catch {
    throw new Error("invalid URL");
  }

  return options;
}

async function downloadOnce(url, timeoutSeconds) {
  const startedAt = performance.now();
  const response = await fetch(url, {
    headers: { "User-Agent": "internet-speed-test/1.0" },
    signal: AbortSignal.timeout(timeoutSeconds * 1000),
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status} ${response.statusText}`);
  }

  let bytesDownloaded = 0;
  for await (const chunk of response.body) {
    bytesDownloaded += chunk.byteLength;
  }

  return {
    durationSeconds: (performance.now() - startedAt) / 1000,
    bytesDownloaded,
  };
}

async function main() {
  let options;
  try {
    options = parseArguments(process.argv.slice(2));
  } catch (error) {
    console.error(`Error: ${error.message}`);
    printUsage();
    process.exitCode = 2;
    return;
  }

  if (options === null) {
    return;
  }

  const measurements = [];
  try {
    for (let requestNumber = 1; requestNumber <= options.count; requestNumber += 1) {
      const measurement = await downloadOnce(options.url, options.timeout);
      measurements.push(measurement);
      console.log(
        `Request ${requestNumber}/${options.count}: ` +
          `${measurement.durationSeconds.toFixed(3)} s, ` +
          `${measurement.bytesDownloaded} bytes`,
      );
    }
  } catch (error) {
    console.error(`Request failed: ${error.message}`);
    process.exitCode = 1;
    return;
  }

  const totalDuration = measurements.reduce(
    (sum, measurement) => sum + measurement.durationSeconds,
    0,
  );
  const totalBytes = measurements.reduce(
    (sum, measurement) => sum + measurement.bytesDownloaded,
    0,
  );
  const averageDuration = totalDuration / measurements.length;
  const speedMibPerSecond = totalBytes / totalDuration / BYTES_IN_MIB;

  console.log("\nSummary");
  console.log(`Average request time: ${averageDuration.toFixed(3)} s`);
  console.log(
    `Total downloaded: ${totalBytes} bytes (${(totalBytes / BYTES_IN_MIB).toFixed(2)} MiB)`,
  );
  console.log(`Download speed: ${speedMibPerSecond.toFixed(2)} MiB/s`);
}

main();
