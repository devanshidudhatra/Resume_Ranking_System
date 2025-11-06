from sentence_transformers import SentenceTransformer, util

# Load a pre-trained BERT model optimized for sentence embeddings
bert_model = SentenceTransformer('all-MiniLM-L6-v2')

def calculate_relevancy(extracted_data, job_description):
    """
    Calculates relevancy between a resume (extracted_data) and a job description using BERT embeddings.
    """

    # Join resume sections
    resume_text = " ".join([
        " ".join(extracted_data.get("skills", [])),
        " ".join(extracted_data.get("education", [])),
        " ".join(extracted_data.get("experience", []))
    ])

    # Join job description sections
    job_desc_text = " ".join([
        " ".join(job_description.get("required_skills", [])),
        " ".join(job_description.get("required_education", [])),
        " ".join(job_description.get("required_experience", []))
    ])

    # Compute embeddings
    resume_embedding = bert_model.encode(resume_text, convert_to_tensor=True)
    job_desc_embedding = bert_model.encode(job_desc_text, convert_to_tensor=True)

    # Cosine similarity
    similarity_score = util.cos_sim(resume_embedding, job_desc_embedding).item()

    # Convert to percentage
    relevancy_score = round(similarity_score * 100, 2)

    return relevancy_score

def interpret_score(score):
    if score > 85:
        return "Excellent Match"
    elif score > 70:
        return "Good Match"
    elif score > 50:
        return "Moderate Match"
    else:
        return "Low Match"
