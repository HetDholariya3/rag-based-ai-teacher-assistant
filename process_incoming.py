from flask import Flask, render_template, request
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import joblib
import requests
import google.generativeai as genai
from config import api_key


genai.configure(api_key=api_key)

app = Flask(__name__)

def create_embedding(text_list):
    r = requests.post("http://localhost:11434/api/embed", json={
        "model": "bge-m3",
        "input": text_list
    })
    embedding = r.json()['embeddings']
    return embedding

def interface_genai(prompt):
    model = genai.GenerativeModel("gemini-2.5-pro")
    response = model.generate_content(prompt)
    return response.text

df = joblib.load('embeddings.joblib')

@app.route("/", methods=["GET", "POST"])
def home():
    answer = ""
    if request.method == "POST":
        incoming_query = request.form["question"]
        quesion_embedding = create_embedding([incoming_query])[0]
        
        similarity = cosine_similarity(np.vstack(df["embedding"]), [quesion_embedding]).flatten()
        max_indx = similarity.argsort()[::-1][0:10]
        new_df = df.loc[max_indx]

        prompt = f'''
I am teaching AI/ML in my the-ultimate-job-ready-data-science-course. Here are related video subtitle chunks:

{new_df[["title", "number", "start", "end", "text"]].to_json(orient="records")}

User asked: "{incoming_query}"

You have to answer in a clear, student-friendly way.
Also specify:
- Which video number
- Start & end timestamps (in seconds)
- What content is covered

⚠ If question is not related to the course, reply:
"Sorry, I can only answer questions related to the course content."
        '''

        answer = interface_genai(prompt)

    return render_template("index.html", answer=answer)

if __name__ == "__main__":
    app.run(debug=True)
