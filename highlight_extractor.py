import fitz
import re
from collections import defaultdict
from typing import Dict, List, Tuple, Any

class DocumentAnalyzer:
    def __init__(self, doc: fitz.Document):
        self.doc = doc
        self.font_stats = self._analyze_fonts()
        self.structure = self._analyze_structure()
        
    def _analyze_fonts(self) -> Dict[str, Dict[str, Any]]:
        """Analyze font usage throughout the document."""
        font_stats = defaultdict(lambda: {
            'sizes': defaultdict(int),
            'weights': defaultdict(int),
            'counts': defaultdict(int)
        })
        
        for page in self.doc:
            for block in page.get_text("dict")["blocks"]:
                if "lines" not in block:
                    continue
                for line in block["lines"]:
                    for span in line["spans"]:
                        font_name = span.get("font", "")
                        size = span.get("size", 0)
                        text = span.get("text", "").strip()
                        
                        if text:
                            font_stats[font_name]['sizes'][size] += 1
                            font_stats[font_name]['counts']['total'] += 1
                            if 'bold' in font_name.lower():
                                font_stats[font_name]['weights']['bold'] += 1
        
        return dict(font_stats)
    
    def _analyze_structure(self) -> Dict[str, Any]:
        """Analyze document structure and patterns."""
        structure = {
            'heading_sizes': [],
            'common_formats': defaultdict(int),
            'list_patterns': defaultdict(int),
            'code_blocks': [],
            'math_blocks': []
        }
        
        # Find most common font sizes (potential headings)
        all_sizes = []
        for font_info in self.font_stats.values():
            for size, count in font_info['sizes'].items():
                all_sizes.extend([size] * count)
        
        if all_sizes:
            avg_size = sum(all_sizes) / len(all_sizes)
            structure['heading_sizes'] = sorted(
                set(size for size in all_sizes if size > avg_size * 1.2),
                reverse=True
            )
        
        return structure

class HighlightExtractor:
    def __init__(self, doc: fitz.Document):
        self.doc = doc
        self.analyzer = DocumentAnalyzer(doc)
        
    def _get_context(self, page: fitz.Page, rect: fitz.Rect, lines: int = 2) -> Dict[str, List[str]]:
        """Get surrounding context for a highlight."""
        page_dict = page.get_text("dict")
        highlight_y = (rect.y0 + rect.y1) / 2
        
        context = {
            'before': [],
            'after': [],
            'same_paragraph': []
        }
        
        # Collect all text lines with y-positions
        text_lines = []
        current_paragraph = []
        last_y = None
        
        for block in page_dict["blocks"]:
            if "lines" not in block:
                continue
                
            for line in block["lines"]:
                y = (line["bbox"][1] + line["bbox"][3]) / 2
                text = " ".join(span["text"] for span in line["spans"])
                
                if last_y is not None and abs(y - last_y) > 20:  # New paragraph
                    if current_paragraph:
                        text_lines.append((sum(y for y, _ in current_paragraph) / len(current_paragraph),
                                        " ".join(t for _, t in current_paragraph)))
                    current_paragraph = []
                
                current_paragraph.append((y, text))
                last_y = y
        
        if current_paragraph:
            text_lines.append((sum(y for y, _ in current_paragraph) / len(current_paragraph),
                             " ".join(t for _, t in current_paragraph)))
        
        # Find the highlighted line's position
        highlight_idx = -1
        for i, (y, text) in enumerate(text_lines):
            if abs(y - highlight_y) < 10:
                highlight_idx = i
                break
        
        if highlight_idx >= 0:
            # Get context before
            start_idx = max(0, highlight_idx - lines)
            context['before'] = [text for _, text in text_lines[start_idx:highlight_idx]]
            
            # Get context after
            end_idx = min(len(text_lines), highlight_idx + lines + 1)
            context['after'] = [text for _, text in text_lines[highlight_idx + 1:end_idx]]
            
            # Get same paragraph context
            if highlight_idx > 0 and abs(text_lines[highlight_idx][0] - text_lines[highlight_idx-1][0]) < 20:
                context['same_paragraph'].extend([text for _, text in text_lines[max(0, highlight_idx-2):highlight_idx]])
            if highlight_idx < len(text_lines)-1 and abs(text_lines[highlight_idx][0] - text_lines[highlight_idx+1][0]) < 20:
                context['same_paragraph'].extend([text for _, text in text_lines[highlight_idx+1:min(len(text_lines), highlight_idx+3)]])
        
        return context
    
    def _analyze_highlight_style(self, page: fitz.Page, rect: fitz.Rect) -> Dict[str, Any]:
        """Analyze text style within highlight."""
        style_info = {
            'font_size': 0,
            'is_bold': False,
            'is_italic': False,
            'alignment': 'left',
            'indentation': 0,
            'is_list_item': False,
            'is_code_style': False
        }
        
        # Get text with style information
        page_dict = page.get_text("dict")
        
        for block in page_dict["blocks"]:
            if "lines" not in block:
                continue
                
            for line in block["lines"]:
                line_rect = fitz.Rect(line["bbox"])
                if line_rect.intersect(rect):
                    style_info['indentation'] = line["bbox"][0]
                    
                    for span in line["spans"]:
                        span_rect = fitz.Rect(span["bbox"])
                        if span_rect.intersect(rect):
                            style_info['font_size'] = span.get("size", 0)
                            font_name = span.get("font", "").lower()
                            style_info['is_bold'] = 'bold' in font_name
                            style_info['is_italic'] = 'italic' in font_name
                            
                            # Check for monospace font (potential code)
                            style_info['is_code_style'] = any(code_font in font_name 
                                                            for code_font in ['mono', 'code', 'console'])
        
        return style_info

    def extract_highlights(self) -> List[Tuple[str, str]]:
        """Extract and categorize highlights from the document."""
        highlights = []
        
        for page_num, page in enumerate(self.doc):
            for annot in page.annots():
                if annot.type[1] == "Highlight":
                    rect = annot.rect
                    # Add small margin to avoid false positives
                    margin = 2
                    clip_rect = fitz.Rect(rect.x0 + margin, rect.y0 + margin,
                                        rect.x1 - margin, rect.y1 - margin)
                    
                    words = page.get_text("words", clip=clip_rect)
                    if not words:
                        continue
                    
                    # Sort words and group into lines
                    words_sorted = sorted(words, key=lambda w: (round(w[3], 1), w[0]))
                    lines = defaultdict(list)
                    last_y = None
                    y_tolerance = 3
                    
                    for word in words_sorted:
                        y_pos = round(word[3], 1)
                        if last_y is None or abs(y_pos - last_y) > y_tolerance:
                            last_y = y_pos
                        lines[last_y].append(word[4])
                    
                    # Process each line
                    for y_pos in sorted(lines.keys()):
                        text = ' '.join(lines[y_pos]).strip()
                        if not text:
                            continue
                        
                        # Get style and context information
                        style_info = self._analyze_highlight_style(page, rect)
                        context = self._get_context(page, rect)
                        
                        # Categorize the highlight
                        category = self._categorize_highlight(text, style_info, context)
                        highlights.append((category, text))
        
        return highlights

    def _categorize_highlight(self, text: str, style_info: Dict[str, Any], 
                            context: Dict[str, List[str]]) -> str:
        """Enhanced categorization logic using style and context information."""
        text = text.strip()
        
        # Helper function to check heading characteristics
        def is_likely_heading():
            if style_info['font_size'] > 0:
                # Check if font size matches known heading sizes
                if style_info['font_size'] in self.analyzer.structure['heading_sizes'][:3]:
                    return True
            
            if style_info['is_bold']:
                if len(text) < 80 and text.istitle() and not any(char in text for char in '.!?;:,'):
                    # Check if previous and next lines don't look like headings
                    surrounding_text = context['before'] + context['after']
                    if not any(line.istitle() for line in surrounding_text):
                        return True
            
            if re.match(r'^(Chapter|Section|Part|Unit)\s+\d+', text, re.IGNORECASE):
                return True
                
            return False
        
        # Check for headings
        if is_likely_heading():
            return 'heading'
        
        # Check for code
        code_indicators = [
            (r'\b(def|class|import|from|if|elif|else|for|while|try|except)\b', 'Python'),
            (r'\b(function|var|let|const|class|interface)\b', 'JavaScript'),
            (r'\b(public|private|protected|static|void|class)\b', 'Java'),
            (r'\b(SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|FROM|WHERE)\b', 'SQL')
        ]
        
        if style_info['is_code_style']:
            return 'code'
            
        for pattern, _ in code_indicators:
            if re.search(pattern, text, re.IGNORECASE):
                # Verify with context
                code_context = sum(1 for line in context['same_paragraph'] 
                                 if any(re.search(p[0], line, re.IGNORECASE) 
                                       for p in code_indicators))
                if code_context > 0:
                    return 'code'
        
        # Check for mathematical expressions
        math_patterns = [
            r'[+\-×÷=≠≈≤≥∞∑∫√∛∜∂∇∆∅∈∉⊂⊃∪∩∧∨¬⇒⇔∀∃∄]',
            r'\b(sin|cos|tan|log|ln|exp|sqrt|pi|alpha|beta|gamma|delta)\b',
            r'\d+\s*[+\-×÷=]\s*\d+',
            r'\(\d+\)'
        ]
        
        math_matches = sum(1 for pattern in math_patterns if re.search(pattern, text))
        if math_matches >= 2:
            return 'math'
        
        # Check for lists with improved context awareness
        if re.match(r'^[-•*]\s', text) or re.match(r'^\d+[\.)]\s', text):
            # Verify with surrounding context
            list_context = sum(1 for line in context['before'] + context['after']
                             if re.match(r'^[-•*]\s|\d+[\.)]\s', line))
            if list_context > 0:
                return 'list_item'
        
        # Check for questions
        if text.endswith('?'):
            return 'question'
        if text.startswith(('What', 'How', 'Why', 'When', 'Where', 'Who')):
            # Avoid misclassifying section titles
            if not style_info['is_bold'] and len(text) > 50:
                return 'question'
        
        # Check for definitions
        if ':' in text:
            term = text.split(':')[0].strip()
            if len(term) < 30 and not re.search(r'[.!?]', term):
                # Avoid misclassifying time or ratios
                if not re.match(r'\d+:\d+', text):
                    return 'definition'
        
        # Handle emphasized text that isn't a heading
        if style_info['is_bold'] and not is_likely_heading():
            return 'emphasis'
        
        # Default to regular point
        return 'point'