import os
import json
from flask import Flask, request, render_template_string, redirect, url_for
from dotenv import load_dotenv
import google.generativeai as genai
import re
from google.cloud import translate_v2 as translate # Import Google Cloud Translation API

app = Flask(__name__)
load_dotenv()

# Configure Gemini API (for text generation)
print(f"DEBUG: GOOGLE_APPLICATION_CREDENTIALS loaded: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Configure Google Cloud Translation API
# The library automatically looks for GOOGLE_APPLICATION_CREDENTIALS environment variable
# pointing to your service account key file.
translate_client = translate.Client()

WORDS_FILE = "arabic_words.json"

# This dictionary will now primarily store manually added words and their translations.
# Dynamically generated words will be translated on-the-fly.
# You can pre-fill this with common words if you like.
translations = {
    "كتاب": "book",
    "مدرسة": "school",
    "قلم": "pen",
    "تفاحة": "apple",
    "ماء": "water",
    "مدينة": "city",
    "بيت": "house",
    "باب": "door",
    "هو": "he",
    "هي": "she",
    "في": "in",
    "قريب": "near",
    "من": "from / of",
}

def list_models():
    """Prints all available models for debugging purposes."""
    models = genai.list_models()
    print("\n--- Available Gemini Models ---")
    for model in models:
        print(model)
    print("--- End Model List ---\n")

# Uncomment the line below to run this once and see available models in your console
# list_models()

def load_words():
    """Loads Arabic words from a JSON file."""
    if os.path.exists(WORDS_FILE):
        with open(WORDS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_words(words):
    """Saves Arabic words to a JSON file."""
    with open(WORDS_FILE, "w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False, indent=2)

def get_english_translation(text):
    """Translates Arabic text to English using Google Cloud Translation API."""
    try:
        # The target language for translation
        target = 'en'
        # The source language is 'ar' (Arabic)
        source = 'ar'

        # Text is assumed to be a single word or a short phrase for this context
        result = translate_client.translate(text, target_language=target, source_language=source)
        return result['translatedText']
    except Exception as e:
        print(f"Error translating '{text}': {e}")
        return "Translation Error" # Fallback if translation fails

def generate_with_gemini(prompt_text):
    """Generates content using the specified Gemini model and handles responses."""
    model = genai.GenerativeModel("models/gemma-3-12b-it") # Ensure this model is valid

    try:
        response = model.generate_content(prompt_text)

        # --- DEBUGGING OUTPUT ---
        print("\n--- Gemini Response Debug ---")
        print(f"Prompt sent: '{prompt_text}'")
        print(f"Response object type: {type(response)}")
        # --- END DEBUGGING OUTPUT ---

        if response.candidates:
            candidate = response.candidates[0]
            # --- DEBUGGING OUTPUT ---
            print(f"Candidate finish reason: {candidate.finish_reason}")
            print(f"Candidate content object (full dump): {candidate.content}")
            # --- END DEBUGGING OUTPUT ---

            if candidate.content and candidate.content.parts and hasattr(candidate.content.parts[0], 'text'):
                generated_text = candidate.content.parts[0].text
                print(f"Successfully extracted text content (first 100 chars): '{generated_text[:100]}...'")
                return generated_text
            else:
                print("Error: Candidate content structure is not as expected (missing parts or text in first part).")
                return "No text content could be extracted from the model's response."
        else:
            print("No candidates returned in the response.")
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                print(f"Prompt blocked due to: {response.prompt_feedback.block_reason}")
                print(f"Safety ratings: {response.prompt_feedback.safety_ratings}")
            return "No content could be generated for this prompt (blocked or empty response)."

    except Exception as e:
        print(f"An error occurred during content generation: {e}")
        return f"An error occurred: {e}"

def parse_sentence_and_question(generated_text):
    """Parses the generated text to extract the Arabic sentence and question."""
    sentence = "No sentence found."
    question = "No question found."

    sentence_match = re.search(r'\*\*Sentence:\*\*\s*(.*?)(?:\s*\*\*Translation:|\s*\*\*Question:|$)', generated_text, re.DOTALL)
    if sentence_match:
        sentence = sentence_match.group(1).strip()
        sentence = re.sub(r'\s*\([^)]*\)\s*', '', sentence).strip()

    question_match = re.search(r'\*\*Question:\*\*\s*(.*?)(?:\s*\*\*Translation:|\s*\*\*Breakdown:|$)', generated_text, re.DOTALL)
    if question_match:
        question = question_match.group(1).strip()
        question = re.sub(r'\s*\([^)]*\)\s*', '', question).strip()

    if sentence == "No sentence found." and "؟" in generated_text:
        parts = generated_text.split("؟", 1)
        sentence_candidate = parts[0].strip()
        if sentence_candidate and not sentence_candidate.endswith("؟"):
             sentence = sentence_candidate

        question_candidate = parts[1].strip() + "؟" if parts[1].strip() else "ما السؤال المتعلق بهذه الجملة؟"
        if question_candidate and len(question_candidate.split()) > 2:
            question = question_candidate

    if sentence and not re.search(r'[.؟!]$', sentence) and sentence != "No sentence found.":
        sentence += "."

    if question and not question.endswith("؟") and question != "No question found.":
        question += "؟"

    if not question or question == "No question found.":
        question = "ما السؤال المتعلق بهذه الجملة؟"

    return sentence, question

@app.route("/", methods=["GET", "POST"])
def index():
    words = load_words()
    message = ""

    if request.method == "POST":
        new_word = request.form.get("new_word", "").strip()
        if new_word:
            # If a new word is added, dynamically translate it and add to translations
            if new_word not in translations:
                translated_word = get_english_translation(new_word)
                translations[new_word] = translated_word
                print(f"Dynamically translated '{new_word}' to '{translated_word}' and added to translations.")

            if new_word not in words:
                words.append(new_word)
                save_words(words)
                message = f'Word "{new_word}" added.'
            elif new_word in words:
                message = f'Word "{new_word}" already exists.'
        else:
            message = "Please enter a valid word."

    words_with_translations = [(w, translations.get(w, "")) for w in words]

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <title>Arabic With AAeshah</title>
        <style>
            body { font-family: Arial; background-color: #f8f9fa; margin: 30px; }
            .container { max-width: 900px; margin: auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            input[type="text"] { width: 100%; font-size: 18px; padding: 12px; margin-bottom: 10px; border: 2px solid #ddd; border-radius: 6px; direction: rtl; text-align: right; }
            input[type="submit"] { background-color: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; }
            .word-list { margin-top: 20px; background-color: #f8f9fa; padding: 20px; border-radius: 8px; }
            #arabicKeyboard, #arabicKeyboardPractice { margin-top: 15px; display: flex; flex-wrap: wrap; gap: 5px; }
            #arabicKeyboard button, #arabicKeyboardPractice button { font-size: 16px; padding: 8px 12px; border: none; border-radius: 4px; background-color: #e2e6ea; cursor: pointer; }
            #arabicKeyboard button:hover, #arabicKeyboardPractice button:hover { background-color: #d6d8db; }
            #micButton, #micButtonPractice { margin-top: 10px; cursor: pointer; font-size: 24px; background: none; border: none; }

            /* Tooltip Styles */
            .arabic-word-with-translation {
                position: relative;
                display: inline-block;
                cursor: help; /* Changes cursor to a question mark */
                border-bottom: 1px dotted #888; /* Dotted underline */
            }

            .arabic-word-with-translation .tooltip-text {
                visibility: hidden;
                width: auto; /* Adjust width based on content */
                background-color: #555;
                color: #fff;
                text-align: center;
                border-radius: 6px;
                padding: 5px 10px;
                position: absolute;
                z-index: 1;
                bottom: 125%; /* Position above the text */
                left: 50%;
                margin-left: -50%; /* Center the tooltip */
                opacity: 0;
                transition: opacity 0.3s;
                white-space: nowrap; /* Keep translation on one line */
                direction: ltr; /* Ensure tooltip text is LTR */
                text-align: left; /* Align tooltip text left */
            }

            .arabic-word-with-translation .tooltip-text::after {
                content: "";
                position: absolute;
                top: 100%;
                left: 50%;
                margin-left: -5px;
                border-width: 5px;
                border-style: solid;
                border-color: #555 transparent transparent transparent;
            }

            .arabic-word-with-translation:hover .tooltip-text {
                visibility: visible;
                opacity: 1;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Arabic With AAeshah</h1>
            <form method="POST">
                <label>Enter an Arabic word:</label>
                <input type="text" name="new_word" id="new_word" autocomplete="off" />
                <input type="submit" value="Add Word" />
            </form>
            <p>{{ message }}</p>

            <h3>Arabic Keyboard</h3>
            <div id="arabicKeyboard">
                {% for char in "ابتثجحخدذرزسشصضطظعغفقكلمنهويءئؤةًٌٍَُِْٓ" %}
                    <button type="button" onclick="insertChar('{{ char }}', 'new_word')">{{ char }}</button>
                {% endfor %}
                <button type="button" onclick="clearInput('new_word')">Clear</button>
            </div>

            <button type="button" id="micButton" onclick="startRecognition('new_word')">🎤</button>
            <div id="speechStatus"></div>

            <div class="word-list">
                <h2>Your Words</h2>
                <ul>
                    {% for word, translation in words_with_translations %}
                        <li><strong>{{ word }}</strong>{% if translation %} - {{ translation }}{% endif %}</li>
                    {% else %}
                        <li>No words added yet.</li>
                    {% endfor %}
                </ul>
            </div>

            <p>
                <a href="{{ url_for('practice') }}" style="background-color:#007bff; color:white; padding:10px 20px; text-decoration:none; border-radius:6px;">Start Practice</a>
            </p>
        </div>

        <script>
        function insertChar(char, targetId) {
            const inputField = document.getElementById(targetId);
            if (inputField) {
                inputField.value += char;
            }
        }
        function clearInput(targetId) {
            const inputField = document.getElementById(targetId);
            if (inputField) {
                inputField.value = '';
            }
        }

        var recognition;
        function startRecognition(targetId) {
            const statusDiv = document.getElementById(targetId === 'new_word' ? 'speechStatus' : 'speechStatusPractice');
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRecognition) {
                alert("Speech Recognition not supported in this browser.");
                if (statusDiv) statusDiv.textContent = "Speech Recognition not supported.";
                return;
            }

            recognition = new SpeechRecognition();
            recognition.lang = 'ar-SA';
            recognition.interimResults = false;
            recognition.maxAlternatives = 1;

            recognition.onstart = () => { if (statusDiv) statusDiv.textContent = "🎙 Listening..."; };
            recognition.onerror = (event) => { if (statusDiv) statusDiv.textContent = "❌ Error: " + event.error; };
            recognition.onend = () => { if (statusDiv) statusDiv.textContent = "Stopped."; };
            recognition.onresult = (event) => {
                let transcript = event.results[0][0].transcript;
                const inputField = document.getElementById(targetId);
                if (inputField) {
                    inputField.value += transcript;
                }
                if (statusDiv) statusDiv.textContent = "✅ You said: " + transcript;
            };
            recognition.start();
        }
        </script>
    </body>
    </html>
    """, words_with_translations=words_with_translations, message=message)


@app.route("/practice", methods=["GET", "POST"])
def practice():
    sentence = ""
    question = ""
    user_answer = ""
    feedback = ""
    sentence_words_with_translations = [] # New variable for individual words

    words = load_words()

    if not words:
        return redirect(url_for("index"))

    if request.method == "POST":
        user_answer = request.form.get("user_answer", "").strip()
        question = request.form.get("question", "").strip()
        original_sentence = request.form.get("original_sentence", "").strip()

        # Re-process the original sentence for display with translations
        sentence_parts = re.findall(r'\b\w+\b|[.,!?;]', original_sentence) # Improved tokenization
        for word_part in sentence_parts:
            # Clean the word by removing punctuation for lookup
            cleaned_word = re.sub(r'[.?!,]', '', word_part)
            translation = translations.get(cleaned_word, None) # Check if pre-defined
            if translation is None: # If not pre-defined, get dynamic translation
                translation = get_english_translation(cleaned_word)

            sentence_words_with_translations.append({'arabic': word_part, 'english': translation})
        sentence = original_sentence # Set sentence back for display

        feedback = "✅ تم استلام إجابتك!" if user_answer else "❌ الرجاء إدخال إجابة."
    else:
        # Prompt model to generate an Arabic sentence and question
        prompt = f"Write a simple Arabic sentence containing the following words: {', '.join(words)}. Then write a question related to it."
        generated = generate_with_gemini(prompt)
        sentence, question = parse_sentence_and_question(generated)

        # Process the generated sentence into individual words with translations
        # Improved regex to split words but keep punctuation separate, or handle common attached punctuation
        sentence_parts = re.findall(r'\b\w+\b|[.,!?;]', sentence) # This regex splits words and keeps punctuation as separate "words"
        for word_part in sentence_parts:
            # Clean the word by removing punctuation for lookup in translations
            cleaned_word = re.sub(r'[.?!,]', '', word_part) # Remove punctuation for lookup
            translation = translations.get(cleaned_word, None) # Check if pre-defined

            if translation is None and cleaned_word: # If not pre-defined AND it's a valid word (not just punctuation)
                translation = get_english_translation(cleaned_word)
            elif not cleaned_word: # If it's just punctuation, no translation
                translation = ""
            elif translation is None: # Fallback if cleaned_word is empty but translation is None
                translation = "No translation available"

            sentence_words_with_translations.append({'arabic': word_part, 'english': translation})


    return render_template_string("""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8" />
        <title>Practice - Arabic With AAeshah</title>
        <style>
            body { font-family: Arial; background-color: #f0f0f0; margin: 30px; direction: rtl; }
            .container { max-width: 900px; margin: auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            label, h2 { font-weight: bold; margin-top: 20px; }
            textarea { width: 100%; font-size: 20px; padding: 12px; border: 2px solid #ddd; border-radius: 6px; direction: rtl; text-align: right; }
            input[type="submit"] { margin-top: 20px; background-color: #28a745; color: white; padding: 12px 24px; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; }
            .feedback { margin-top: 20px; font-size: 18px; color: #333; }
            .back-link { margin-top: 20px; display: inline-block; color: #007bff; text-decoration: none; }
            /* Styles for the keyboard (shared with index for consistency) */
            #arabicKeyboard, #arabicKeyboardPractice { margin-top: 15px; display: flex; flex-wrap: wrap; gap: 5px; }
            #arabicKeyboard button, #arabicKeyboardPractice button { font-size: 16px; padding: 8px 12px; border: none; border-radius: 4px; background-color: #e2e6ea; cursor: pointer; }
            #arabicKeyboard button:hover, #arabicKeyboardPractice button:hover { background-color: #d6d8db; }
            #micButton, #micButtonPractice { margin-top: 10px; cursor: pointer; font-size: 24px; background: none; border: none; }

            /* Tooltip Styles (copied from index and applied here too) */
            .arabic-word-with-translation {
                position: relative;
                display: inline-block;
                cursor: help; /* Changes cursor to a question mark */
                border-bottom: 1px dotted #888; /* Dotted underline */
                font-size: 24px; /* Make the sentence larger */
                margin-left: 5px; /* Add some space between words */
            }

            .arabic-word-with-translation .tooltip-text {
                visibility: hidden;
                width: auto; /* Adjust width based on content */
                background-color: #555;
                color: #fff;
                text-align: center;
                border-radius: 6px;
                padding: 5px 10px;
                position: absolute;
                z-index: 1;
                bottom: 125%; /* Position above the text */
                left: 50%;
                transform: translateX(-50%); /* Center the tooltip perfectly */
                opacity: 0;
                transition: opacity 0.3s;
                white-space: nowrap; /* Keep translation on one line */
                direction: ltr; /* Ensure tooltip text is LTR */
                text-align: left; /* Align tooltip text left */
            }

            .arabic-word-with-translation .tooltip-text::after {
                content: "";
                position: absolute;
                top: 100%;
                left: 50%;
                margin-left: -5px;
                border-width: 5px;
                border-style: solid;
                border-color: #555 transparent transparent transparent;
            }

            .arabic-word-with-translation:hover .tooltip-text {
                visibility: visible;
                opacity: 1;
            }
            .sentence-display {
                font-size: 24px; /* Ensure the whole sentence section is larger */
                text-align: right;
                line-height: 1.8; /* Improve readability */
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>تمرين القراءة والكتابة</h2>
            <form method="POST">
                <p><strong>الجملة:</strong> <span class="sentence-display">
                    {% for word_data in sentence_words_with_translations %}
                        <span class="arabic-word-with-translation">
                            {{ word_data.arabic }}
                            {% if word_data.english %}
                                <span class="tooltip-text">{{ word_data.english }}</span>
                            {% endif %}
                        </span>
                    {% endfor %}
                </span></p>
                <p><strong>السؤال:</strong> {{ question }}</p>
                <input type="hidden" name="question" value="{{ question }}">
                <input type="hidden" name="original_sentence" value="{{ sentence }}"> <label for="user_answer">إجابتك:</label>
                <textarea name="user_answer" id="user_answer" rows="4" required>{{ user_answer }}</textarea>

                <h3>لوحة المفاتيح العربية</h3>
                <div id="arabicKeyboardPractice">
                    {% for char in "ابتثجحخدذرزسشصضطظعغفقكلمنهويءئؤةًٌٍَُِْٓ" %}
                        <button type="button" onclick="insertChar('{{ char }}', 'user_answer')">{{ char }}</button>
                    {% endfor %}
                    <button type="button" onclick="clearInput('user_answer')">مسح</button>
                </div>

                <button type="button" id="micButtonPractice" onclick="startRecognition('user_answer')">🎤</button>
                <div id="speechStatusPractice"></div>

                <input type="submit" value="أرسل الإجابة">
            </form>

            {% if feedback %}
                <div class="feedback">{{ feedback }}</div>
            {% endif %}

            <p>
                <a class="back-link" href="{{ url_for('index') }}">⟵ الرجوع إلى الصفحة الرئيسية</a>
            </p>
        </div>

        <script>
        function insertChar(char, targetId) {
            const inputField = document.getElementById(targetId);
            if (inputField) {
                inputField.value += char;
            }
        }
        function clearInput(targetId) {
            const inputField = document.getElementById(targetId);
            if (inputField) {
                inputField.value = '';
            }
        }

        var recognition;
        function startRecognition(targetId) {
            const statusDiv = document.getElementById(targetId === 'new_word' ? 'speechStatus' : 'speechStatusPractice');
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRecognition) {
                alert("Speech Recognition not supported in this browser.");
                if (statusDiv) statusDiv.textContent = "Speech Recognition not supported.";
                return;
            }

            recognition = new SpeechRecognition();
            recognition.lang = 'ar-SA';
            recognition.interimResults = false;
            recognition.maxAlternatives = 1;

            recognition.onstart = () => { if (statusDiv) statusDiv.textContent = "🎙 Listening..."; };
            recognition.onerror = (event) => { if (statusDiv) statusDiv.textContent = "❌ Error: " + event.error; };
            recognition.onend = () => { if (statusDiv) statusDiv.textContent = "Stopped."; };
            recognition.onresult = (event) => {
                let transcript = event.results[0][0].transcript;
                const inputField = document.getElementById(targetId);
                if (inputField) {
                    inputField.value += transcript;
                }
                if (statusDiv) statusDiv.textContent = "✅ You said: " + transcript;
            };
            recognition.start();
        }
        </script>
    </body>
    </html>
    """, sentence=sentence, question=question, user_answer=user_answer, feedback=feedback,
    sentence_words_with_translations=sentence_words_with_translations)

if __name__ == "__main__":
    app.run(debug=True)