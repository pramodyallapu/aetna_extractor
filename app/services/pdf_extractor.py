import pdfplumber
import re
import pandas as pd
import io
from math import isfinite
from typing import List, Dict
from pypdf import PdfReader

def reverse_if_indicated(line: str) -> str:
    indicators = ['tnuomA', 'egaP', 'tnemyaP', 'detnirP', 'rebmuN']
    lw = line.lower()
    for ind in indicators:
        if ind in lw:
            return line[::-1]
    return line

def normalize_number_string(s: str) -> str:
    s = s.strip().replace('$', '').replace('USD', '').replace(' ', '').replace(',', '')
    if s.count('.') > 1:
        parts = s.split('.')
        s = ''.join(parts[:-1]) + '.' + parts[-1]
    return s

def try_parse_amount_candidates(num_str: str):
    candidates = []
    s1 = normalize_number_string(num_str)
    try:
        candidates.append(('orig', float(s1)))
    except:
        pass
    srev = normalize_number_string(num_str[::-1])
    try:
        candidates.append(('rev', float(srev)))
    except:
        pass
    if not candidates:
        return None, None
    if len(candidates) == 1:
        return candidates[0][1], candidates[0][0]
    return max(candidates, key=lambda x: x[1])[1], max(candidates, key=lambda x: x[1])[0]

def extract_amount_from_line(line: str):
    tokens = re.findall(r'[$]?\s*[0-9][0-9,\.]{1,}\d', line)
    for tok in tokens:
        tok = re.sub(r'[^\d.,]+', '', tok)
        tok = re.sub(r'[^\d.,]+$', '', tok)
        val, src = try_parse_amount_candidates(tok)
        if val is not None:
            return round(val, 2), src
    return None, None

def extract_long_numeric_token(line: str):
    m = re.findall(r'\b\d{5,}\b', line)
    return m[0] if m else None

def is_table_header(line: str):
    header_tokens = ['SERVICE', 'PL', 'NUM.', 'SUBMITTED', 'NEGOTIATED',
                     'COPAY', 'NOT', 'DEDUCTIBLE', 'INSURANCE', 'PATIENT',
                     'PAYABLE', 'DATES', 'CODE']
    count = sum(1 for t in header_tokens if t.lower() in line.lower())
    return count >= 4

service_line_re = re.compile(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b.*?\b[A-Z0-9]{5,}\b.*?\b[$]?\s*\d[\d,\.]{1,}\d\b')

def count_service_rows_in_block(lines: List[str], start_idx: int, end_idx: int):
    svc_count = 0
    for i in range(start_idx, end_idx):
        ln = lines[i].strip()
        if not ln:
            continue
        if service_line_re.search(ln):
            svc_count += 1
    return svc_count

def count_claim_blocks_and_services(lines: List[str]):
    i = 0
    n = len(lines)
    blocks = 0
    total_service_rows = 0
    debug_positions = []
    
    while i < n:
        if i+1 < n and is_table_header(lines[i]) and ('dates' in lines[i+1].lower() or 'code' in lines[i+1].lower()):
            j = i + 2
            found_totals = False
            while j < n:
                if 'total' in lines[j].lower() or 'totals' in lines[j].lower():
                    found_totals = True
                    break
                j += 1
            if found_totals:
                svc = count_service_rows_in_block(lines, i+2, j)
                blocks += 1
                total_service_rows += svc
                debug_positions.append((i, j, svc))
                i = j + 1
                continue
            else:
                i += 1
                continue
        i += 1
    return blocks, total_service_rows, debug_positions

def fallback_count_services_global(lines: List[str]):
    count = 0
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        if service_line_re.search(s):
            count += 1
    return count

def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> List[str]:
    raw_lines = []
    
    # Try pypdf first
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        for page in reader.pages:
            txt = page.extract_text() or ""
            for l in txt.splitlines():
                raw_lines.append(l)
    except Exception:
        # Fallback to pdfplumber
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for p in pdf.pages:
                txt = p.extract_text() or ""
                for l in txt.splitlines():
                    raw_lines.append(l)
    
    return raw_lines

def process_single_pdf_bytes(pdf_bytes: bytes, filename: str, insurance_name: str) -> Dict:
    raw_lines = extract_text_from_pdf_bytes(pdf_bytes)
    
    # Normalize lines
    normalized_lines = [reverse_if_indicated(l) for l in raw_lines]
    
    # Practice name (first ALL CAPS candidate)
    practice = ""
    for ln in normalized_lines:
        s = ln.strip()
        if len(s) >= 4 and s.upper() == s and re.search(r'[A-Z]', s) and not re.search(r'\d', s):
            if len(s.split()) >= 2:
                practice = s
                break
    
    # Page count detection
    page_count = None
    for ln in normalized_lines:
        m = re.search(r'page\s*\D*(\d+)\s*(?:of|/)\s*(\d+)', ln, re.IGNORECASE)
        if m:
            page_count = int(m.group(2))
            break
        m2 = re.search(r'(\d+)\s*of\s*(\d+)', ln, re.IGNORECASE)
        if m2:
            page_count = int(m2.group(2))
            break
        m3 = re.search(r'(\d+)of(\d+)', ln, re.IGNORECASE)
        if m3:
            page_count = int(m3.group(2))
            break
    
    if not page_count:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            page_count = len(pdf.pages)
    
    # Find trace amount/number and printed date
    trace_amt = None
    trace_no = None
    printed_date = ""
    
    for idx, ln in enumerate(normalized_lines):
        low = ln.lower()
        if 'trace' in low or 'trace :' in low or 'trace:' in low or 'tnuom' in low or 'tnuoma' in low:
            a, src = extract_amount_from_line(ln)
            if a is not None:
                trace_amt = a
            chk = extract_long_numeric_token(ln)
            if chk:
                trace_no = chk
            # Check neighbors
            for nb in normalized_lines[max(0, idx-2): idx+3]:
                if trace_amt is None:
                    a2, s2 = extract_amount_from_line(nb)
                    if a2 is not None:
                        trace_amt = a2
                if trace_no is None:
                    chk2 = extract_long_numeric_token(nb)
                    if chk2:
                        trace_no = chk2
        
        if 'printed' in low or 'detnirp' in low or 'asu :' in low:
            dates = re.findall(r'\d{1,4}/\d{1,4}/\d{1,4}', ln)
            if dates:
                printed_date = dates[0]
    
    # Claim counting
    blocks, svc_rows_in_blocks, dbg_positions = count_claim_blocks_and_services(normalized_lines)
    
    if blocks > 0:
        claim_count = svc_rows_in_blocks
    else:
        svc_global = fallback_count_services_global(normalized_lines)
        claim_count = svc_global
    
    return {
        "File Name": filename,
        "Insurance Name": insurance_name,
        "Practice Name": practice,
        "Check #": trace_no or "",
        "Check Date": printed_date or "",
        "Claim Count": claim_count,
        "Line Count": page_count,
        "Check Amount": (f"{trace_amt:.2f}" if (trace_amt is not None and isfinite(trace_amt)) else "")
    }

def process_pdfs_directly(files: List[Dict], insurance_name: str) -> List[Dict]:
    results = []
    for file_info in files:
        result = process_single_pdf_bytes(file_info["content"], file_info["filename"], insurance_name)
        results.append(result)
    return results