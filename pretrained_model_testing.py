from pyresparser import ResumeParser

def parse_resume(file_path):
    data = ResumeParser(file_path).get_extracted_data()
    return data

# Example usage
if __name__ == "__main__":
    resume_path = input("Enter path to resume (PDF or DOCX): ")
    result = parse_resume(resume_path)
    
    print("\n=== Resume Analysis Results ===")
    print(result)

# import spacy

# # Load the model to check if it works
# nlp = spacy.load("en_core_web_sm")
# print("Model loaded successfully!")
