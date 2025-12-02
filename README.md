"# aetna_extractor" 
# PDF Extraction API

A FastAPI application for extracting data from insurance claim PDFs.

## Features

- Upload multiple PDF files simultaneously
- Extract key information including:
  - Practice Name
  - Check Number
  - Check Date
  - Claim Count
  - Line Count
  - Check Amount
- Download results as CSV or Excel files
- User-friendly web interface



# PDF Extraction API - Project Overview

## Executive Summary
The PDF Extraction API is a FastAPI-based web application designed to extract structured data from insurance claim PDF documents. The system processes multiple PDF files simultaneously, extracts key information including practice details, check numbers, claim counts, and financial data, and provides output in CSV and Excel formats.

## Business Problem
Insurance providers and healthcare organizations receive numerous claim documents in PDF format that contain critical financial and operational data. Manual extraction of this data is time-consuming, error-prone, and inefficient. This application automates the extraction process, improving accuracy and saving significant manual effort.

## Key Features
- **Multi-file Processing**: Upload and process multiple PDF files simultaneously
- **Intelligent Extraction**: Advanced text parsing with fallback mechanisms
- **Dual Output Formats**: Download results as CSV or Excel
- **Web Interface**: User-friendly drag-and-drop interface
- **API Access**: RESTful API for integration with other systems
- **Automatic Cleanup**: Temporary file management and cleanup

## Technology Stack
- **Backend**: FastAPI, Python 3.9+
- **PDF Processing**: pdfplumber, pypdf
- **Data Processing**: pandas, openpyxl
- **Frontend**: HTML5, CSS3, JavaScript
- **Deployment**: Uvicorn ASGI server

## Target Users
1. Insurance claim processors
2. Healthcare billing departments
3. Financial auditors
4. Data analysts
5. System integrators

## Success Metrics
- 90% reduction in manual data entry time
- 95% accuracy in data extraction
- Support for 100+ concurrent PDF uploads
- Sub-5 second processing time per PDF