import streamlit as st
from autogen import ConversableAgent
from pydantic import ConfigDict
from Data import Data

import os
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env

llm_config = {
    "config_list": [{"model": "gpt-4o", "api_key": os.getenv("OPEN_AI_API_KEY")}],
}

class ClientAgent:
    def __init__(self, client_name):
        self.client_name = client_name
        self.client = Data.clients[client_name]
        self.topics = Data.clients[client_name]["topic_content"]

    def process_client_data(self):
        # Proceed with processing only if verification is successful
        client_prompt = f'''
        You are a helpful customer onboarding agent specializing in filtering and organizing client information based on specific topics of interest. Your task is to analyze the provided client data and topics, and generate two outputs in a dictionary format:
        1. Topics-related professional information
        2. Personal interests and talking points for a client meeting

        For each output, follow these guidelines:

        1. Analyze the provided client data and topics.
        2. Extract and organize relevant information from the client data.
        3. Ensure that no irrelevant or sensitive information is included in the output.
        4. Present the filtered information in a structured format.

        Present the filtered information in the following format:

        {{
        "professional_information": {{
            "topic1": [relevant information],
            "topic2": [relevant information],
            "topic3": [relevant information]
        }},
        "personal_interests": [relevant information 1, information 2, etc...]
        }}

        Client data: {self.client}
        Topics: {self.topics}
        '''

        # Instantiate client agent with the prompt
        client_agent = ConversableAgent(
        name="Client Agent",
        system_message=client_prompt,
        llm_config=llm_config,
        code_execution_config=False,
        human_input_mode="NEVER",
        )

        # Generate reply
        reply = client_agent.generate_reply(
                messages=[{"content": "Show me the result.", "role": "user"}]
            )

        # Parse the reply (you might need to adjust this based on the actual response format)
        import json
        try:
            processed_data = json.loads(reply)
            # print(processed_data)
            return processed_data
        except json.JSONDecodeError:
            # print("Could not parse the agent's response")
            return {"professional_information": {}, "personal_interests": []}