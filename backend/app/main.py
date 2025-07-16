import os
import shutil
import uuid
import logging
import zipfile
from pathlib import Path
from typing import List, Optional, Dict, Any

from fastapi import (
    FastAPI, 
    File, 
    UploadFile, 
    Form, 
    Depends, 
    HTTPException, 
    BackgroundTasks,
    status,
    Query
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from contextlib import contextmanager

from . import crud, models, schemas, services
from .database import get_db, init_db, Base

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the database when the module is imported
init_db()

# Create upload directory
UPLOAD_DIR = Path("/tmp/pyconnect_uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Create FastAPI app
app = FastAPI(
    title="Py-Connect API",
    description="Backend API for Py-Connect application deployment",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database session dependency
@contextmanager
def get_db_session():
    """Get a database session with proper cleanup."""
    db = next(get_db())
    try:
        yield db
    finally:
        if db.is_active:
            db.close()

def deploy_in_background(content_id: int, zip_path: Path) -> None:
    """
    Background task to handle app deployment.
    
    Args:
        content_id: ID of the content to deploy
        zip_path: Path to the uploaded zip file
    """
    with get_db_session() as db:
        try:
            # Get the content item
            db_content = crud.get_content(db, content_id)
            if not db_content:
                logger.error(f"Content with ID {content_id} not found")
                return

            try:
                # Update status to 'deploying'
                db_content = crud.update_content_status(
                    db=db,
                    content_id=content_id,
                    status="deploying"
                )
                
                if not db_content:
                    logger.error(f"Failed to update status for content_id {content_id}")
                    return
                
                # Build and run the app (blocking call)
                container_id, host_port = services.build_and_run_app(db_content, zip_path)
                
                # Update status to 'running' with container info
                db_content = crud.update_content_status(
                    db=db,
                    content_id=content_id,
                    status="running",
                    container_id=container_id,
                    internal_port=host_port
                )
                
                logger.info(f"Successfully deployed {db_content.name}. Container: {container_id}, Port: {host_port}")
                
            except Exception as e:
                # Update status to 'error' if deployment fails
                logger.error(f"Error during deployment for content_id {content_id}: {str(e)}", exc_info=True)
                try:
                    crud.update_content_status(
                        db=db,
                        content_id=content_id,
                        status="error"
                    )
                except Exception as db_error:
                    logger.error(f"Failed to update status to error: {str(db_error)}", exc_info=True)
                raise
                
        except Exception as e:
            logger.error(f"Unexpected error in deploy_in_background for content_id {content_id}: {str(e)}", exc_info=True)
            
        finally:
            # Clean up the uploaded file
            try:
                if zip_path.exists():
                    zip_path.unlink()
                    logger.info(f"Cleaned up file: {zip_path}")
            except Exception as e:
                logger.error(f"Error cleaning up file {zip_path}: {str(e)}", exc_info=True)

@app.post(
    "/api/publish",
    response_model=schemas.ContentInDB,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        400: {"description": "Content with this name already exists"},
        422: {"description": "Validation error"},
        500: {"description": "Failed to process upload"}
    }
)
async def publish_content(
    background_tasks: BackgroundTasks,
    name: str = Form(..., min_length=1, max_length=100),
    description: Optional[str] = Form(None, max_length=500),
    app_bundle: UploadFile = File(..., description="ZIP file containing the application code"),
    db: Session = Depends(get_db)
):
    """
    Upload and deploy a new application.
    
    - **name**: Name of the application (must be unique, 1-100 chars)
    - **description**: Optional description (max 500 chars)
    - **app_bundle**: ZIP file containing the application code and Dockerfile
    """
    # Check file extension
    if not app_bundle.filename.lower().endswith('.zip'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .zip files are allowed"
        )
    
    # Check if content with this name already exists
    if crud.get_content_by_name(db, name=name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content with this name already exists"
        )

    # Save uploaded file to temporary location
    zip_path = UPLOAD_DIR / f"{uuid.uuid4()}.zip"
    
    try:
        # Save the uploaded file
        with zip_path.open("wb") as buffer:
            shutil.copyfileobj(app_bundle.file, buffer)
        
        # Verify it's a valid zip file
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                if 'Dockerfile' not in zip_ref.namelist():
                    raise ValueError("ZIP file must contain a Dockerfile in the root directory")
        except zipfile.BadZipFile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ZIP file"
            )
            
        # Create content item in database
        content_data = schemas.ContentCreate(
            name=name,
            description=description
        )
        
        content = crud.create_content(db=db, content=content_data)
        
        # Start background task for deployment
        background_tasks.add_task(
            deploy_in_background,
            content_id=content.id,
            zip_path=zip_path
        )

        return content
        
    except HTTPException:
        raise
    except Exception as e:
        # Clean up the file if it was created
        if zip_path.exists():
            try:
                zip_path.unlink()
            except Exception as cleanup_error:
                logger.error(f"Error cleaning up file {zip_path}: {str(cleanup_error)}")
                
        logger.error(f"Error processing upload: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process upload: {str(e)}"
        )

@app.get(
    "/api/content",
    response_model=List[schemas.ContentInDB],
    summary="List all content items",
    description="Get a list of all deployed content with pagination"
)
def list_content(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of items to return (max 100)"),
    db: Session = Depends(get_db)
):
    """
    Get a list of all content items with pagination.
    
    - **skip**: Number of items to skip (for pagination)
    - **limit**: Maximum number of items to return (1-100)
    """
    try:
        return crud.get_all_content(db, skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"Error listing content: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve content list"
        )

@app.get(
    "/api/content/{content_id}",
    response_model=schemas.ContentInDB,
    responses={
        404: {"description": "Content not found"},
        422: {"description": "Validation error"}
    }
)
def get_content(
    content_id: int = Path(description="ID of the content to retrieve", gt=0),
    db: Session = Depends(get_db)
):
    """
    Get a specific content item by ID.
    
    - **content_id**: ID of the content to retrieve (must be a positive integer)
    """
    try:
        content = crud.get_content(db, content_id=content_id)
        if content is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )
        return content
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving content {content_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve content"
        )

@app.delete(
    "/api/content/{content_id}",
    status_code=status.HTTP_200_OK,
    response_model=Dict[str, str],
    responses={
        404: {"description": "Content not found"},
        500: {"description": "Error deleting content"},
        422: {"description": "Validation error"}
    }
)
def delete_content(
    content_id: int = Path(description="ID of the content to delete", gt=0),
    db: Session = Depends(get_db)
):
    """
    Delete a content item and its associated container.
    
    - **content_id**: ID of the content to delete (must be a positive integer)
    """
    try:
        content = crud.get_content(db, content_id=content_id)
        if content is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )
        
        # Stop and remove the container if it's running
        if content.container_id:
            try:
                services.stop_and_remove_container(content.container_id)
            except Exception as e:
                logger.error(f"Error stopping container {content.container_id}: {str(e)}", exc_info=True)
                # Don't fail the request if container cleanup fails
        
        # Delete the content from the database
        try:
            crud.delete_content(db, content_id=content_id)
            return {"message": "Content deleted successfully"}
        except Exception as e:
            logger.error(f"Error deleting content {content_id}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete content from database"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error deleting content {content_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while deleting the content"
        )

@app.get(
    "/health", 
    status_code=status.HTTP_200_OK,
    response_model=Dict[str, str],
    summary="Health Check",
    description="Health check endpoint for monitoring"
)
async def health_check():
    """
    Health check endpoint for monitoring.
    
    Returns:
        A simple status message indicating the service is running
    """
    return {"status": "ok", "service": "py-connect-backend"}

# Add startup event to ensure upload directory exists
@app.on_event("startup")
async def startup_event():
    """Initialize resources when the application starts."""
    try:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Upload directory ready at {UPLOAD_DIR}")
    except Exception as e:
        logger.error(f"Failed to create upload directory: {str(e)}")
        raise

# Add shutdown event to clean up resources
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources when the application shuts down."""
    logger.info("Shutting down py-connect-backend...")
