#!/usr/bin/env python3
"""Measure sequential download performance for a URL."""

from __future__ import annotations

import argparse
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass


DEFAULT_REQUEST_COUNT = 10
DEFAULT_TIMEOUT_SECONDS = 30.0
CHUNK_SIZE = 64 * 1024


@dataclass(frozen=True)
class Measurement:
    duration_seconds: float
    bytes_downloaded: int


def download_once(url: str, timeout: float) -> Measurement:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "internet-speed-test/1.0"},
    )
    started_at = time.perf_counter()
    bytes_downloaded = 0

    with urllib.request.urlopen(request, timeout=timeout) as response:
        while chunk := response.read(CHUNK_SIZE):
            bytes_downloaded += len(chunk)

    return Measurement(time.perf_counter() - started_at, bytes_downloaded)


def run_measurements(url: str, count: int, timeout: float) -> list[Measurement]:
    measurements: list[Measurement] = []
    for request_number in range(1, count + 1):
        measurement = download_once(url, timeout)
        measurements.append(measurement)
        print(
            f"Request {request_number}/{count}: "
            f"{measurement.duration_seconds:.3f} s, "
            f"{measurement.bytes_downloaded} bytes"
        )
    return measurements


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download a URL sequentially and report average request time and speed."
    )
    parser.add_argument("url", help="URL of the file or resource to download")
    parser.add_argument(
        "--count",
        type=int,
        default=DEFAULT_REQUEST_COUNT,
        help=f"number of sequential requests (default: {DEFAULT_REQUEST_COUNT})",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"timeout for each request in seconds (default: {DEFAULT_TIMEOUT_SECONDS:g})",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.count <= 0:
        print("Error: --count must be greater than zero.", file=sys.stderr)
        return 2
    if args.timeout <= 0:
        print("Error: --timeout must be greater than zero.", file=sys.stderr)
        return 2

    try:
        measurements = run_measurements(args.url, args.count, args.timeout)
    except (urllib.error.URLError, OSError, TimeoutError) as error:
        print(f"Request failed: {error}", file=sys.stderr)
        return 1

    total_duration = sum(item.duration_seconds for item in measurements)
    total_bytes = sum(item.bytes_downloaded for item in measurements)
    average_duration = total_duration / len(measurements)
    speed_mib_per_second = total_bytes / total_duration / (1024 * 1024)

    print("\nSummary")
    print(f"Average request time: {average_duration:.3f} s")
    print(f"Total downloaded: {total_bytes} bytes ({total_bytes / (1024 * 1024):.2f} MiB)")
    print(f"Download speed: {speed_mib_per_second:.2f} MiB/s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
