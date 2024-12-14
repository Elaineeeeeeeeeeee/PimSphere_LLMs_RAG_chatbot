import openai
import os
import re
import pickle
from llama_parse import LlamaParse
from llama_index.core import VectorStoreIndex
from llama_index.postprocessor.flag_embedding_reranker import FlagEmbeddingReranker
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.query_engine import SubQuestionQueryEngine
from llama_index.llms.openai import OpenAI
from llama_index.core.node_parser import MarkdownElementNodeParser
from llama_index.llms.openai import OpenAI
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env


class MetadataFilter:
    def __init__(self, api_key, client, crm_data, chat_history, products):
        openai.api_key = api_key
        self.crm_data = crm_data
        self.chat_history = chat_history
        self.client = client
        self.products = products

    def get_client_preference(self):
        """
        Generate client preferences using OpenAI API based on chat history and CRM data.
        """
        prompt = f"""
            I want to generate a ordered list of client's interested product and an uninterested products based on the client's chat history and user behavior data composed of downloading report and visiting product website.
            For interested product, the order is based on how much they are interestedin the product. Uninterested products dont need order.
            Client name: {self.client}

            You can find client's chat history here: {self.chat_history["chats"]}, viewing all those notes content,
            If they want to know more about a specific product, they are interested in that product.
            The more they mention a product, the more they are interested in that product.

            You can find client's behavior data here: {self.crm_data["activities"]}, the two types of activities are downloading report and visiting product webpage,
            for downloading report, they are interested in that product, for visiting product webpage, they are interested in the product on that webpage.
            The more they download a report or visit a product webpage(which can be calculated as the sum of the **count** field), the more they are interested in that product.

            The products are: {self.products}.

            Based on the above information, please generate a sorted list of products that the client is interested and a list of products that the client is not interested in. 
            The products should all be from the list of {self.products}. 
           

            Pay attention!
            1. the output should be strictlty follow the format below, for products list, use the format [product1, product2, ...]
            2. for the interested and uninterested products, use the format below:
            prod_name: product1
            explanation(be brief and use bulletpoints):
            **dont add - or any other characters before prod_name or explanation, just the text**
            3. the uninterested products should be those clearly mentioned. If a product is not mentioned, it should be considered as neutral instead of uninterested.
            4. use - to add bullet points in the explanation.
            
            ***Strictly follow the output format below***:
            Interested products list: [product1, product2, ...]

            Interested products: 
            ***no - before***prod_name: product1
            explanation***be brief and use bulletpoints***:  
            ...
            ]

            Uninterested products list: [product1, ...]
            
            Uninterested products: 
            ***no - before***prod_name: product1
            explanation***be brief and use bulletpoints***:   
            ...
            ]
        """
        
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an client relationship expert for finding client's interested/uninterested PIMCO product."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            logprobs=None,
            # temperature=0.5,
            # n=1  # Ensures only one result is returned
        )

        return response.choices[0].message.content.strip()
 

  
class PreferenceParser:
    def __init__(self, client_preference):
        self.client_preference = client_preference

    def extract_product_lists(self):
        """
        Extract interested and uninterested product lists from the response.
        """
        interested_match = re.search(r'Interested products list: \[(.*?)\]', self.client_preference, re.DOTALL)
        uninterested_match = re.search(r'Uninterested products list: \[(.*?)\]', self.client_preference, re.DOTALL)

        interested_products = [
            item.strip().strip('"') for item in re.split(r',\s*', interested_match.group(1))
        ] if interested_match else []

        uninterested_products = [
            item.strip().strip('"') for item in re.split(r',\s*', uninterested_match.group(1))
        ] if uninterested_match else []

        return interested_products, uninterested_products

    def extract_product_details(self):
        """
        Extract detailed explanations for interested and uninterested products.
        """
        # Clean up response text to avoid unexpected issues
        sanitized_client_preference = self.client_preference.strip()

        # Regex pattern to match product details with explanation
        pattern = r"prod_name:\s*(?P<prod_name>.*?)\nexplanation:?\s*\n(?P<explanation>(?:- .*?\n)+)"
        matches = re.finditer(pattern, sanitized_client_preference, re.DOTALL)

        # Initialize lists to hold interested and uninterested products
        interested_products = []
        uninterested_products = []

        # Locate the start of the "Uninterested products" section
        uninterested_section_start = sanitized_client_preference.find("Uninterested products:")

        for match in matches:
            prod_name = match.group("prod_name").strip()
            explanation_text = match.group("explanation").strip()

            # Split explanation into a list of bullet points
            explanation = [
                line.strip("- ").strip() for line in explanation_text.splitlines() if line.startswith("-")
            ]

            # Determine whether the match belongs to interested or uninterested products
            if uninterested_section_start != -1 and match.start() > uninterested_section_start:
                uninterested_products.append({
                    "prod_name": prod_name,
                    "explanation": explanation
                })
            else:
                interested_products.append({
                    "prod_name": prod_name,
                    "explanation": explanation
                })

        return interested_products, uninterested_products






class DocumentParser:
    def __init__(self, directory_path):
        self.directory_path = directory_path

    def parse_documents(self):
     
        # List to store dictionaries with file name (without extension) and parsed data
        parsed_files = []

        for file_name in os.listdir(self.directory_path):
            if file_name.endswith(".pdf"):  # Process only PDF files
                file_path = os.path.join(self.directory_path, file_name)
                # Remove the .pdf extension
                file_name_without_ext = os.path.splitext(file_name)[0]
                # Use LlamaParse to load and parse the document
                print(f"Parsing file: {file_name_without_ext}")
                parsed_data = LlamaParse(result_type="markdown").load_data(file_path)
                # Append a dictionary with the filename (without extension) and parsed data to the list
                parsed_files.append({"file_name": file_name_without_ext, "parsed_data": parsed_data})
        return parsed_files


class QueryEngineManager:
    def __init__(self, node_parser, reranker, llm):
        self.node_parser = node_parser
        self.reranker = reranker
        self.llm = llm
        self.query_engines = {}
        self.nodes_dict = {}

    def create_query_engine_over_doc(self, docs, nodes_save_path=None):
      
        raw_nodes = self.node_parser.get_nodes_from_documents(docs)
        if nodes_save_path:
            pickle.dump(raw_nodes, open(nodes_save_path, "wb"))

        base_nodes, objects = self.node_parser.get_nodes_and_objects(raw_nodes)
        vector_index = VectorStoreIndex(nodes=base_nodes + objects)
        query_engine = vector_index.as_query_engine(
            similarity_top_k=15, node_postprocessors=[self.reranker]
        )
        return query_engine, base_nodes

    def create_query_engine_tools(self, parsed_files=None, node_path=None):
        query_engine_tools = []

        base_dir = Path(__file__).parent
        nodes_dir = base_dir / node_path

        if os.path.exists(nodes_dir):
            existing_nodes_files = list(nodes_dir.glob("*.pkl"))
            for node in existing_nodes_files:
                file_name = node.stem
                nodes = pickle.load(open(node, "rb"))
                base_nodes, objects = self.node_parser.get_nodes_and_objects(nodes)
                vector_index = VectorStoreIndex(nodes=base_nodes + objects)
                query_engine = vector_index.as_query_engine(
                    similarity_top_k=15, node_postprocessors=[self.reranker]
                )

                self.query_engines[file_name] = query_engine
                self.nodes_dict[file_name] = base_nodes
                file_name = file_name.replace("_nodes", "")
                query_engine_tools.append(
                    QueryEngineTool(
                        query_engine=query_engine,
                        metadata=ToolMetadata(
                            name=file_name,
                            description=f"Provides information about {file_name.replace('_', ' ')}"
                        )
                    )
                )
        else:
            nodes_dir.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {nodes_dir}")
        
            for file in parsed_files:
                file_name = file["file_name"]
                parsed_data = file["parsed_data"]
                nodes_save_path = nodes_dir / f"{file_name}_nodes.pkl"
                query_engine, nodes = self.create_query_engine_over_doc(parsed_data, nodes_save_path)
                self.query_engines[file_name] = query_engine
                self.nodes_dict[file_name] = nodes

                query_engine_tools.append(
                    QueryEngineTool(
                        query_engine=query_engine,
                        metadata=ToolMetadata(
                            name=file_name,
                            description=f"Provides information about {file_name.replace('_', ' ')}"
                        )
                    )
                )



        return SubQuestionQueryEngine.from_defaults(
            query_engine_tools=query_engine_tools,
            llm=self.llm,
            use_async=True,
        )

class RecommendationEngine:
    def __init__(self, sub_query_engine, filtered_products):
        self.sub_query_engine = sub_query_engine
        self.filtered_products = filtered_products

    def generate_recommendations(self, client_profile):
        query_prompt = \
        f"""
        given the client's infomation here {client_profile}, choose the best investment products 
        (could be several best products as long as aligns with clients goal and interests) from {self.filtered_products} 
        for the client based on their investment goals, risk tolerance, financial history, current portfolio, 
        and behavioral insights.

        **response format(be brief and to-the-point)**
        product1:
        product key features:
        explain how this product aligns with client's interests:

        product2:
        product key features:
        explain how this product aligns with client's interests:

        product3:
        product key features:
        explain how this product aligns with client's interests:

        ...

        """
        return self.sub_query_engine.query(query_prompt)

    def parse_recommendation_response(self, response):
        pattern = r"product\d+: (?P<prod_name>.*?)\nproduct key features: (?P<prod_features>.*?)\nexplain how this product aligns with client's interests: (?P<alignment_explanation>.*?)(?=\nproduct\d+:|$)"
        matches = re.finditer(pattern, response.response, re.DOTALL)

        RAG_selected_products = []
        for match in matches:
            product_info = {
                "prod_name": match.group("prod_name").strip(),
                "prod_features": match.group("prod_features").strip(),
                "alignment_explanation": match.group("alignment_explanation").strip()
            }
            RAG_selected_products.append(product_info)

        print(RAG_selected_products)
        return RAG_selected_products


def product_agent(client_behavior, client_chat_history, pimco_prod, client_info, directory_path):
    # API Key
    api_key = os.getenv("OPEN_AI_API_KEY")

    # Step 1: Generate client preferences
    metadata_filter = MetadataFilter(api_key, "John Doe", client_behavior, client_chat_history, pimco_prod)
    client_preference = metadata_filter.get_client_preference()
    print("Client Preference:", client_preference)

    # Step 2: Parse the preferences
    parser = PreferenceParser(client_preference)
    interested_products, uninterested_products = parser.extract_product_lists()
    interested_details, uninterested_details = parser.extract_product_details()

    # Step 3: Display results
    print("Interested Products List:", interested_products)
    print("Uninterested Products List:", uninterested_products)
    print("\nInterested Products Details:", interested_details)
    print("Uninterested Products Details:", uninterested_details)

    # Step 4: Filter products
    filtered_pimco_prod = [prod for prod in pimco_prod if prod not in uninterested_products]
    print("\nFiltered PIMCO Products:", filtered_pimco_prod)

    # API access to llama-cloud
    os.environ["LLAMA_CLOUD_API_KEY"] = os.getenv("LLAMA_CLOUD_API_KEY")
    os.environ["OPENAI_API_KEY"] = os.getenv("OPEN_AI_API_KEY")
     
    base_dir = Path(__file__).parent
    nodes_dir = base_dir / "nodes"
    if not os.path.exists(nodes_dir):
        document_parser = DocumentParser(directory_path)
        parsed_files = document_parser.parse_documents()

    # Initialize LLM, node parser, and reranker
    node_parser = MarkdownElementNodeParser(
        llm=OpenAI(model="gpt-4o"), num_workers=8
    )
    reranker = FlagEmbeddingReranker(model="BAAI/bge-reranker-large", top_n=5)
    llm = OpenAI(model="gpt-4o")

    query_engine_manager = QueryEngineManager(node_parser, reranker, llm)
    if not os.path.exists(nodes_dir):
        sub_query_engine = query_engine_manager.create_query_engine_tools(parsed_files, "nodes")
    else:
        sub_query_engine = query_engine_manager.create_query_engine_tools(node_path="nodes")

    recommendation_engine = RecommendationEngine(sub_query_engine, filtered_pimco_prod)
    client_profile = client_info

    response = recommendation_engine.generate_recommendations(client_profile)
    recommendations = recommendation_engine.parse_recommendation_response(response)

    Agent_output = {
        "interested_products_from_prefiltering": interested_details,
        "interested_products_from_RAG": recommendations
    }
    return Agent_output


def get_product_info(client, pimco_prod, pdf_directory_path):
    Agent_output = product_agent(client["client_behavior"], client["client_chat_history"], pimco_prod, client["client_investing_info"], pdf_directory_path)
    print(Agent_output)
    return Agent_output

    



