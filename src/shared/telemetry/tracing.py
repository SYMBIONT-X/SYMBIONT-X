"""Distributed tracing for SYMBIONT-X."""

import os
from typing import Optional, Dict, Any
from contextlib import contextmanager
import time

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace import Status, StatusCode


class TracingManager:
    """Manages distributed tracing across SYMBIONT-X agents."""
    
    def __init__(self, service_name: str = "symbiont-x"):
        self.service_name = service_name
        self._tracer: Optional[trace.Tracer] = None
        self._initialized = False
    
    def initialize(
        self,
        service_name: Optional[str] = None,
        otlp_endpoint: Optional[str] = None,
    ):
        """Initialize the tracing provider."""
        
        if self._initialized:
            return
        
        service = service_name or self.service_name
        
        # Create resource
        resource = Resource.create({
            "service.name": service,
            "service.version": "1.0.0",
            "deployment.environment": os.getenv("ENVIRONMENT", "development"),
        })
        
        # Create tracer provider
        provider = TracerProvider(resource=resource)
        
        # Add exporters
        if otlp_endpoint:
            try:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
                otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
                provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            except Exception as e:
                print(f"OTLP exporter failed: {e}")
        
        # Always add console exporter in development
        if os.getenv("ENVIRONMENT", "development") == "development":
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        
        # Set global tracer provider
        trace.set_tracer_provider(provider)
        
        self._tracer = trace.get_tracer(service)
        self._initialized = True
    
    def get_tracer(self) -> trace.Tracer:
        """Get the tracer instance."""
        
        if not self._initialized:
            self.initialize()
        
        return self._tracer
    
    @contextmanager
    def span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
    ):
        """Create a traced span."""
        
        tracer = self.get_tracer()
        
        with tracer.start_as_current_span(name) as span:
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, str(value))
            
            try:
                yield span
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    def trace_agent_call(
        self,
        source_agent: str,
        target_agent: str,
        operation: str,
    ):
        """Decorator for tracing agent-to-agent calls."""
        
        def decorator(func):
            async def wrapper(*args, **kwargs):
                tracer = self.get_tracer()
                
                with tracer.start_as_current_span(
                    f"{source_agent}->{target_agent}:{operation}"
                ) as span:
                    span.set_attribute("source.agent", source_agent)
                    span.set_attribute("target.agent", target_agent)
                    span.set_attribute("operation", operation)
                    
                    start_time = time.time()
                    
                    try:
                        result = await func(*args, **kwargs)
                        span.set_status(Status(StatusCode.OK))
                        return result
                    except Exception as e:
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        span.record_exception(e)
                        raise
                    finally:
                        duration = time.time() - start_time
                        span.set_attribute("duration_seconds", duration)
            
            return wrapper
        return decorator


# Global tracing manager instance
tracing_manager = TracingManager()
