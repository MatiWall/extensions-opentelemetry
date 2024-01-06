import logging
import sys
import threading

import opentelemetry.trace
import opentelemetry.metrics
from opentelemetry.sdk._logs import LoggingHandler
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource, ResourceAttributes
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from extensions.configuration import environment, hostname, service_namespace, service_name, service_version, service_instance

# Create a resource with OpenTelemetry attributes
_resources = Resource.create({
    ResourceAttributes.DEPLOYMENT_ENVIRONMENT: environment(),
    ResourceAttributes.HOST_NAME: hostname(),
    ResourceAttributes.SERVICE_NAMESPACE: service_namespace(),
    ResourceAttributes.SERVICE_NAME: service_name(),
    ResourceAttributes.SERVICE_VERSION: service_version(),
    ResourceAttributes.SERVICE_INSTANCE_ID: service_instance()
})

def exception_handler(exc_type, exc_value, exc_traceback):
    """Custom exception handler."""
    logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    # You can also add logic to report the exception to your observability system using OpenTelemetry

def configure_logging(
        handlers: list[logging.Handler] | None = None,
        level: int = logging.INFO,
        enable_otel: bool = False
):
    """Configure logging with optional OpenTelemetry integration."""
    if handlers is None:
        handlers = []

    # Set custom exception handlers
    sys.excepthook = exception_handler
    threading.excepthook = exception_handler

    # Console handler for basic logging
    console_handler = logging.StreamHandler()
    handlers.append(console_handler)
    # Configure root logger
    logging.basicConfig(
        level=level,
        handlers=handlers,
        force=True
    )

    if enable_otel:
        enable_opentelemetry_export()


def configure_otel_log_exporting():
    logger = logging.getLogger()
    provider = LoggerProvider(resource=_resources)
    provider.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter()))
    logger.addHandler(LoggingHandler(logger_provider=provider))

def configure_otel_trace_export():
    trace_provider = TracerProvider(resource=_resources)
    trace_exporter = OTLPSpanExporter()  # Update with your endpoint
    trace_provider.add_span_processor(BatchSpanProcessor(trace_exporter))

    opentelemetry.trace.set_tracer_provider(trace_provider)

def configure_otel_metrics_export():
    metric_exporter = OTLPMetricExporter()  # Update with your endpoint

    reader = PeriodicExportingMetricReader(
        exporter=metric_exporter,
        export_interval_millis=15_000
    )
    metric_provider = MeterProvider(resource=_resources, metric_readers=[reader])
    opentelemetry.metrics.set_meter_provider(metric_provider)

def enable_opentelemetry_export():
    configure_otel_log_exporting()
    configure_otel_trace_export()
    configure_otel_metrics_export()

# Example usage
if __name__ == "__main__":
    configure_logging(enable_otel=True)
    logger = logging.getLogger(__name__)

    # Log some messages
    logger.info("This is an informational message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
