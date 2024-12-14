from product_agent import get_product_info
from ReportAgent import ReportAgent
from pdf_loader import MarkdownToPDFConverter
import nest_asyncio; 
from Data import Data

nest_asyncio.apply()

class Autogen:
    def __init__(self, client_name, client_data):
        self.pdf_directory_path = "./pdf_directory"
        self.client_name = client_name
        self.client = Data.clients[client_name]
        self.client_data = client_data

    def product_info(self):
        product_info = get_product_info(self.client,Data.pimco_prod, self.pdf_directory_path)
        print(product_info)
        return product_info
    
    def generate_report(self):
        agent = ReportAgent(self.client, self.client_data["personal_interests"], self.product_info())
        generated_report = agent.generate_report()
        return generated_report

    def convert_to_pdf(self, generated_report):
        converter = MarkdownToPDFConverter(self.client_name, output_dir_name="output")
        resp = converter.process_reports(generated_report)
        return resp





   
