"""
NYOS APR PDF Generation Service

Generates professional, well-structured PDF reports for Annual Product Reviews
with company branding, proper formatting, and regulatory-ready layout.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm, mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, HRFlowable, KeepTogether, ListFlowable, ListItem
)
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle, Ellipse, Path
from reportlab.graphics import renderPDF
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime
from pathlib import Path
import os
import re

# Get the assets directory
ASSETS_DIR = Path(__file__).parent.parent / "assets"

# Brand Colors
BRAND_PRIMARY = colors.HexColor("#1e3a8a")      # Deep blue
BRAND_SECONDARY = colors.HexColor("#2563eb")   # Blue
BRAND_ACCENT = colors.HexColor("#22c55e")      # Green
BRAND_DARK = colors.HexColor("#0f172a")        # Near black
BRAND_LIGHT = colors.HexColor("#f8fafc")       # Light gray
BRAND_GRAY = colors.HexColor("#64748b")        # Gray


class APRPDFGenerator:
    """Generates professional APR PDF documents"""
    
    def __init__(self):
        self.styles = self._create_styles()
        self.page_width, self.page_height = A4
        
    def _create_styles(self):
        """Create custom paragraph styles for the document"""
        styles = getSampleStyleSheet()
        
        # Title style - Main document title
        styles.add(ParagraphStyle(
            name='APRTitle',
            parent=styles['Heading1'],
            fontSize=28,
            textColor=BRAND_PRIMARY,
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Subtitle
        styles.add(ParagraphStyle(
            name='APRSubtitle',
            parent=styles['Normal'],
            fontSize=14,
            textColor=BRAND_GRAY,
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica'
        ))
        
        # Section Header (H1)
        styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=BRAND_PRIMARY,
            spaceBefore=25,
            spaceAfter=15,
            fontName='Helvetica-Bold',
            borderWidth=0,
            borderPadding=0,
            borderColor=BRAND_PRIMARY,
        ))
        
        # Subsection Header (H2)
        styles.add(ParagraphStyle(
            name='SubsectionHeader',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=BRAND_SECONDARY,
            spaceBefore=15,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        ))
        
        # Body text
        styles.add(ParagraphStyle(
            name='APRBody',
            parent=styles['Normal'],
            fontSize=10,
            textColor=BRAND_DARK,
            spaceBefore=6,
            spaceAfter=6,
            alignment=TA_JUSTIFY,
            fontName='Helvetica',
            leading=14
        ))
        
        # Bullet point
        styles.add(ParagraphStyle(
            name='APRBullet',
            parent=styles['Normal'],
            fontSize=10,
            textColor=BRAND_DARK,
            leftIndent=20,
            spaceBefore=3,
            spaceAfter=3,
            fontName='Helvetica',
            bulletIndent=10,
            leading=14
        ))
        
        # Executive summary highlight
        styles.add(ParagraphStyle(
            name='ExecSummary',
            parent=styles['Normal'],
            fontSize=11,
            textColor=BRAND_DARK,
            spaceBefore=8,
            spaceAfter=8,
            alignment=TA_JUSTIFY,
            fontName='Helvetica',
            leading=16,
            backColor=colors.HexColor("#f0f9ff"),
            borderWidth=1,
            borderColor=BRAND_SECONDARY,
            borderPadding=10,
            borderRadius=5
        ))
        
        # Table header
        styles.add(ParagraphStyle(
            name='TableHeader',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.white,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Table cell
        styles.add(ParagraphStyle(
            name='TableCell',
            parent=styles['Normal'],
            fontSize=9,
            textColor=BRAND_DARK,
            alignment=TA_CENTER,
            fontName='Helvetica'
        ))
        
        # Footer
        styles.add(ParagraphStyle(
            name='Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=BRAND_GRAY,
            alignment=TA_CENTER,
            fontName='Helvetica'
        ))
        
        # Status indicator styles
        styles.add(ParagraphStyle(
            name='StatusGood',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor("#16a34a"),
            fontName='Helvetica-Bold',
            alignment=TA_CENTER
        ))
        
        styles.add(ParagraphStyle(
            name='StatusWarning',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor("#ea580c"),
            fontName='Helvetica-Bold',
            alignment=TA_CENTER
        ))
        
        styles.add(ParagraphStyle(
            name='StatusCritical',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor("#dc2626"),
            fontName='Helvetica-Bold',
            alignment=TA_CENTER
        ))
        
        return styles
    
    def _draw_logo(self, canvas, x, y):
        """Draw the NYOS logo using ReportLab graphics"""
        # Scale factor for the logo
        scale = 0.8
        
        # Capsule shape - left part (blue)
        canvas.setFillColor(BRAND_SECONDARY)
        canvas.roundRect(x, y, 30*scale, 15*scale, 7*scale, fill=1, stroke=0)
        
        # Capsule shape - right part (green)
        canvas.setFillColor(BRAND_ACCENT)
        canvas.roundRect(x + 15*scale, y, 20*scale, 15*scale, 7*scale, fill=1, stroke=0)
        
        # Checkmark on green part
        canvas.setStrokeColor(colors.white)
        canvas.setLineWidth(2)
        p = canvas.beginPath()
        p.moveTo(x + 22*scale, y + 7.5*scale)
        p.lineTo(x + 26*scale, y + 11*scale)
        p.lineTo(x + 32*scale, y + 4*scale)
        canvas.drawPath(p, stroke=1, fill=0)
        
        # Molecular dots on blue part
        canvas.setFillColor(colors.Color(1, 1, 1, 0.6))
        canvas.circle(x + 8*scale, y + 9*scale, 1.5*scale, fill=1, stroke=0)
        canvas.setFillColor(colors.Color(1, 1, 1, 0.4))
        canvas.circle(x + 12*scale, y + 5*scale, 1*scale, fill=1, stroke=0)
        
        # NYOS text
        canvas.setFillColor(BRAND_PRIMARY)
        canvas.setFont('Helvetica-Bold', 16)
        canvas.drawString(x + 40*scale, y + 3*scale, "NYOS")
        
        # Tagline
        canvas.setFillColor(BRAND_GRAY)
        canvas.setFont('Helvetica', 6)
        canvas.drawString(x + 40*scale, y - 5*scale, "PHARMACEUTICAL QUALITY")
    
    def _header_footer(self, canvas, doc):
        """Draw header with logo and footer with page numbers"""
        canvas.saveState()
        
        # Header - Draw logo
        self._draw_logo(canvas, 50, self.page_height - 55)
        
        # Header line
        canvas.setStrokeColor(BRAND_SECONDARY)
        canvas.setLineWidth(2)
        canvas.line(50, self.page_height - 70, self.page_width - 50, self.page_height - 70)
        
        # Document info on right side of header
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(BRAND_GRAY)
        canvas.drawRightString(self.page_width - 50, self.page_height - 45, 
                               f"Annual Product Review")
        canvas.drawRightString(self.page_width - 50, self.page_height - 55, 
                               f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        # Footer
        canvas.setStrokeColor(BRAND_LIGHT)
        canvas.setLineWidth(1)
        canvas.line(50, 40, self.page_width - 50, 40)
        
        # Page number
        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(BRAND_GRAY)
        canvas.drawCentredString(self.page_width / 2, 25, f"Page {doc.page}")
        
        # Confidential notice
        canvas.setFont('Helvetica-Oblique', 7)
        canvas.drawString(50, 25, "CONFIDENTIAL - For Internal Use Only")
        
        # Company info
        canvas.drawRightString(self.page_width - 50, 25, "NYOS Pharmaceutical Quality System")
        
        canvas.restoreState()
    
    def _create_cover_page(self, apr_data: dict) -> list:
        """Create the cover page elements"""
        elements = []
        
        # Large spacer for centering
        elements.append(Spacer(1, 2*inch))
        
        # Main title
        elements.append(Paragraph(
            "ANNUAL PRODUCT REVIEW",
            self.styles['APRTitle']
        ))
        
        # Product name
        elements.append(Paragraph(
            f"<b>Paracetamol 500mg Tablets</b>",
            self.styles['APRSubtitle']
        ))
        
        # Year
        elements.append(Spacer(1, 0.5*inch))
        elements.append(Paragraph(
            f"<font size='24' color='#2563eb'><b>{apr_data.get('year', 'N/A')}</b></font>",
            ParagraphStyle('YearStyle', alignment=TA_CENTER)
        ))
        
        elements.append(Spacer(1, 1*inch))
        
        # Summary box
        summary_data = [
            ['Total Batches', str(apr_data.get('total_batches', 'N/A'))],
            ['Overall Yield', f"{apr_data.get('overall_yield', 'N/A'):.1f}%" if apr_data.get('overall_yield') else 'N/A'],
            ['QC Pass Rate', f"{apr_data.get('overall_qc_pass_rate', 'N/A'):.1f}%" if apr_data.get('overall_qc_pass_rate') else 'N/A'],
            ['Total Complaints', str(apr_data.get('total_complaints', 'N/A'))],
            ['Total CAPAs', str(apr_data.get('total_capas', 'N/A'))],
        ]
        
        summary_table = Table(summary_data, colWidths=[2.5*inch, 1.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), BRAND_LIGHT),
            ('TEXTCOLOR', (0, 0), (-1, -1), BRAND_DARK),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, BRAND_SECONDARY),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
        ]))
        
        # Center the table
        elements.append(Table([[summary_table]], colWidths=[5*inch]))
        
        elements.append(Spacer(1, 1.5*inch))
        
        # Document info
        info_style = ParagraphStyle(
            'InfoStyle',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=BRAND_GRAY,
            alignment=TA_CENTER
        )
        
        elements.append(Paragraph(
            f"<b>Document Status:</b> {apr_data.get('status', 'Draft').upper()}",
            info_style
        ))
        
        if apr_data.get('approved_by'):
            elements.append(Paragraph(
                f"<b>Approved By:</b> {apr_data.get('approved_by')} on {apr_data.get('approved_at', 'N/A')}",
                info_style
            ))
        
        elements.append(Spacer(1, 0.3*inch))
        elements.append(Paragraph(
            f"Report Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}",
            info_style
        ))
        
        elements.append(PageBreak())
        
        return elements
    
    def _create_toc(self, sections: list) -> list:
        """Create table of contents"""
        elements = []
        
        elements.append(Paragraph("TABLE OF CONTENTS", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.3*inch))
        
        toc_style = ParagraphStyle(
            'TOCEntry',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=BRAND_DARK,
            spaceBefore=8,
            spaceAfter=8,
            leftIndent=0
        )
        
        for i, section in enumerate(sections, 1):
            elements.append(Paragraph(
                f"<b>{i}.</b> {section}",
                toc_style
            ))
        
        elements.append(PageBreak())
        
        return elements
    
    def _parse_markdown_to_elements(self, markdown_text: str, base_style='APRBody') -> list:
        """Convert markdown text to ReportLab elements"""
        if not markdown_text:
            return [Paragraph("<i>No content available</i>", self.styles['APRBody'])]
        
        elements = []
        lines = markdown_text.split('\n')
        current_list = []
        in_list = False
        
        for line in lines:
            line = line.strip()
            
            if not line:
                if in_list and current_list:
                    elements.extend(current_list)
                    current_list = []
                    in_list = False
                continue
            
            # Headers
            if line.startswith('### '):
                if in_list and current_list:
                    elements.extend(current_list)
                    current_list = []
                    in_list = False
                text = self._clean_markdown(line[4:])
                elements.append(Paragraph(text, self.styles['SubsectionHeader']))
                
            elif line.startswith('## '):
                if in_list and current_list:
                    elements.extend(current_list)
                    current_list = []
                    in_list = False
                text = self._clean_markdown(line[3:])
                elements.append(Paragraph(text, self.styles['SectionHeader']))
                
            elif line.startswith('# '):
                if in_list and current_list:
                    elements.extend(current_list)
                    current_list = []
                    in_list = False
                text = self._clean_markdown(line[2:])
                elements.append(Paragraph(text, self.styles['SectionHeader']))
                
            # Bullet points
            elif line.startswith('- ') or line.startswith('* '):
                in_list = True
                text = self._clean_markdown(line[2:])
                current_list.append(Paragraph(f"• {text}", self.styles['APRBullet']))
                
            # Numbered lists
            elif re.match(r'^\d+\.\s', line):
                in_list = True
                text = self._clean_markdown(re.sub(r'^\d+\.\s', '', line))
                num = re.match(r'^(\d+)', line).group(1)
                current_list.append(Paragraph(f"{num}. {text}", self.styles['APRBullet']))
                
            # Regular paragraph
            else:
                if in_list and current_list:
                    elements.extend(current_list)
                    current_list = []
                    in_list = False
                text = self._clean_markdown(line)
                if text:
                    elements.append(Paragraph(text, self.styles[base_style]))
        
        # Don't forget remaining list items
        if current_list:
            elements.extend(current_list)
        
        return elements
    
    def _clean_markdown(self, text: str) -> str:
        """Convert markdown formatting to ReportLab tags"""
        if not text:
            return ""
        
        # Bold: **text** or __text__
        text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'__(.+?)__', r'<b>\1</b>', text)
        
        # Italic: *text* or _text_
        text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
        text = re.sub(r'_(.+?)_', r'<i>\1</i>', text)
        
        # Code: `text`
        text = re.sub(r'`(.+?)`', r'<font face="Courier">\1</font>', text)
        
        return text
    
    def _create_section(self, title: str, content: str, section_num: int) -> list:
        """Create a formatted section with header and content"""
        elements = []
        
        # Section header with number
        header_text = f"{section_num}. {title}"
        elements.append(Paragraph(header_text, self.styles['SectionHeader']))
        
        # Decorative line under header
        elements.append(HRFlowable(
            width="100%",
            thickness=2,
            color=BRAND_SECONDARY,
            spaceAfter=15
        ))
        
        # Parse and add content
        content_elements = self._parse_markdown_to_elements(content)
        elements.extend(content_elements)
        
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _create_statistics_table(self, apr_data: dict) -> list:
        """Create annual statistics summary table"""
        elements = []
        
        elements.append(Paragraph("Annual Statistics Summary", self.styles['SubsectionHeader']))
        
        # Create data for table
        data = [
            ['Metric', 'Value', 'Status'],
            ['Total Batches Produced', str(apr_data.get('total_batches', 'N/A')), '✓'],
            ['Average Yield', f"{apr_data.get('overall_yield', 0):.2f}%", 
             '✓' if apr_data.get('overall_yield', 0) >= 95 else '⚠'],
            ['QC Pass Rate', f"{apr_data.get('overall_qc_pass_rate', 0):.1f}%",
             '✓' if apr_data.get('overall_qc_pass_rate', 0) >= 95 else '⚠'],
            ['Customer Complaints', str(apr_data.get('total_complaints', 'N/A')), '—'],
            ['CAPAs Initiated', str(apr_data.get('total_capas', 'N/A')), '—'],
        ]
        
        table = Table(data, colWidths=[2.5*inch, 1.5*inch, 1*inch])
        table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), BRAND_PRIMARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Data rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            
            # Alternating row colors
            ('BACKGROUND', (0, 1), (-1, 1), BRAND_LIGHT),
            ('BACKGROUND', (0, 3), (-1, 3), BRAND_LIGHT),
            ('BACKGROUND', (0, 5), (-1, 5), BRAND_LIGHT),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, BRAND_GRAY),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def generate_apr_pdf(self, apr_data: dict) -> BytesIO:
        """
        Generate the complete APR PDF document
        
        Args:
            apr_data: Dictionary containing all APR data including:
                - year: int
                - title: str
                - executive_summary: str
                - production_review: str
                - quality_review: str
                - complaints_review: str
                - capa_review: str
                - equipment_review: str
                - stability_review: str
                - trend_analysis: str
                - conclusions: str
                - recommendations: str
                - total_batches: int
                - total_complaints: int
                - total_capas: int
                - overall_yield: float
                - overall_qc_pass_rate: float
                - status: str
                - approved_by: str (optional)
                - approved_at: str (optional)
        
        Returns:
            BytesIO buffer containing the PDF
        """
        buffer = BytesIO()
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=50,
            leftMargin=50,
            topMargin=80,
            bottomMargin=60,
            title=f"APR {apr_data.get('year', '')} - Paracetamol 500mg",
            author="NYOS Pharmaceutical Quality System"
        )
        
        elements = []
        
        # Cover page
        elements.extend(self._create_cover_page(apr_data))
        
        # Table of contents
        sections = [
            "Executive Summary",
            "Production Review",
            "Quality Review",
            "Customer Complaints Review",
            "CAPA Review",
            "Equipment Review",
            "Stability Review",
            "Trend Analysis",
            "Conclusions",
            "Recommendations"
        ]
        elements.extend(self._create_toc(sections))
        
        # Statistics summary
        elements.extend(self._create_statistics_table(apr_data))
        elements.append(PageBreak())
        
        # Main sections
        section_mapping = [
            ("Executive Summary", apr_data.get('executive_summary', '')),
            ("Production Review", apr_data.get('production_review', '')),
            ("Quality Review", apr_data.get('quality_review', '')),
            ("Customer Complaints Review", apr_data.get('complaints_review', '')),
            ("CAPA Review", apr_data.get('capa_review', '')),
            ("Equipment Review", apr_data.get('equipment_review', '')),
            ("Stability Review", apr_data.get('stability_review', '')),
            ("Trend Analysis", apr_data.get('trend_analysis', '')),
            ("Conclusions", apr_data.get('conclusions', '')),
            ("Recommendations", apr_data.get('recommendations', '')),
        ]
        
        for i, (title, content) in enumerate(section_mapping, 1):
            elements.extend(self._create_section(title, content, i))
            # Page break after major sections
            if i in [1, 3, 6, 8]:
                elements.append(PageBreak())
        
        # Signature page
        elements.append(PageBreak())
        elements.extend(self._create_signature_page(apr_data))
        
        # Build the PDF
        doc.build(elements, onFirstPage=self._header_footer, onLaterPages=self._header_footer)
        
        buffer.seek(0)
        return buffer
    
    def _create_signature_page(self, apr_data: dict) -> list:
        """Create approval/signature page"""
        elements = []
        
        elements.append(Spacer(1, 1*inch))
        elements.append(Paragraph("DOCUMENT APPROVAL", self.styles['SectionHeader']))
        elements.append(HRFlowable(width="100%", thickness=2, color=BRAND_SECONDARY, spaceAfter=30))
        
        approval_style = ParagraphStyle(
            'ApprovalStyle',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=BRAND_DARK,
            spaceBefore=15,
            spaceAfter=15
        )
        
        elements.append(Paragraph(
            "This Annual Product Review has been prepared in accordance with regulatory requirements "
            "and internal quality procedures. The data and conclusions presented herein have been "
            "reviewed for accuracy and completeness.",
            approval_style
        ))
        
        elements.append(Spacer(1, 0.5*inch))
        
        # Signature boxes
        sig_data = [
            ['<b>Prepared By:</b>', '', '<b>Date:</b>', ''],
            ['', '', '', ''],
            ['Name: _____________________', '', 'Signature: _____________________', ''],
            ['', '', '', ''],
            ['<b>Reviewed By:</b>', '', '<b>Date:</b>', ''],
            ['', '', '', ''],
            ['Name: _____________________', '', 'Signature: _____________________', ''],
            ['', '', '', ''],
            ['<b>Approved By:</b>', '', '<b>Date:</b>', ''],
            ['', '', '', ''],
            ['Name: _____________________', '', 'Signature: _____________________', ''],
        ]
        
        # Convert to Paragraphs
        sig_table_data = []
        for row in sig_data:
            sig_table_data.append([
                Paragraph(cell, self.styles['APRBody']) if cell else '' for cell in row
            ])
        
        sig_table = Table(sig_table_data, colWidths=[2*inch, 0.5*inch, 2*inch, 0.5*inch])
        sig_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        elements.append(sig_table)
        
        elements.append(Spacer(1, 1*inch))
        
        # Document control info
        control_style = ParagraphStyle(
            'ControlStyle',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=BRAND_GRAY,
            alignment=TA_CENTER,
            spaceBefore=10
        )
        
        elements.append(HRFlowable(width="100%", thickness=1, color=BRAND_LIGHT, spaceBefore=20))
        elements.append(Paragraph(
            f"<b>Document ID:</b> APR-{apr_data.get('year', 'XXXX')}-001 | "
            f"<b>Version:</b> 1.0 | "
            f"<b>Classification:</b> Confidential",
            control_style
        ))
        elements.append(Paragraph(
            f"Generated by NYOS Pharmaceutical Quality System on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            control_style
        ))
        
        return elements


def generate_apr_pdf(apr_data: dict) -> BytesIO:
    """
    Convenience function to generate APR PDF
    
    Args:
        apr_data: APR report data dictionary
        
    Returns:
        BytesIO buffer containing the PDF
    """
    generator = APRPDFGenerator()
    return generator.generate_apr_pdf(apr_data)
