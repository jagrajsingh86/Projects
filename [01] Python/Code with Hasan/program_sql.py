from flask import Flask, request, jsonify
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "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"))
import pandas as pd
import os

app = Flask(__name__)

# Dictionary to store DataFrames, keyed by filenames or session identifiers
data_storage = {}

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    filename = file.filename

    # Load file into a DataFrame
    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(file)
        elif filename.endswith('.xlsx'):
            df = pd.read_excel(file)
        else:
            return jsonify({"error": "Unsupported file type"}), 400

        # Store DataFrame in memory
        data_storage[filename] = df
        return jsonify({"message": f"File {filename} uploaded successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/ask', methods=['POST'])
def ask_openai():
    data = request.get_json()
    user_question = data.get("question")
    filename = data.get("filename")

    # Validate inputs
    if not user_question or filename not in data_storage:
        return jsonify({"error": "Invalid question or filename"}), 400

    # Access DataFrame from memory
    df = data_storage[filename]

    # Here, you may process the DataFrame based on the question
    # For simplicity, we are sending a summary of the data to OpenAI
    sample_data = df.head(5).to_string()

    try:
        response = client.completions.create(model="text-davinci-003",
        prompt=f"{user_question}\n\nSample Data:\n{sample_data}",
        max_tokens=150)
        answer = response.choices[0].text.strip()

        return jsonify({"answer": answer})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
