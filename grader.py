# grader.py
import os
import google.generativeai as genai
from dotenv import load_dotenv

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
    print("GEMINI_API_KEY not found. Please ensure it's set in your environment variables.")

genai.configure(api_key=GEMINI_API_KEY)

def list_available_models():
    print("Attempting to list available Gemini models...")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"Available model: {m.name}")
    except Exception as e:
        print(f"Error listing models: {e}")

# Call this function at startup to log available models
list_available_models()

# Updated model name based on available models from Render logs
model = genai.GenerativeModel("gemini-2.5-flash")

def load_rubric(course_name):
    # Hardcoded sample for now - later load from file or DB
    if course_name == "math":
        return """Rubric for Math Assignment:

Criteria 1: Problem Solving (40 points)
- 40 points: Demonstrates a complete understanding of the problem, applies appropriate strategies, and arrives at a correct solution with clear and logical steps.
- 30 points: Demonstrates a good understanding of the problem, applies mostly appropriate strategies, and arrives at a nearly correct solution with minor errors in steps.
- 20 points: Demonstrates some understanding of the problem, applies some appropriate strategies, but the solution contains significant errors or is incomplete.
- 10 points: Demonstrates minimal understanding of the problem, applies inappropriate strategies, and the solution is largely incorrect.

Criteria 2: Mathematical Reasoning (30 points)
- 30 points: Provides clear, concise, and accurate mathematical reasoning to support the solution. Uses appropriate mathematical language and notation.
- 20 points: Provides mostly clear and accurate mathematical reasoning, but may have minor inconsistencies or less precise language/notation.
- 10 points: Provides limited or unclear mathematical reasoning, with several inconsistencies or inappropriate language/notation.
- 5 points: Lacks mathematical reasoning or provides incorrect reasoning.

Criteria 3: Presentation and Communication (20 points)
- 20 points: Solution is well-organized, legible, and easy to follow. All steps are clearly communicated.
- 15 points: Solution is generally organized and legible, but may have minor issues in clarity or flow.
- 10 points: Solution is somewhat disorganized or difficult to read, with several communication issues.
- 5 points: Solution is disorganized and illegible, making it difficult to understand.

Criteria 4: Timeliness (10 points)
- 10 points: Assignment submitted on time.
- 0 points: Assignment submitted late.

Overall Feedback: Provide constructive feedback on strengths and areas for improvement. Suggest specific actions for the student to take to improve their understanding or performance.
"""
    elif course_name == "history":
        return """Rubric for History Essay:

Criteria 1: Historical Accuracy (40 points)
- 40 points: All historical facts, dates, and events are accurate and well-supported by evidence.
- 30 points: Mostly accurate historical facts, dates, and events, with minor inaccuracies or less robust evidence.
- 20 points: Several historical inaccuracies or insufficient evidence to support claims.
- 10 points: Significant historical inaccuracies or lack of factual basis.

Criteria 2: Argumentation and Analysis (30 points)
- 30 points: Presents a clear, compelling thesis statement and supports it with strong, well-reasoned arguments and insightful analysis.
- 20 points: Presents a thesis statement and arguments, but the analysis may be less developed or occasionally lack depth.
- 10 points: Weak or unclear thesis statement, with limited argumentation and superficial analysis.
- 5 points: Lacks a thesis statement, arguments are absent or illogical, and analysis is minimal.

Criteria 3: Organization and Structure (20 points)
- 20 points: Essay is logically organized with a clear introduction, body paragraphs, and conclusion. Transitions are smooth and effective.
- 15 points: Essay is generally organized, but may have minor issues with flow or paragraph coherence.
- 10 points: Essay is somewhat disorganized, with unclear transitions or a weak overall structure.
- 5 points: Essay is disorganized and illegible, making it difficult to understand.

Criteria 4: Source Integration and Citation (10 points)
- 10 points: Integrates sources effectively and cites them correctly using a consistent citation style.
- 0 points: Integrates sources poorly or cites them incorrectly/inconsistently.

Overall Feedback: Provide constructive feedback on strengths and areas for improvement. Suggest specific actions for the student to take to improve their understanding or performance.
"""
    else:
        return "No rubric found for this course."

def grade_assignment(assignment_text):
    # For now, let's assume the course is 'math' for demonstration purposes
    course_name = "math"
    rubric = load_rubric(course_name)

    if rubric == "No rubric found for this course.":
        return "Error: No rubric found for the specified course."

    prompt = f"""You are an AI assistant designed to grade assignments based on a provided rubric. 
    
    Here is the rubric for the {course_name} assignment:
    {rubric}

    Here is the student's assignment:
    {assignment_text}

    Please provide a detailed grading based on the rubric, including a score for each criterion and overall feedback. 
    Format your response clearly, starting with the criterion name, followed by the score, and then a brief justification. 
    Finally, provide an overall score and comprehensive feedback.
    """

    try:
        response = model.generate_content(prompt)
        print(f"Type of response from model.generate_content: {type(response)}")
        print(f"Content of response from model.generate_content: {response}")

        if hasattr(response, 'text'):
            return response.text
        elif isinstance(response, str):
            return response
        else:
            # Fallback for unexpected types, try to convert to string
            return str(response)
    except Exception as e:
        return f"Error during grading: {e}"

if __name__ == "__main__":
    # Example usage:
    sample_assignment = """The student solved the quadratic equation x^2 - 4x + 4 = 0 by factoring. They correctly identified that the equation factors to (x-2)^2 = 0, and thus x=2. The steps were clear and easy to follow. However, they did not show any work for how they arrived at the factored form.
"""
    feedback = grade_assignment(sample_assignment)
    print(feedback)

    sample_assignment_history = """The essay discusses the causes of World War I. It mentions the assassination of Archduke Franz Ferdinand and the alliance system. However, it lacks in-depth analysis of other contributing factors like imperialism and militarism. The essay is well-structured but has some grammatical errors.
"""
    feedback_history = grade_assignment(sample_assignment_history)
    print(feedback_history)


