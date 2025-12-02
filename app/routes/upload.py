from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from typing import List
import pandas as pd
import io
from app.services.pdf_extractor import process_pdfs_directly

router = APIRouter(prefix="/api", tags=["upload"])

@router.post("/upload-pdfs")
async def upload_pdfs(
    files: List[UploadFile] = File(...),
    insurance_name: str = Form("Aetna"),
    output_format: str = Form("csv")
):
    """
    Upload multiple PDF files and extract data from them
    Returns file directly for download
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")
    
    # Validate files are PDFs
    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail=f"File {file.filename} is not a PDF")
    
    try:
        # Process PDFs directly without saving
        file_contents = []
        for file in files:
            content = await file.read()
            file_contents.append({
                "filename": file.filename,
                "content": content
            })
        
        # Process PDFs
        results = process_pdfs_directly(file_contents, insurance_name)
        
        # Create DataFrame
        df = pd.DataFrame(results)
        
        # Create output file in memory
        if output_format.lower() == "excel":
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Extracted_Data')
            output.seek(0)
            
            return StreamingResponse(
                output,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f"attachment; filename=extracted_data.xlsx"
                }
            )
        else:
            # Default to CSV
            csv_data = df.to_csv(index=False)
            
            return StreamingResponse(
                io.StringIO(csv_data),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=extracted_data.csv"
                }
            )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDFs: {str(e)}")