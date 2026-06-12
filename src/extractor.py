import fitz  # type: ignore
import json
from typing import Tuple, List, Optional, Any
from openai import OpenAI
from models import Section, TocList

def extract_toc_with_llm(doc: fitz.Document, client: OpenAI, model_name: str) -> List[List[Any]]:
    """
    Extracts the TOC from the first few pages of a document using an LLM.
    Returns a list of [level, title, page_number] matching PyMuPDF's get_toc() format.
    """
    content_parts = []
    # Grab the first 30 pages
    for p in range(min(30, doc.page_count)):
        page = doc.load_page(p)
        content_parts.append(page.get_text())
    
    content = "\n".join(content_parts)
    
    prompt = f"""
You are an expert document parser. The following text contains the first few pages of a textbook. 
Find the Table of Contents (TOC) and extract all the chapters, sections, and subsections.
Return the hierarchy level (1 for Chapter, 2 for Section, 3 for Subsection, etc.), the title, and the page number exactly as written in the TOC.

Text:
{content}

Output your response strictly in JSON format matching the following schema:
{{
    "items": [
        {{"level": 1, "title": "Chapter Name", "page_number": 10}}
    ]
}}
"""
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful expert document parser that strictly outputs JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        
        response_content = response.choices[0].message.content
        if not response_content:
            return []
            
        parsed_data = json.loads(response_content)
        toc_list = TocList(**parsed_data)
        
        # Convert to PyMuPDF toc format: [level, title, page_number]
        return [[item.level, item.title, item.page_number] for item in toc_list.items]
    except Exception as e:
        print(f"Error extracting TOC with LLM: {e}")
        return []

def extract_sections(pdf_path: str, client: Optional[OpenAI] = None, model_name: Optional[str] = None) -> Tuple[Section, ...]:
    """
    Extracts hierarchical sections from a PDF based on its Table of Contents.
    Returns a tuple of immutable Section objects.
    """
    doc = fitz.open(pdf_path)
    toc = doc.get_toc()
    
    if not toc and client and model_name:
        print("No Table of Contents found in metadata. Extracting from first 30 pages using LLM...")
        toc = extract_toc_with_llm(doc, client, model_name)
    
    if not toc:
        content = "".join(page.get_text() for page in doc)
        return (Section(title="Full Text", hierarchy=("Document",), content=content.strip()),)
        
    sections: List[Section] = []
    hierarchy_stack: List[Tuple[int, str]] = []  
    
    for i in range(len(toc)):
        level, title, page_num = toc[i]
        page_idx = max(0, int(page_num) - 1)
        
        # Find the page where the next section of the same or higher level starts
        end_page_idx = doc.page_count - 1
        for j in range(i + 1, len(toc)):
            next_level, _, next_page_num = toc[j]
            if next_level <= level:
                # next_page_num is 1-indexed. Page before it is next_page_num - 1. 
                # Since pages are 0-indexed, that's next_page_num - 2.
                end_page_idx = max(page_idx, int(next_page_num) - 2)
                break
                
        content_parts = []
        for p in range(page_idx, end_page_idx + 1):
            if p < doc.page_count:
                page = doc.load_page(p)
                content_parts.append(page.get_text())
        
        content = "".join(content_parts).strip()
        
        # Maintain hierarchy path
        while hierarchy_stack and hierarchy_stack[-1][0] >= int(level):
            hierarchy_stack.pop()
        hierarchy_stack.append((int(level), str(title)))
        
        current_hierarchy = tuple(item[1] for item in hierarchy_stack)
        
        if content:
            sections.append(Section(
                title=str(title),
                hierarchy=current_hierarchy,
                content=content
            ))
            
    return tuple(sections)
