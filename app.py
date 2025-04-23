from flask import Flask, render_template, request, send_file, jsonify
import fitz
import os
import tempfile
import re
from werkzeug.utils import secure_filename
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()

def extract_highlights(pdf_path):
    """Extract and format highlights into concise, summary-oriented notes"""
    doc = fitz.open(pdf_path)
    highlights = []
    
    for page in doc:
        for annot in page.annots():
            if annot.type[1] == "Highlight":
                rect = annot.rect
                words = page.get_text("words", clip=rect)
                
                if not words:
                    continue
                
                # Group words into lines based on y-position
                lines = {}
                for word in words:
                    y_pos = round(word[3], 1)  # Round y-coordinate to group lines
                    if y_pos not in lines:
                        lines[y_pos] = []
                    lines[y_pos].append(word[4])
                
                # Process each line
                for y_pos in sorted(lines.keys()):
                    line_text = ' '.join(lines[y_pos]).strip()
                    
                    # Skip empty lines
                    if not line_text:
                        continue
                    
                    # Format headings (e.g., "AIM:", section titles)
                    if re.match(r'^(AIM:|Objective:|Goal:)', line_text, re.IGNORECASE):
                        highlights.append(('heading', line_text))
                    # Format numbered or bulleted lists
                    elif re.match(r'^\d+\)|\d+\.', line_text):
                        highlights.append(('list', line_text))
                    # Format code blocks (simplified for summary)
                    elif any(char in line_text for char in ['{', '}', ';', '=', '<', '>']):
                        # Summarize code snippets
                        if 'class' in line_text or 'public' in line_text:
                            highlights.append(('code', 'Code snippet: Process scheduling implementation'))
                        else:
                            highlights.append(('code', line_text[:100] + '...' if len(line_text) > 100 else line_text))
                    # Format complete sentences or key points
                    elif line_text.endswith(('.', ':', ';')):
                        highlights.append(('point', line_text))
                    else:
                        # Treat as a brief note or fragment
                        highlights.append(('point', line_text))
    
    # Format the highlights into a structured summary
    formatted_text = []
    current_section = None
    
    for item_type, text in highlights:
        if item_type == 'heading':
            if current_section:
                formatted_text.append('\n')  # Space before new section
            formatted_text.append(text.upper())
            current_section = text
        elif item_type == 'list':
            formatted_text.append(f"- {text}")
        elif item_type == 'point':
            formatted_text.append(f"• {text}")
        elif item_type == 'code':
            formatted_text.append(f"[Code]: {text}")
    
    return '\n'.join(formatted_text).strip()

def create_pdf_summary(text, output_path):
    """Create a formatted PDF from extracted highlights"""
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                          rightMargin=inch/2, leftMargin=inch/2,
                          topMargin=inch/2, bottomMargin=inch/2)
    styles = getSampleStyleSheet()
    
    # Custom styles
    heading_style = ParagraphStyle(
        name='Heading',
        parent=styles['Heading1'],
        fontSize=14,
        spaceAfter=12,
        textColor='#4B0082'
    )
    point_style = ParagraphStyle(
        name='Point',
        parent=styles['BodyText'],
        fontSize=11,
        leading=14,
        spaceAfter=8
    )
    
    story = []
    lines = text.split('\n')
    
    for line in lines:
        if not line.strip():
            story.append(Spacer(1, 12))
            continue
        if re.match(r'^(AIM:|OBJECTIVE:|GOAL:)', line, re.IGNORECASE):
            story.append(Paragraph(line, heading_style))
        elif line.startswith('-') or line.startswith('•') or line.startswith('[Code]'):
            story.append(Paragraph(line, point_style))
        else:
            story.append(Paragraph(line, point_style))
    
    doc.build(story)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file.filename.lower().endswith('.pdf'):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            extracted_text = extract_highlights(filepath)
            
            if not extracted_text:
                os.remove(filepath)
                return jsonify({'error': 'No highlights found'}), 400
            
            # Create PDF
            pdf_filename = filename.replace('.pdf', '_notes.pdf')
            pdf_filepath = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
            create_pdf_summary(extracted_text, pdf_filepath)
            
            # Read PDF for response
            with open(pdf_filepath, 'rb') as f:
                pdf_data = f.read()
            
            # Clean up files
            os.remove(filepath)
            os.remove(pdf_filepath)
            
            return jsonify({
                'text': extracted_text,
                'filename': pdf_filename,
                'pdf_data': pdf_data.hex()  # Send PDF as hex string
            })
        except Exception as e:
            os.remove(filepath)
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

if __name__ == "__main__":
    app.run(debug=True)

# Required for Render
application = app
