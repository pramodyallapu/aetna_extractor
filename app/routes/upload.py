from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from typing import List
import os
import pandas as pd
from app.services.pdf_extractor import process_pdfs, cleanup_files
import uuid

router = APIRouter(prefix="/api", tags=["upload"])

@router.post("/upload-pdfs")
async def upload_pdfs(
    files: List[UploadFile] = File(...),
    insurance_name: str = Form("Aetna")
):
    """
    Upload multiple PDF files and extract data from them
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")
    
    # Save uploaded files
    saved_files = []
    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail=f"File {file.filename} is not a PDF")
        
        file_id = str(uuid.uuid4())
        file_path = f"uploads/{file_id}_{file.filename}"
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        saved_files.append({
            "id": file_id,
            "original_name": file.filename,
            "path": file_path
        })
    
    try:
        # Process PDFs
        results = process_pdfs(saved_files, insurance_name)
        
        # Create DataFrame
        df = pd.DataFrame(results)
        
        # Generate output files
        output_id = str(uuid.uuid4())
        csv_path = f"output/output_{output_id}.csv"
        excel_path = f"output/output_{output_id}.xlsx"
        
        df.to_csv(csv_path, index=False)
        df.to_excel(excel_path, index=False)
        
        # Cleanup uploaded files
        cleanup_files(saved_files)
        
        return {
            "message": "PDFs processed successfully",
            "total_files": len(files),
            "output_files": {
                "csv": csv_path,
                "excel": excel_path
            },
            "data": results
        }
        
    except Exception as e:
        # Cleanup on error
        cleanup_files(saved_files)
        raise HTTPException(status_code=500, detail=f"Error processing PDFs: {str(e)}")

@router.get("/download/{file_type}/{file_id}")
async def download_file(file_type: str, file_id: str):
    """
    Download output files
    """
    if file_type == "csv":
        file_path = f"output/output_{file_id}.csv"
        media_type = "text/csv"
        filename = "extracted_data.csv"
    elif file_type == "excel":
        file_path = f"output/output_{file_id}.xlsx"
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = "extracted_data.xlsx"
    else:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename
    )