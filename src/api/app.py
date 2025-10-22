"""FastAPI application with OpenAPI documentation for North Star Metrics."""

import asyncio
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..analysis.analysis_engine import AnalysisEngine
from ..config.environment_loader import get_current_environment, get_feature_flags
from ..data.unified_processor import UnifiedDataProcessor
from ..resilience.alerting import get_active_alerts, get_alert_summary
from ..resilience.monitoring import get_circuit_breaker_health
from ..structured_logging.structured_logger import get_structured_logger, set_correlation_id


# Pydantic models for API requests/responses
class ErrorDetail(BaseModel):
    """Detailed error information."""

    type: str = Field(..., description="Error type or category")
    message: str = Field(..., description="Human-readable error message")
    code: Optional[str] = Field(None, description="Error code for programmatic handling")
    field: Optional[str] = Field(None, description="Field name for validation errors")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class ErrorResponse(BaseModel):
    """Structured error response."""

    error: str = Field(..., description="Error summary")
    message: str = Field(..., description="Detailed error message")
    correlation_id: Optional[str] = Field(None, description="Request correlation ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    path: Optional[str] = Field(None, description="Request path that caused the error")
    details: Optional[List[ErrorDetail]] = Field(None, description="Detailed error information")
    suggestion: Optional[str] = Field(None, description="Suggested resolution")


class AnalysisRequest(BaseModel):
    """Request model for analysis operations."""

    organization: str = Field(..., description="GitHub organization name", example="mycompany")
    days: int = Field(7, ge=1, le=365, description="Number of days to analyze")
    include_commits: bool = Field(True, description="Include commit analysis")
    include_prs: bool = Field(True, description="Include PR analysis")
    repositories: Optional[List[str]] = Field(None, description="Specific repositories to analyze")


class AnalysisResponse(BaseModel):
    """Response model for analysis operations."""

    analysis_id: str = Field(..., description="Unique analysis identifier")
    status: str = Field(..., description="Analysis status")
    organization: str = Field(..., description="Organization analyzed")
    total_records: int = Field(..., description="Total records processed")
    processing_time_seconds: float = Field(..., description="Processing time in seconds")
    results_file: Optional[str] = Field(None, description="Path to results file")


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str = Field(..., description="Service status")
    environment: str = Field(..., description="Current environment")
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(..., description="Health check timestamp")
    dependencies: Dict[str, str] = Field(..., description="Dependency health status")


class MetricsResponse(BaseModel):
    """Response model for metrics."""

    circuit_breakers: Dict[str, Any] = Field(..., description="Circuit breaker status")
    active_alerts: List[Dict[str, Any]] = Field(..., description="Active alerts")
    alert_summary: Dict[str, Any] = Field(..., description="Alert summary")


class PilotRequest(BaseModel):
    """Request model for pilot analysis."""

    organization: str = Field(..., description="GitHub organization name")
    test_repositories: Optional[List[str]] = Field(None, description="Test repositories for pilot")


# Background task storage (in production, use a proper task queue)
background_tasks = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger = get_structured_logger("api.startup")
    logger.info("Starting North Star Metrics API")

    # Verify configuration
    from ..config.environment_loader import validate_environment

    validation = validate_environment()

    if validation["errors"]:
        logger.error("Configuration validation failed", extra={"errors": validation["errors"]})
        raise RuntimeError("Invalid configuration")

    if validation["warnings"]:
        logger.warning("Configuration warnings", extra={"warnings": validation["warnings"]})

    yield

    # Shutdown
    logger.info("Shutting down North Star Metrics API")


# Create FastAPI app
app = FastAPI(
    title="North Star Metrics API",
    description="""
    ## Engineering Impact Analytics API
    
    North Star Metrics provides AI-powered analysis of engineering work across organizations.
    It analyzes GitHub repositories and Pull Requests to generate insights about:
    
    - **Work Type Classification**: Automatically categorizes changes as features, bugs, refactoring, etc.
    - **Impact Scoring**: Measures complexity, risk, and clarity of code changes
    - **Linear Integration**: Correlates code changes with planned work tickets
    - **Developer Metrics**: Tracks individual and team performance patterns
    - **Process Insights**: Identifies workflow improvement opportunities
    
    ### Quick Start
    
    1. **Health Check**: GET `/health` to verify the service is running
    2. **Pilot Analysis**: POST `/analysis/pilot` to run a 7-day trial
    3. **Full Analysis**: POST `/analysis/run` for comprehensive analysis
    4. **Monitor**: GET `/metrics` to view system health and alerts
    
    ### Authentication
    
    API keys are required for analysis operations. Set the following environment variables:
    - `ANTHROPIC_API_KEY`: For AI analysis
    - `GITHUB_TOKEN`: For repository access  
    - `LINEAR_API_KEY`: For ticket correlation (optional)
    """,
    version="1.0.0",
    contact={
        "name": "North Star Metrics Support",
        "email": "support@northstarmetrics.dev",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan,
    servers=[
        {"url": "https://api.northstarmetrics.dev", "description": "Production server"},
        {"url": "https://staging-api.northstarmetrics.dev", "description": "Staging server"},
        {"url": "http://localhost:8000", "description": "Development server"},
    ],
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_correlation_id(request, call_next):
    """Add correlation ID to requests."""
    correlation_id = set_correlation_id()
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    logger = get_structured_logger("api.validation_error")
    correlation_id = request.headers.get("X-Correlation-ID")

    error_details = []
    for error in exc.errors():
        error_details.append(
            ErrorDetail(
                type="validation_error",
                message=error["msg"],
                code=error["type"],
                field=".".join(str(loc) for loc in error["loc"]),
                details={"input": error.get("input")},
            )
        )

    error_response = ErrorResponse(
        error="Validation Error",
        message="Request validation failed",
        correlation_id=correlation_id,
        path=str(request.url.path),
        details=error_details,
        suggestion="Please check your request parameters and try again",
    )

    logger.warning(
        "Request validation failed",
        extra={
            "path": str(request.url.path),
            "errors": [detail.dict() for detail in error_details],
        },
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=error_response.dict()
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions."""
    logger = get_structured_logger("api.http_error")
    correlation_id = request.headers.get("X-Correlation-ID")

    # Map common status codes to user-friendly messages
    status_messages = {
        404: "The requested resource was not found",
        401: "Authentication is required",
        403: "Access to this resource is forbidden",
        429: "Too many requests. Please try again later",
        500: "An internal server error occurred",
        503: "Service is temporarily unavailable",
    }

    suggestions = {
        404: "Please check the URL and try again",
        401: "Please provide valid authentication credentials",
        403: "Please contact support if you believe you should have access",
        429: "Please wait before making additional requests",
        500: "Please try again later or contact support",
        503: "Please try again in a few moments",
    }

    error_response = ErrorResponse(
        error=f"HTTP {exc.status_code}",
        message=status_messages.get(exc.status_code, str(exc.detail)),
        correlation_id=correlation_id,
        path=str(request.url.path),
        suggestion=suggestions.get(exc.status_code),
    )

    logger.error(
        f"HTTP {exc.status_code} error",
        extra={
            "status_code": exc.status_code,
            "path": str(request.url.path),
            "detail": str(exc.detail),
        },
    )

    return JSONResponse(status_code=exc.status_code, content=error_response.dict())


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger = get_structured_logger("api.unexpected_error")
    correlation_id = request.headers.get("X-Correlation-ID")

    error_response = ErrorResponse(
        error="Internal Server Error",
        message="An unexpected error occurred while processing your request",
        correlation_id=correlation_id,
        path=str(request.url.path),
        suggestion="Please try again later or contact support if the problem persists",
    )

    logger.error(
        "Unexpected error occurred",
        extra={
            "path": str(request.url.path),
            "error_type": type(exc).__name__,
            "error_message": str(exc),
        },
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=error_response.dict()
    )


def get_logger():
    """Dependency to get logger with correlation ID."""
    return get_structured_logger("api")


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Check the health status of the North Star Metrics service and its dependencies",
    tags=["Health"],
)
async def health_check(logger=Depends(get_logger)):
    """Comprehensive health check endpoint."""
    logger.info("Health check requested")

    # Check dependencies
    dependencies = {}

    try:
        # Test configuration loading
        from ..config.config_manager import ConfigManager

        _config_manager = ConfigManager()  # noqa: F841
        dependencies["configuration"] = "healthy"
    except Exception as e:
        dependencies["configuration"] = f"unhealthy: {str(e)}"

    try:
        # Test analysis engine
        _analysis_engine = AnalysisEngine()  # noqa: F841
        dependencies["analysis_engine"] = "healthy"
    except Exception as e:
        dependencies["analysis_engine"] = f"unhealthy: {str(e)}"

    try:
        # Test circuit breakers
        cb_health = get_circuit_breaker_health()
        dependencies["circuit_breakers"] = cb_health["overall_health"]
    except Exception as e:
        dependencies["circuit_breakers"] = f"unhealthy: {str(e)}"

    # Determine overall status
    unhealthy_deps = [dep for dep, status in dependencies.items() if "unhealthy" in status]
    overall_status = "unhealthy" if unhealthy_deps else "healthy"

    response = HealthResponse(
        status=overall_status,
        environment=get_current_environment(),
        version="1.0.0",
        timestamp=datetime.now(),
        dependencies=dependencies,
    )

    status_code = (
        status.HTTP_503_SERVICE_UNAVAILABLE if overall_status == "unhealthy" else status.HTTP_200_OK
    )

    logger.info(
        "Health check completed",
        extra={"status": overall_status, "unhealthy_dependencies": unhealthy_deps},
    )

    return JSONResponse(content=response.dict(), status_code=status_code)


@app.get(
    "/metrics",
    response_model=MetricsResponse,
    summary="System Metrics",
    description="Get system metrics including circuit breakers and alerts",
    tags=["Monitoring"],
)
async def get_metrics(logger=Depends(get_logger)):
    """Get system metrics and monitoring data."""
    logger.info("Metrics requested")

    try:
        circuit_breaker_health = get_circuit_breaker_health()
        active_alerts = get_active_alerts()
        alert_summary = get_alert_summary()

        return MetricsResponse(
            circuit_breakers=circuit_breaker_health,
            active_alerts=active_alerts,
            alert_summary=alert_summary,
        )
    except Exception as e:
        logger.error("Failed to get metrics", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")


@app.post(
    "/analysis/pilot",
    response_model=AnalysisResponse,
    summary="Pilot Analysis",
    description="Run a 7-day pilot analysis to validate the system with a small dataset",
    tags=["Analysis"],
)
async def run_pilot_analysis(
    request: PilotRequest, background_tasks: BackgroundTasks, logger=Depends(get_logger)
):
    """Run pilot analysis for an organization."""
    logger.info("Pilot analysis requested", extra={"organization": request.organization})

    # Generate analysis ID
    analysis_id = f"pilot_{request.organization}_{int(time.time())}"

    # Add background task
    background_tasks.add_task(
        _run_analysis_task,
        analysis_id,
        request.organization,
        7,  # Pilot is always 7 days
        request.test_repositories,
    )

    # Store task info
    background_tasks[analysis_id] = {
        "status": "started",
        "organization": request.organization,
        "type": "pilot",
        "started_at": datetime.now(),
    }

    return AnalysisResponse(
        analysis_id=analysis_id,
        status="started",
        organization=request.organization,
        total_records=0,
        processing_time_seconds=0.0,
    )


@app.post(
    "/analysis/run",
    response_model=AnalysisResponse,
    summary="Full Analysis",
    description="Run comprehensive analysis for an organization",
    tags=["Analysis"],
)
async def run_analysis(
    request: AnalysisRequest, background_tasks: BackgroundTasks, logger=Depends(get_logger)
):
    """Run full analysis for an organization."""
    logger.info(
        "Full analysis requested",
        extra={"organization": request.organization, "days": request.days},
    )

    # Generate analysis ID
    analysis_id = f"analysis_{request.organization}_{int(time.time())}"

    # Add background task
    background_tasks.add_task(
        _run_analysis_task, analysis_id, request.organization, request.days, request.repositories
    )

    # Store task info
    background_tasks[analysis_id] = {
        "status": "started",
        "organization": request.organization,
        "type": "full",
        "days": request.days,
        "started_at": datetime.now(),
    }

    return AnalysisResponse(
        analysis_id=analysis_id,
        status="started",
        organization=request.organization,
        total_records=0,
        processing_time_seconds=0.0,
    )


@app.get(
    "/analysis/{analysis_id}/status",
    summary="Analysis Status",
    description="Get the status of a running or completed analysis",
    tags=["Analysis"],
)
async def get_analysis_status(analysis_id: str, logger=Depends(get_logger)):
    """Get status of an analysis task."""
    logger.info("Analysis status requested", extra={"analysis_id": analysis_id})

    if analysis_id not in background_tasks:
        raise HTTPException(status_code=404, detail="Analysis not found")

    task_info = background_tasks[analysis_id]
    return JSONResponse(content=task_info)


@app.get(
    "/environments/current",
    summary="Current Environment",
    description="Get information about the current environment and feature flags",
    tags=["Configuration"],
)
async def get_current_environment_info(logger=Depends(get_logger)):
    """Get current environment information."""
    logger.info("Environment info requested")

    environment = get_current_environment()
    feature_flags = get_feature_flags()

    return {"environment": environment, "feature_flags": feature_flags}


async def _run_analysis_task(
    analysis_id: str, organization: str, days: int, repositories: Optional[List[str]] = None
):
    """Background task to run analysis."""
    logger = get_structured_logger("api.analysis_task")
    logger.info(
        "Starting analysis task",
        extra={"analysis_id": analysis_id, "organization": organization, "days": days},
    )

    start_time = time.time()

    try:
        # Update status
        background_tasks[analysis_id]["status"] = "processing"

        # Initialize components
        _analysis_engine = AnalysisEngine()  # noqa: F841
        _processor = UnifiedDataProcessor()  # noqa: F841

        # Run analysis (simplified for demo)
        # In production, this would call the actual analysis pipeline
        await asyncio.sleep(2)  # Simulate processing time

        # Update status
        processing_time = time.time() - start_time
        background_tasks[analysis_id].update(
            {
                "status": "completed",
                "total_records": 150,  # Mock data
                "processing_time_seconds": processing_time,
                "completed_at": datetime.now(),
                "results_file": f"analysis_results_{analysis_id}.csv",
            }
        )

        logger.info(
            "Analysis task completed",
            extra={"analysis_id": analysis_id, "processing_time_seconds": processing_time},
        )

    except Exception as e:
        logger.error("Analysis task failed", extra={"analysis_id": analysis_id, "error": str(e)})

        background_tasks[analysis_id].update(
            {"status": "failed", "error": str(e), "failed_at": datetime.now()}
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.api.app:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
