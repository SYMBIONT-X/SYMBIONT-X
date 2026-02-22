#!/usr/bin/env python3
"""Load testing script for SYMBIONT-X APIs."""

import asyncio
import time
import statistics
from typing import List, Dict, Any
from dataclasses import dataclass
import argparse

import httpx


@dataclass
class RequestResult:
    """Result of a single request."""
    endpoint: str
    status_code: int
    duration_ms: float
    success: bool
    error: str = None


class LoadTester:
    """Simple load tester for SYMBIONT-X."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[RequestResult] = []
    
    async def make_request(
        self,
        client: httpx.AsyncClient,
        method: str,
        endpoint: str,
        data: Dict = None,
    ) -> RequestResult:
        """Make a single request and record result."""
        
        url = f"{self.base_url}{endpoint}"
        start = time.perf_counter()
        
        try:
            if method == "GET":
                response = await client.get(url)
            elif method == "POST":
                response = await client.post(url, json=data or {})
            else:
                response = await client.request(method, url, json=data)
            
            duration = (time.perf_counter() - start) * 1000
            
            return RequestResult(
                endpoint=endpoint,
                status_code=response.status_code,
                duration_ms=round(duration, 2),
                success=response.status_code < 400,
            )
            
        except Exception as e:
            duration = (time.perf_counter() - start) * 1000
            return RequestResult(
                endpoint=endpoint,
                status_code=0,
                duration_ms=round(duration, 2),
                success=False,
                error=str(e),
            )
    
    async def run_concurrent(
        self,
        endpoints: List[tuple],
        concurrency: int = 10,
        total_requests: int = 100,
    ):
        """Run concurrent requests."""
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            tasks = []
            
            for i in range(total_requests):
                method, endpoint, data = endpoints[i % len(endpoints)]
                tasks.append(self.make_request(client, method, endpoint, data))
                
                # Batch execution
                if len(tasks) >= concurrency:
                    results = await asyncio.gather(*tasks)
                    self.results.extend(results)
                    tasks = []
            
            # Remaining tasks
            if tasks:
                results = await asyncio.gather(*tasks)
                self.results.extend(results)
    
    def get_report(self) -> Dict[str, Any]:
        """Generate load test report."""
        
        if not self.results:
            return {"error": "No results"}
        
        durations = [r.duration_ms for r in self.results]
        success_count = sum(1 for r in self.results if r.success)
        
        # Group by endpoint
        by_endpoint = {}
        for r in self.results:
            if r.endpoint not in by_endpoint:
                by_endpoint[r.endpoint] = []
            by_endpoint[r.endpoint].append(r)
        
        endpoint_stats = {}
        for endpoint, results in by_endpoint.items():
            ep_durations = [r.duration_ms for r in results]
            endpoint_stats[endpoint] = {
                "count": len(results),
                "success_rate": sum(1 for r in results if r.success) / len(results) * 100,
                "avg_ms": round(statistics.mean(ep_durations), 2),
                "p95_ms": round(sorted(ep_durations)[int(len(ep_durations) * 0.95)], 2),
            }
        
        return {
            "total_requests": len(self.results),
            "successful": success_count,
            "failed": len(self.results) - success_count,
            "success_rate": round(success_count / len(self.results) * 100, 2),
            "duration": {
                "avg_ms": round(statistics.mean(durations), 2),
                "min_ms": round(min(durations), 2),
                "max_ms": round(max(durations), 2),
                "p50_ms": round(statistics.median(durations), 2),
                "p95_ms": round(sorted(durations)[int(len(durations) * 0.95)], 2),
                "p99_ms": round(sorted(durations)[int(len(durations) * 0.99)], 2),
            },
            "by_endpoint": endpoint_stats,
        }


async def main():
    parser = argparse.ArgumentParser(description="SYMBIONT-X Load Tester")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL")
    parser.add_argument("--concurrency", "-c", type=int, default=10, help="Concurrent requests")
    parser.add_argument("--requests", "-n", type=int, default=100, help="Total requests")
    args = parser.parse_args()
    
    print(f"\n🚀 SYMBIONT-X Load Test")
    print(f"   URL: {args.url}")
    print(f"   Concurrency: {args.concurrency}")
    print(f"   Total Requests: {args.requests}")
    print("-" * 50)
    
    # Define test endpoints
    endpoints = [
        ("GET", "/health", None),
        ("GET", "/agents", None),
        ("GET", "/workflows", None),
        ("GET", "/monitoring/metrics/summary", None),
        ("GET", "/hitl/approvals/pending", None),
    ]
    
    tester = LoadTester(args.url)
    
    start = time.perf_counter()
    await tester.run_concurrent(endpoints, args.concurrency, args.requests)
    total_time = time.perf_counter() - start
    
    report = tester.get_report()
    
    print(f"\n📊 Results ({total_time:.2f}s)")
    print("-" * 50)
    print(f"Total Requests:  {report['total_requests']}")
    print(f"Successful:      {report['successful']}")
    print(f"Failed:          {report['failed']}")
    print(f"Success Rate:    {report['success_rate']}%")
    print(f"\n⏱️  Response Times")
    print(f"   Average:  {report['duration']['avg_ms']}ms")
    print(f"   P50:      {report['duration']['p50_ms']}ms")
    print(f"   P95:      {report['duration']['p95_ms']}ms")
    print(f"   P99:      {report['duration']['p99_ms']}ms")
    print(f"   Min:      {report['duration']['min_ms']}ms")
    print(f"   Max:      {report['duration']['max_ms']}ms")
    
    print(f"\n📍 By Endpoint")
    for endpoint, stats in report["by_endpoint"].items():
        print(f"   {endpoint}")
        print(f"      Count: {stats['count']}, Avg: {stats['avg_ms']}ms, P95: {stats['p95_ms']}ms")
    
    # Calculate throughput
    rps = report['total_requests'] / total_time
    print(f"\n🔥 Throughput: {rps:.2f} requests/second")
    
    print("-" * 50)
    print("✅ Load test complete\n")


if __name__ == "__main__":
    asyncio.run(main())
