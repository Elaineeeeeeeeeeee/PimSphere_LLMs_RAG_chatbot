from pathlib import Path
from markdown_pdf import MarkdownPdf, Section
from pydantic import BaseModel

class CustomBaseModel(BaseModel):
    class Config:
        arbitrary_types_allowed = True

class MarkdownToPDFConverter:
    def __init__(self, client_name, output_dir_name="output"):
        # Set up base and output directories
        self.base_dir = Path.cwd()
        self.output_dir = self.base_dir / output_dir_name
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.client_name = client_name

    def split_reports(self, markdown_content, delimiter='---'):
        """
        Split the markdown content into individual reports using a specified delimiter.
        """
        reports = markdown_content.split('**Report')[1:]  # Start from index 1 to skip content before first report
    
        # Reconstruct each report by adding back the '**Report' prefix
        reports = ['**Report' + report.strip() for report in reports]
        
        return reports

    def convert_to_pdf(self, report_content, output_filename):
        """
        Convert a single markdown report to a PDF.
        """
        pdf = MarkdownPdf(toc_level=2)  # Generate Table of Contents up to level 2 headings
        pdf.add_section(Section(report_content))
        pdf.save(output_filename)

    def process_reports(self, markdown_content, filename_prefix="Report"):
        """
        Split the markdown content and convert each report to a separate PDF.
        Returns a dictionary of generated PDF file paths.
        """
        reports = self.split_reports(markdown_content)
        generated_pdfs = {}

        for i, report in enumerate(reports, start=1):
            output_filename = self.output_dir / f"{self.client_name}_{filename_prefix}{i}.pdf"
            self.convert_to_pdf(report, str(output_filename))
            # print(f"Converted {filename_prefix} {i} to {output_filename}")
            
            # Store PDF file paths in a dictionary
            generated_pdfs[f"{filename_prefix} {i}"] = str(output_filename)
        
        return generated_pdfs