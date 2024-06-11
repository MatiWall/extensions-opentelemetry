import logging
logger = logging.getLogger(__name__)
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
from extensions.configuration import environment, hostname, service_namespace, service_name, service_version, service_instance # type: ignore

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
    """
    Custom exception handler.

    Parameters
    ----------
    exc_type : type
        The type of the exception.
    exc_value : Exception
        The exception instance.
    exc_traceback : traceback
        The traceback object.

    Returns
    -------
    None

    Notes
    -----
    You can also add logic to report the exception to your observability system using OpenTelemetry.
    """
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    # You can also add logic to report the exception to your observability system using OpenTelemetry

def configure_logging(
        handlers: list[logging.Handler] | None = None,
        level: int = logging.INFO,
        enable_otel: bool = False
):
    """
    Configure logging with optional OpenTelemetry integration.

    Parameters
    ----------
    handlers : list[logging.Handler] | None, optional
        List of logging handlers to be added, by default None.
    level : int, optional
        Logging level to be set, by default logging.INFO.
    enable_otel : bool, optional
        Flag to enable OpenTelemetry integration, by default False.

    Returns
    -------
    None

    Notes
    -----
    This function configures logging for the application. If `handlers` is not provided,
    a console handler is added by default. Custom exception handlers are set for
    uncaught exceptions in both the main thread and other threads. If `enable_otel`
    is True, OpenTelemetry integration is enabled.
    """
    if handlers is None:
        handlers = []

    # Set custom exception handlers
    sys.excepthook = exception_handler # type: ignore
    threading.excepthook = exception_handler # type: ignore

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
    """
    Configure OpenTelemetry logging exporting.

    This function configures the OpenTelemetry logging exporter to export logs.
    """
    logger = logging.getLogger()
    provider = LoggerProvider(resource=_resources)
    provider.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter()))
    logger.addHandler(LoggingHandler(logger_provider=provider))

def configure_otel_trace_export():
    """
    Configure OpenTelemetry trace exporting.

    This function configures the OpenTelemetry trace exporter to export traces.
    """
    trace_provider = TracerProvider(resource=_resources)
    trace_exporter = OTLPSpanExporter()  # Update with your endpoint
    trace_provider.add_span_processor(BatchSpanProcessor(trace_exporter))

    opentelemetry.trace.set_tracer_provider(trace_provider)

def configure_otel_metrics_export():
    """
    Configure OpenTelemetry metrics exporting.

    This function configures the OpenTelemetry metrics exporter to export metrics.
    """
    metric_exporter = OTLPMetricExporter()  # Update with your endpoint

    reader = PeriodicExportingMetricReader(
        exporter=metric_exporter,
        export_interval_millis=15_000
    )
    metric_provider = MeterProvider(resource=_resources, metric_readers=[reader])
    opentelemetry.metrics.set_meter_provider(metric_provider)

def enable_opentelemetry_export():
    """
    Enable OpenTelemetry exporting.

    This function enables exporting for OpenTelemetry logging, tracing, and metrics.
    """
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
