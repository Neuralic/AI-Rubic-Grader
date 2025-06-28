import os
import google.generativeai as genai
from dotenv import load_dotenv
import json

load_dotenv()

INCOMING_DIR = "incoming_pdfs"

# Ensure the directory exists (create if not)
if not os.path.exists(INCOMING_DIR):
    os.makedirs(INCOMING_DIR)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Add a print statement to check if the API key is loaded
if GEMINI_API_KEY:
    print("GEMINI_API_KEY loaded successfully.")
else:
    print("GEMINI_API_KEY not found. Please ensure it\"s set in your environment variables.")

genai.configure(api_key=GEMINI_API_KEY)

# Updated model name based on available models from Render logs
model = genai.GenerativeModel("gemini-2.5-flash")

def load_rubric(rubric_name):
    try:
        with open("rubrics.json", "r") as f:
            rubrics = json.load(f)
        return rubrics.get(rubric_name)
    except FileNotFoundError:
        print("Error: rubrics.json not found.")
        return None
    except json.JSONDecodeError:
        print("Error: Could not decode rubrics.json. Check JSON format.")
        return None

def format_rubric_for_prompt(rubric_data):
    if not rubric_data:
        return "No rubric provided."
    
    formatted_rubric = f"Rubric Name: {rubric_data.get(\'name\', \'N/A\')}\n"
    formatted_rubric += f"Description: {rubric_data.get(\'description\', \'N/A\')}\n\n"
    
    for criterion in rubric_data.get(\'criteria\', []):
        formatted_rubric += f"Criteria: {criterion.get(\'title\', \'N/A\')} ({criterion.get(\'points\', 0)} points)\n"
        formatted_rubric += f"Description: {criterion.get(\'description\', \'N/A\')}\n"
        formatted_rubric += "\n"
    return formatted_rubric

def grade_assignment(assignment_text, rubric_name="generic"):
    rubric_data = load_rubric(rubric_name)
    formatted_rubric = format_rubric_for_prompt(rubric_data)

    if not rubric_data:
        return {"error": f"Rubric \'{rubric_name}\' not found or could not be loaded."}

    prompt = f"""You are an AI assistant acting as a Professional Lecturer or a Senior Teacher. Your task is to grade assignments based on the provided rubric. 
    
    Here is the rubric for the assignment:
    {formatted_rubric}

    Here is the student\"s assignment:
    {assignment_text}

    Please provide a detailed grading based on the rubric, including a score for each criterion and overall feedback. 
    Format your response as a JSON object with the following keys:
    - \"student_name\": [Student's Name, extracted from the assignment if possible, otherwise 'Unknown']
    - \"overall_grade\": [Overall percentage grade, e.g., '85%']
    - \"feedback\": [Overall comprehensive feedback]
    - \"criteria_scores\": [
        {
            \"criterion\": [Criterion Name],
            \"score\": [Score for this criterion],
            \"justification\": [Brief justification based on the rubric and submission],
            \"detalle\": [Where points were lost, if applicable]
        }
        // ... for each criterion
    ]
    
    Ensure the output is a valid JSON object only, with no additional text or formatting outside the JSON.
    """

    try:
        response = model.generate_content(prompt)
        print(f"Type of response from model.generate_content: {type(response)}")
        print(f"Content of response from model.generate_content: {response}")

        if hasattr(response, 'text'):
            try:
                # Attempt to parse the response text as JSON
                json_response = json.loads(response.text)
                return json_response
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from model response: {e}")
                print(f"Raw model response text: {response.text}")
                return {"error": "Failed to parse AI response as JSON", "raw_response": response.text}
        elif isinstance(response, str):
            try:
                json_response = json.loads(response)
                return json_response
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from model response (string): {e}")
                print(f"Raw model response (string): {response}")
                return {"error": "Failed to parse AI response as JSON", "raw_response": response}
        else:
            # Fallback for unexpected types, try to convert to string and then parse JSON
            try:
                json_response = json.loads(str(response))
                return json_response
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from model response (other type): {e}")
                print(f"Raw model response (other type): {str(response)}")
                return {"error": "Failed to parse AI response as JSON", "raw_response": str(response)}
    except Exception as e:
        return {"error": f"Error during grading: {e}"}

if __name__ == "__main__":
    # Example usage:
    sample_assignment = """The student solved the quadratic equation x^2 - 4x + 4 = 0 by factoring. They correctly identified that the equation factors to (x-2)^2 = 0, and thus x=2. The steps were clear and easy to follow. However, they did not show any work for how they arrived at the factored form.
"""
    feedback = grade_assignment(sample_assignment, "generic")
    print(feedback)

    sample_assignment_history = """The essay discusses the causes of World War I. It mentions the assassination of Archduke Franz Ferdinand and the alliance system. However, it lacks in-depth analysis of other contributing factors like imperialism and militarism. The essay is well-structured but has some grammatical errors.
"""
    feedback_history = grade_assignment(sample_assignment_history, "generic")
    print(feedback_history)


