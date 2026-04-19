import asyncio
import time

import httpx
from fastmcp import FastMCP

mcp = FastMCP("Perf Server", instructions="A performance testing utility server.")


async def _run_perf_test(
    url: str = "http://localhost:58080",
    num_requests: int = 100,
    concurrency: int = 10,
) -> dict:
    """Run a load test against a URL with concurrent requests.

    Args:
        url: The target URL to test.
        num_requests: Total number of requests to send.
        concurrency: Number of concurrent requests.
    """
    latencies = []
    errors = 0
    status_codes = {}

    semaphore = asyncio.Semaphore(concurrency)

    async def send_request(client: httpx.AsyncClient):
        nonlocal errors
        async with semaphore:
            start = time.perf_counter()
            try:
                response = await client.get(url)
                elapsed = (time.perf_counter() - start) * 1000
                latencies.append(elapsed)
                code = response.status_code
                status_codes[code] = status_codes.get(code, 0) + 1
            except Exception:
                errors += 1

    async with httpx.AsyncClient(timeout=30) as client:
        overall_start = time.perf_counter()
        tasks = [send_request(client) for _ in range(num_requests)]
        await asyncio.gather(*tasks)
        overall_elapsed = (time.perf_counter() - overall_start) * 1000

    if not latencies:
        return {"error": "All requests failed", "total_errors": errors}

    sorted_latencies = sorted(latencies)
    successful = len(latencies)

    return {
        "url": url,
        "total_requests": num_requests,
        "successful_requests": successful,
        "failed_requests": errors,
        "concurrency": concurrency,
        "total_time_ms": round(overall_elapsed, 2),
        "requests_per_second": round(successful / (overall_elapsed / 1000), 2),
        "latency_ms": {
            "min": round(sorted_latencies[0], 2),
            "max": round(sorted_latencies[-1], 2),
            "mean": round(sum(sorted_latencies) / successful, 2),
            "median": round(sorted_latencies[successful // 2], 2),
            "p95": round(sorted_latencies[int(successful * 0.95)], 2),
            "p99": round(sorted_latencies[int(successful * 0.99)], 2),
        },
        "status_codes": status_codes,
    }


mcp.tool()(_run_perf_test)

perf_tools = [_run_perf_test]
