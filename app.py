from flask import Flask, request, render_template_string, redirect, url_for
import json
import os
import requests
from dotenv import load_dotenv
app = Flask(__name__)
load_dotenv()  # Load variables from .env


WORDS_FILE = "arabic_words.json"

# Example Arabic to English dictionary for hover tooltips
translations = {
    "كتاب": "book",
    "مدرسة": "school",
    "قلم": "pen",
    "تفاحة": "apple",
    "ماء": "water"
}



HF_API_URL = "https://api-inference.huggingface.co/models/akhooli/arabic-gpt2"
HF_API_TOKEN = os.getenv("HF_API_TOKEN")

headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}

def load_words():
    if os.path.exists(WORDS_FILE):
        with open(WORDS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_words(words):
    with open(WORDS_FILE, "w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False, indent=2)

def hf_generate(prompt):
    payload = {"inputs": prompt, "parameters": {"max_new_tokens": 60}}
    response = requests.post(HF_API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list) and len(data) > 0 and "generated_text" in data[0]:
            return data[0]["generated_text"]
        else:
            return "Sorry, could not generate text."
    else:
        return f"Error: {response.status_code} - {response.text}"

@app.route("/", methods=["GET", "POST"])
def index():
    words = load_words()
    message = ""

    if request.method == "POST":
        new_word = request.form.get("new_word", "").strip()
        if new_word and new_word not in words:
            words.append(new_word)
            save_words(words)
            message = f'Word "{new_word}" added.'
        elif new_word in words:
            message = f'Word "{new_word}" already exists.'
        else:
            message = "Please enter a valid word."

    # Prepare a list of tuples: (arabic_word, translation or empty)
    words_with_translations = [(w, translations.get(w, "")) for w in words]

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <title>Arabic With AAeshah</title>
      <style>
        body { font-family: Arial, sans-serif; margin: 30px; }
        .word-tooltip {
          border-bottom: 1px dotted #000;
          cursor: help;
          position: relative;
        }
        .word-tooltip:hover::after {
          content: attr(data-translation);
          position: absolute;
          left: 0;
          bottom: 125%;
          background: #333;
          color: #fff;
          padding: 4px 8px;
          border-radius: 4px;
          white-space: nowrap;
          z-index: 10;
          font-size: 0.9em;
        }
      </style>
    </head>
    <body>
      <h1>Arabic With AAeshah</h1>
      <form method="POST">
        <label>Enter an Arabic word:</label><br>
        <input type="text" name="new_word" autofocus autocomplete="off" />
        <input type="submit" value="Add Word" />
      </form>
      <p>{{ message }}</p>
      <h2>Your Words</h2>
      <ul>
        {% for word, translation in words_with_translations %}
          <li>
            <span class="word-tooltip" {% if translation %}data-translation="{{ translation }}"{% endif %}>
              {{ word }}
            </span>
          </li>
        {% else %}
          <li>No words added yet.</li>
        {% endfor %}
      </ul>
      <a href="{{ url_for('practice') }}">Start Practice</a>
    </body>
    </html>
    """, words_with_translations=words_with_translations, message=message)

@app.route("/practice", methods=["GET", "POST"])
def practice():
    words = load_words()
    sentence = ""
    question = ""
    feedback = ""
    user_answer = ""

    if not words:
        return redirect(url_for("index"))

    if request.method == "POST":
        user_answer = request.form.get("user_answer", "").strip()
        question = request.form.get("question", "")

        if user_answer and question:
            feedback = "Answer received. (Answer evaluation coming soon.)"

    else:
        prompt = (f"Use the following Arabic words in a sentence: {', '.join(words)}. "
                  "Then ask a related question in Arabic.")

        generated = hf_generate(prompt)

        if "؟" in generated:
            parts = generated.split("؟")
            sentence = parts[0].strip() + "؟"
            question = parts[1].strip()
        else:
            sentence = generated.strip()
            question = "Can you answer this?"

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <title>Practice - Arabic With AAeshah</title>
    </head>
    <body>
      <h1>Practice</h1>
      <p><strong>Sentence:</strong> {{ sentence }}</p>
      <p><strong>Question:</strong> {{ question }}</p>

      <form method="POST">
        <input type="hidden" name="question" value="{{ question }}" />
        <label>Your answer:</label><br>
        <input type="text" name="user_answer" value="{{ user_answer }}" autofocus autocomplete="off" />
        <input type="submit" value="Check Answer" />
      </form>

      {% if feedback %}
        <p><strong>Feedback:</strong> {{ feedback }}</p>
      {% endif %}

      <p><a href="{{ url_for('index') }}">Back to word list</a></p>
    </body>
    </html>
    """, sentence=sentence, question=question, feedback=feedback, user_answer=user_answer)

if __name__ == "__main__":
    app.run(debug=True)
