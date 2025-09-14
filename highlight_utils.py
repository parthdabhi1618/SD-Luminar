import fitz
import re
from collections import defaultdict

def analyze_document_structure(doc):
    """Analyze the document structure to understand heading hierarchy and content organization."""
    structure = {
        'font_sizes': defaultdict(int),
        'font_weights': defaultdict(int),
        'heading_levels': {},
        'common_formats': defaultdict(int)
    }
    
    for page in doc:
        dict_text = page.get_text("dict")
        for block in dict_text.get("blocks", []):
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    font_size = span.get("size", 0)
                    font_name = span.get("font", "")
                    text = span.get("text", "").strip()
                    
                    if text:
                        structure['font_sizes'][font_size] += 1
                        if "bold" in font_name.lower():
                            structure['font_weights'][text] = 1
                        
                        # Detect potential headings
                        if font_size > 10 and len(text) < 100:  # Typical heading characteristics
                            structure['heading_levels'][font_size] = text
    
    # Sort and normalize font sizes to determine hierarchy
    sorted_sizes = sorted(structure['font_sizes'].keys(), reverse=True)
    for i, size in enumerate(sorted_sizes[:6]):  # Consider top 6 sizes as potential heading levels
        structure['heading_levels'][size] = i + 1
    
    return structure

def extract_text_style(text_spans, text):
    """Extract style information for the given text from spans."""
    style_info = {
        'font_size': 0,
        'is_bold': False,
        'is_italic': False,
        'alignment': 'left',
        'indentation': 0
    }
    
    for span in text_spans:
        for line in span.get("lines", []):
            for s in line.get("spans", []):
                if text in s.get("text", ""):
                    style_info['font_size'] = s.get("size", 0)
                    font_name = s.get("font", "").lower()
                    style_info['is_bold'] = "bold" in font_name
                    style_info['is_italic'] = "italic" in font_name
                    style_info['indentation'] = line.get("bbox", [0])[0]  # x0 coordinate
                    break
    
    return style_info

def get_surrounding_context(page_text, rect, context_lines=2):
    """Get text context before and after the highlighted text."""
    context = {
        'before': [],
        'after': []
    }
    
    text_blocks = []
    for block in page_text.get("blocks", []):
        for line in block.get("lines", []):
            bbox = line.get("bbox")
            if bbox:
                y_mid = (bbox[1] + bbox[3]) / 2
                text = " ".join(span.get("text", "") for span in line.get("spans", []))
                text_blocks.append((y_mid, text.strip()))
    
    text_blocks.sort()
    highlight_y = (rect.y0 + rect.y1) / 2
    
    # Find the index of the highlighted text
    highlight_idx = -1
    for i, (y, text) in enumerate(text_blocks):
        if abs(y - highlight_y) < 5:  # Small tolerance for y-position matching
            highlight_idx = i
            break
    
    if highlight_idx >= 0:
        # Get context before
        start_idx = max(0, highlight_idx - context_lines)
        context['before'] = [text for _, text in text_blocks[start_idx:highlight_idx]]
        
        # Get context after
        end_idx = min(len(text_blocks), highlight_idx + context_lines + 1)
        context['after'] = [text for _, text in text_blocks[highlight_idx + 1:end_idx]]
    
    return context

def is_likely_heading(text, style_info, doc_structure):
    """Determine if text is likely a heading based on style and structure."""
    # Check font size against document's heading hierarchy
    if style_info['font_size'] in doc_structure['heading_levels']:
        heading_level = doc_structure['heading_levels'][style_info['font_size']]
        if heading_level <= 3:  # Consider only top 3 levels as definite headings
            return True
    
    # Check for bold text with certain characteristics
    if style_info['is_bold']:
        if len(text) < 80 and text.istitle() and not any(char in text for char in '.!?;:,'):
            return True
        if re.match(r'^(Chapter|Section|Part|Unit)\s+\d+', text, re.IGNORECASE):
            return True
    
    return False

def analyze_text_structure(text):
    """Analyze the structure and patterns in the text."""
    structure = {
        'sentence_count': len(re.findall(r'[.!?]+', text)),
        'word_count': len(text.split()),
        'has_numbers': bool(re.search(r'\d', text)),
        'is_list_item': bool(re.match(r'^[-•*]\s|^\d+[.)]', text)),
        'has_code_chars': bool(re.search(r'[{}\[\]()<>]', text)),
        'indentation': len(text) - len(text.lstrip()),
    }
    return structure