import json
import os
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

router = APIRouter()
DATA_FILE = "templates.json"

class Template(BaseModel):
    id: str
    name: str
    content: str

def load_templates() -> List[dict]:
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def save_templates(templates: List[dict]):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(templates, f, indent=4, ensure_ascii=False)

@router.get("/templates", response_model=List[Template])
def get_templates():
    return load_templates()

@router.post("/templates", response_model=Template)
def create_template(template: Template):
    templates = load_templates()
    if any(t['id'] == template.id for t in templates):
        raise HTTPException(status_code=400, detail="Template ID already exists")
    
    templates.append(template.dict())
    save_templates(templates)
    return template

@router.put("/templates/{template_id}", response_model=Template)
def update_template(template_id: str, updated_template: Template):
    templates = load_templates()
    for i, t in enumerate(templates):
        if t['id'] == template_id:
            templates[i] = updated_template.dict()
            save_templates(templates)
            return updated_template
    raise HTTPException(status_code=404, detail="Template not found")

@router.delete("/templates/{template_id}")
def delete_template(template_id: str):
    templates = load_templates()
    original_len = len(templates)
    templates = [t for t in templates if t['id'] != template_id]
    
    if len(templates) == original_len:
        raise HTTPException(status_code=404, detail="Template not found")
        
    save_templates(templates)
    return {"message": "Template deleted"}
