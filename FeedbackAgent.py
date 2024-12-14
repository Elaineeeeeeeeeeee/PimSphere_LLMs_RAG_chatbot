from autogen import ConversableAgent
import os
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env

llm_config = {
    "config_list": [{"model": "gpt-4o", "api_key": os.getenv("OPEN_AI_API_KEY")}],
}

class FeedbackAgent:
    
    def refine_report(self, llm_config, initial_report, user_feedback):
        """
        Refine the report based on user feedback.
        
        Args:
        llm_config (dict): Configuration for the language model
        initial_report (str): The initial version of the report
        user_feedback (str): User's feedback for refinement
        
        Returns:
        str: The refined report
        """
        refinement_agent = ConversableAgent(
            name="Refinement Agent",
            system_message=f"""
            You are an expert at refining reports based on specific user feedback.
            
            Original Report Location:
            {initial_report}
            
            User's Feedback: {user_feedback}
            
            Task: Modify the Report
            - Carefully read and interpret the user's feedback
            - Apply specific refinements requested
            - Maintain the core structure and key information
            - Ensure the refined report meets the user's expectations
            
            Note: In a real scenario, you would read the full report content. 
            For this demo, we're using the file path as a placeholder.
            """,
            llm_config=llm_config,
            human_input_mode="NEVER"
        )
        
        # Simulate report refinement
        messages = [
            {"role": "system", "content": f"Current report location: {initial_report}"},
            {"role": "user", "content": f"Feedback: {user_feedback}"}
        ]
        
        refined_report = refinement_agent.generate_reply(messages=messages)
        
        # Handle different possible response formats
        if isinstance(refined_report, list):
            refined_report = refined_report[0] if refined_report else "No refinement could be generated."
        elif isinstance(refined_report, dict):
            refined_report = refined_report.get('content', "No refinement could be generated.")
        
        return refined_report or "No refinement could be generated."

    # def select_report():
    #   """
    #   Function to select a report number from user input.
      
    #   Returns:
    #   str: The selected report number
    #   """
    #   while True:
    #       try:
    #           report_number = input("Please select a report number to update (1-3): ")
    #           if report_number in ['1', '2', '3']:
    #               return report_number
    #           else:
    #               print("Please enter a valid report number (1, 2, or 3).")
    #       except ValueError:
    #           print("Invalid input. Please enter 1, 2, or 3.")

    # def refine_report(self, llm_config, initial_report, user_feedback):
    #     refinement_agent = ConversableAgent(
    #         name="Refinement Agent",
    #         system_message=f"""
    #         You are an expert at refining reports based on specific user feedback.
            
    #         Original Report:
    #         {initial_report}
            
    #         User's Feedback: {user_feedback}
            
    #         Task: Modify the Report
    #         - Carefully interpret the user's feedback
    #         - Apply specific refinements requested
    #         - Maintain the core structure and key information
    #         - Ensure the refined report meets the user's expectations
    #         """,
    #         llm_config=llm_config,
    #         human_input_mode="NEVER"
    #     )
        
    #     # Generate refined report
    #     messages = [
    #         {"role": "system", "content": f"Current report: {initial_report}"},
    #         {"role": "user", "content": f"Feedback: {user_feedback}"}
    #     ]
        
    #     refined_report = refinement_agent.generate_reply(messages=messages)
        
    #     return refined_report

#   def refine_report(llm_config, initial_report):
#       """
#       Interactive report refinement process.
      
#       Args:
#       llm_config (dict): Configuration for the language model
#       initial_report (str): The initial version of the report
      
#       Returns:
#       str: The final refined report
#       """
#       current_report = generated_report
#       while True:
#           # Prompt user for direct feedback
#           user_feedback = input("Please provide feedback for the report (or type 'this is good' to finish): ")

#           # Check for termination condition
#           if user_feedback.lower() == "this is good":
#               print("User has approved the final version of the report.")
#               break  # Use break instead of return

#           # Create a new conversable agent for each refinement iteration
#           refinement_agent = ConversableAgent(
#               name="Refinement Agent",
#               system_message=f"""
#               You are an expert at refining reports based on specific user feedback. 
#               Current report:
#               {current_report}
#               User's feedback: {user_feedback}
              
#               Task: Modify the Report
#               Using the selected report and the feedback provided, generate an updated version of the report. 
#               Ensure that:
#               - the format of the updated report should still be consistent with the original report.
#               - all the other content which the user didn't mention to change should remain unchanged.
#               - All requested changes are applied.
#               - The content is clear, concise, and aligned with the user’s preferences.
#               Output: Present the updated report to the user and ask if further revisions are needed.
#               """,
#               llm_config=llm_config,
#               human_input_mode="NEVER" 
#           )

#           # Generate refined report
#           try:
#               # Use chat_messages to provide context
#               messages = [
#                   {"role": "system", "content": f"Current report: {current_report}"},
#                   {"role": "user", "content": f"Feedback: {user_feedback}"}
#               ]
              
#               refined_report_response = refinement_agent.generate_reply(messages=messages)
            
              
#               # Handle different possible response formats
#               if isinstance(refined_report_response, list):
#                   # If it's a list, try to get the first item
#                   refined_report = refined_report_response[0] if refined_report_response else None
#               elif isinstance(refined_report_response, dict):
#                   # If it's a dictionary, try to get the content
#                   refined_report = refined_report_response.get('content')
#               elif isinstance(refined_report_response, str):
#                   # If it's already a string, use it directly
#                   refined_report = refined_report_response
#               else:
#                   refined_report = None
              
#               # Check if we successfully extracted the refined report
#               if refined_report:
#                   current_report = refined_report
#                   print("\nUpdated Report:\n", current_report)
#               else:
#                   print("Error in generating refined report. Could not extract report content.")
                  
#           except Exception as e:
#               print(f"An error occurred during report refinement: {e}")