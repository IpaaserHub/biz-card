from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import os

from ocr_service import OCRService 

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from templates import router as templates_router
app.include_router(templates_router)

ocr_service = OCRService()

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Business Card Drafter Backend"}

@app.post("/analyze")
async def analyze_card(
    file_front: UploadFile = File(...), 
    file_back: UploadFile = File(None),
    template_id: str = Form(None)
):
    image_paths = []
    
    # Save front image
    front_filename = f"temp_front_{file_front.filename}"
    with open(front_filename, "wb") as buffer:
        buffer.write(await file_front.read())
    image_paths.append(front_filename)

    # Save back image if provided
    back_filename = None
    if file_back:
        back_filename = f"temp_back_{file_back.filename}"
        with open(back_filename, "wb") as buffer:
            buffer.write(await file_back.read())
        image_paths.append(back_filename)
    
    # Load template if selected
    template_content = None
    if template_id:
        from templates import load_templates
        templates = load_templates()
        for t in templates:
            if t['id'] == template_id:
                template_content = t['content']
                break

    try:
        result = ocr_service.analyze(image_paths, template_content)
    finally:
        # Cleanup
        for path in image_paths:
            if os.path.exists(path):
                os.remove(path)
            
    return result
