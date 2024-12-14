from autogen import ConversableAgent
import os
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env

llm_config = {
    "config_list": [{"model": "gpt-4o", "api_key": os.getenv("OPEN_AI_API_KEY")}],
}

class ReportAgent:
    def __init__(self, client, client_personal_data, product_node_output):
        self.client_data = client_personal_data
        self.topics = client["topic_content"]
        self.product_node_output = product_node_output
        self.meeting = client["client_personal_info"]["num_meetings"]

    def num_topics(self):
      return len(self.topics)

    def get_initial_report_generation_prompt(self, num_versions):
      return f'''
      You are tasked with preparing {num_versions} distinct reports for a client meeting. Use only the provided information to ensure accuracy and prevent hallucination.

      **Client & Product Information**
      {self.client_data}
      {self.product_node_output}

      **Topics of Interest**
      {self.topics}

      **Report Generation Guidelines**
      For this scenario, generate {num_versions} reports, each at least 500 words long. 
      Each report should:
      1. **Begin with a summary of the client's personal interests (40% of the content):**
        - Begin with small talk and personalized talking points based on their preferences.
        - Highlight how their interests align with potential financial or investment goals.

      2. **Follow with a discussion of the client's recent activities, professional interests, and the given topics (30% of the content):**
        - Address all provided topics, prioritizing one or two primary topics in each report while covering others briefly.
        - Rotate focus across reports so that each topic receives primary attention in at least one report.
        - Relate these discussions to relevant product offerings where applicable.

      3. **Integrate product information prominently (30% of the content):**
        - Mention all products from `{self.product_node_output}` across the reports, but vary the emphasis for each report.
        - For each highlighted product:
          - Summarize its key features and benefits.
          - Explain how it aligns with the client's stated interests or needs (e.g., risk tolerance, investment horizon).
          - Reference any specific actions or expressions of interest from the client (e.g., downloaded reports, mentioned in chat history).
        - Provide tailored recommendations for highlighted products based on their alignment with the client’s profile.

      4. **Include relevant questions for the client throughout each report:**
        - Use these questions to confirm alignment between their goals and suggested products.
        - Encourage dialogue about their preferences or any additional needs.

      5. Ensure that at least 40% of the content consists of small talk and talking points based on the client's personal interests.

      6. Incorporate insights and recommendations derived solely from the provided client and product information.

      7. Avoid introducing any information not explicitly provided in the input data.

      **Formatting Guidelines:**
      - Format each report in short and concise bullet points only.
      - Maintain a professional yet personable tone suitable for an initial client meeting.
      - Conclude each report with actionable next steps or recommendations.

      **When generating multiple reports:**
      - Assign unique titles to each report as "Report1", "Report2", ..., up to "Report{num_versions}" with a subject name that reflects the primary topic of the report.
      - Cycle through topics, giving each topic primary focus in turn while integrating relevant product details.
      - Vary product emphasis across reports:
        - Ensure that all products are mentioned across the set of reports but highlight different combinations in each version.
        - Compare products briefly where relevant to highlight distinctions and suitability for specific client needs.
        - Revisit topics or products from different perspectives if the number of reports exceeds available topics/products.
      - Ensure each report offers a unique viewpoint or approach, even when revisiting a topic or product.

      **Additional Notes on Product Integration:**
      - For each product mentioned in `{self.product_node_output}`:
        - Include its name, key features, and any alignment explanations provided in the data.
        - Emphasize how it addresses specific client needs or preferences (e.g., risk tolerance, income generation).
        - If multiple products are relevant, compare them briefly to highlight distinctions and suitability.
        - Use product-related insights to inform actionable recommendations or next steps for discussion during the meeting.

      Remember, do not invent or assume any information beyond what is explicitly provided in the client data, product data, topics, and previous meeting information (for follow-up meetings).

      Generate these distinct reports following these guidelines.
      '''

    def get_followup_report_generation_prompt(self, num_versions):
      return f'''
      You are tasked with preparing {num_versions} distinct reports for a follow-up client meeting. Use only the provided information to ensure accuracy and prevent hallucination.

      **Client & Product Information**
      {self.client_data}
      {self.product_node_output}

      **Topics of Interest**
      {self.topics}

      **Follow-up Meeting Guidelines**
      For this scenario, generate {num_versions} reports, each at least 500 words long. Each report should:

      1. **Begin with small talk and follow-ups from the last meeting (20% of the content):**
        - Reference key points or actions from the last meeting: {self.meeting}.
        - Incorporate relevant personal details to maintain rapport.

      2. **Provide a brief summary of the last meeting's content (20% of the content):**
        - Highlight any progress, decisions, or updates since the last discussion.
        - Ensure this section is concise and factual.

      3. **Focus on recent activities, product information, and topics of interest (60% of the content):**
        - Cover all provided topics, emphasizing any new developments or changes since the last meeting.
        - Rotate focus across reports so that each topic receives primary attention in at least one report.
        - Relate topics to relevant product offerings where applicable.

      4. **Integrate product information prominently:**
        - Mention all products from `{self.product_node_output}` across the reports, but vary the emphasis.
        - For each highlighted product:
          - Summarize its key features and benefits.
          - Explain how it aligns with the client’s stated interests or needs (e.g., risk tolerance, investment horizon).
          - Reference any specific actions or expressions of interest from the client (e.g., downloaded reports, mentioned in chat history).
        - Provide tailored recommendations for highlighted products based on their alignment with the client’s profile.

      5. **Conclude with actionable next steps or recommendations:**
        - Suggest specific actions based on progress made since the last meeting.
        - Tailor recommendations to align with updated client goals or preferences.

      **Formatting Guidelines:**
      - Format each report in short and concise bullet points only.
      - Maintain a professional yet personable tone suitable for a follow-up client meeting.
      - Ensure all statements are factual and derived solely from the provided data.

      **When generating multiple reports:**
      - Assign unique titles to each report as "Report1", "Report2", ..., up to "Report{num_versions}" with a subject name that reflects the primary topic of the report.
      - Cycle through topics, giving each topic primary focus in turn while integrating relevant product details.
      - Vary product emphasis across reports:
        - Ensure that all products are mentioned across the set of reports but highlight different combinations in each version.
        - Compare products briefly where relevant to highlight distinctions and suitability for specific client needs.
        - Revisit topics or products from different perspectives if the number of reports exceeds available topics/products.
      - Ensure each report offers a unique viewpoint or approach, even when revisiting a topic or product.

      **Additional Notes on Product Integration:**
      - For each product mentioned in `{self.product_node_output}`:
        - Include its name, key features, and any alignment explanations provided in the data.
        - Emphasize how it addresses specific client needs or preferences (e.g., risk tolerance, income generation).
        - If multiple products are relevant, compare them briefly to highlight distinctions and suitability.
        - Use product-related insights to inform actionable recommendations or next steps for discussion during the meeting.

      Remember, do not invent or assume any information beyond what is explicitly provided in the client data, product data, topics, and previous meeting information.

      Generate these distinct reports following these guidelines.
      '''

    def generate_report(self):
      prompt_report_initial_generation = self.get_initial_report_generation_prompt(self.num_topics())
      prompt_report_followup_generation = self.get_followup_report_generation_prompt(self.num_topics())

      # Generate Report - Initial Meeting
      # input: client info, topics
      # output: dictionary of topics and filtered client info
      report_init_generation_agent = ConversableAgent(
          name="Report Generation Agent",
          system_message=prompt_report_initial_generation,
          llm_config=llm_config,
          code_execution_config=False,
          human_input_mode="NEVER",
      )

      # Generate Report - Follow-up Meetings
      # input: client info, topics, meeting info
      # output: dictionary of topics, meetings, and filtered client info
      report_followup_generation_agent = ConversableAgent(
          name="Report Generation Agent",
          system_message=prompt_report_followup_generation,
          llm_config=llm_config,
          code_execution_config=False,
          human_input_mode="NEVER",
      )

      if self.meeting == 0:
        reply = report_init_generation_agent.generate_reply(
            messages=[{"content": "Generate the report.", "role": "user"}]
        )
      else:
        reply = report_followup_generation_agent.generate_reply(
          messages=[{"content": "Generate the report.", "role": "user"}]
      )

      return reply