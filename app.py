from flask import Flask, request, render_template_string, redirect, url_for
import json, os, requests
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

WORDS_FILE = "arabic_words.json"

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

    words_with_translations = [(w, translations.get(w, "")) for w in words]

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <title>Arabic With AAeshah</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 30px;
                background-color: #f8f9fa;
            }
            .container {
                max-width: 900px;
                margin: 0 auto;
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            input[type="text"] {
                width: 100%;
                font-size: 18px;
                padding: 12px;
                margin-bottom: 10px;
                border: 2px solid #ddd;
                border-radius: 6px;
                direction: rtl;
                text-align: right;
            }
            input[type="submit"] {
                background-color: #007bff;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-size: 16px;
            }
            .word-list {
                margin-top: 20px;
                background-color: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
            }
            /* Styles for keyboard and mic button */
            #arabicKeyboard {
                margin-top: 15px;
                display: flex;
                flex-wrap: wrap;
                gap: 5px;
            }
            #arabicKeyboard button {
                font-size: 16px;
                padding: 8px 12px;
                border: none;
                border-radius: 4px;
                background-color: #e2e6ea;
                cursor: pointer;
            }
            #arabicKeyboard button:hover {
                background-color: #d6d8db;
            }
            #micButton {
                margin-top: 10px;
                cursor: pointer;
                font-size: 24px;
                background: none;
                border: none;
            }
            #micButton:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }
            #speechStatus {
                margin-top: 10px;
                font-style: italic;
                color: #555;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Arabic With AAeshah</h1>
            <form method="POST">
                <label>Enter an Arabic word:</label><br>
                <input type="text" name="new_word" id="new_word" autocomplete="off" autofocus />
                <input type="submit" value="Add Word" />
            </form>
            <p>{{ message }}</p>

            <!-- Arabic Keyboard -->
            <h3>Arabic Keyboard</h3>
            <div id="arabicKeyboard">
                <button onclick="insertChar('ا')">ا</button>
                <button onclick="insertChar('ب')">ب</button>
                <button onclick="insertChar('ت')">ت</button>
                <button onclick="insertChar('ث')">ث</button>
                <button onclick="insertChar('ج')">ج</button>
                <button onclick="insertChar('ح')">ح</button>
                <button onclick="insertChar('خ')">خ</button>
                <button onclick="insertChar('د')">د</button>
                <button onclick="insertChar('ذ')">ذ</button>
                <button onclick="insertChar('ر')">ر</button>
                <button onclick="insertChar('ز')">ز</button>
                <button onclick="insertChar('س')">س</button>
                <button onclick="insertChar('ش')">ش</button>
                <button onclick="insertChar('ص')">ص</button>
                <button onclick="insertChar('ض')">ض</button>
                <button onclick="insertChar('ط')">ط</button>
                <button onclick="insertChar('ظ')">ظ</button>
                <button onclick="insertChar('ع')">ع</button>
                <button onclick="insertChar('غ')">غ</button>
                <button onclick="insertChar('ف')">ف</button>
                <button onclick="insertChar('ق')">ق</button>
                <button onclick="insertChar('ك')">ك</button>
                <button onclick="insertChar('ل')">ل</button>
                <button onclick="insertChar('م')">م</button>
                <button onclick="insertChar('ن')">ن</button>
                <button onclick="insertChar('ه')">ه</button>
                <button onclick="insertChar('و')">و</button>
                <button onclick="insertChar('ي')">ي</button>
                <button onclick="insertChar('ء')">ء</button>
                <button onclick="insertChar('ئ')">ئ</button>
                <button onclick="insertChar('ؤ')">ؤ</button>
                <button onclick="insertChar('ة')">ة</button>
                <button onclick="insertChar('َ')">َ</button>
                <button onclick="insertChar('ُ')">ُ</button>
                <button onclick="insertChar('ِ')">ِ</button>
                <button onclick="insertChar('ً')">ً</button>
                <button onclick="insertChar('ٌ')">ٌ</button>
                <button onclick="insertChar('ٍ')">ٍ</button>
                <button onclick="insertChar('ْ')">ْ</button>
                <button onclick="insertChar('ٓ')">ٓ</button>
                <button onclick="clearInput()">Clear</button>
            </div>
            <!-- Microphone Button -->
            <button id="micButton" title="Speak" onclick="startRecognition()">🎤</button>
            <div id="speechStatus"></div>

            <!-- Word list -->
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
            <p style="margin-top:20px;">
                <a href="{{ url_for('practice') }}" style="background-color:#007bff; color:white; padding:10px 20px; text-decoration:none; border-radius:6px;">Start Practice</a>
            </p>
        </div>

        <script>
        function insertChar(char) {
            const input = document.getElementById('new_word');
            input.value += char;
        }
        function clearInput() {
            document.getElementById('new_word').value = '';
        }

        // Speech Recognition
        var recognition;
        function startRecognition() {
            const statusDiv = document.getElementById('speechStatus');
            if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
                alert("Sorry, your browser doesn't support Speech Recognition.");
                return;
            }

            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition();
            recognition.lang = 'ar-SA'; // Arabic dialect
            recognition.interimResults = false;
            recognition.maxAlternatives = 1;

            recognition.onstart = () => {
                document.getElementById('speechStatus').innerText = 'Listening...';
            };
            recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                document.getElementById('new_word').value += transcript;
                document.getElementById('speechStatus').innerText = 'Recognized: ' + transcript;
            };
            recognition.onerror = (event) => {
                document.getElementById('speechStatus').innerText = 'Error: ' + event.error;
            };
            recognition.onend = () => {
                document.getElementById('speechStatus').innerText = '';
            };
            recognition.start();
        }
        </script>
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
        prompt = f"Use the following Arabic words in a sentence: {', '.join(words)}. Then ask a related question in Arabic."
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
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 30px;
                background-color: #f8f9fa;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            input[type="text"] {
                width: 100%;
                font-size: 18px;
                padding: 12px;
                margin-bottom: 15px;
                border: 2px solid #ddd;
                border-radius: 6px;
                direction: rtl;
                text-align: right;
            }
            input[type="submit"] {
                background-color: #007bff;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-size: 16px;
            }
            .feedback {
                background-color: #d4edda;
                border: 1px solid #c3e6cb;
                color: #155724;
                padding: 12px;
                border-radius: 6px;
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Practice</h1>
            <p><strong>Sentence:</strong> {{ sentence }}</p>
            <p><strong>Question:</strong> {{ question }}</p>

            <form method="POST">
                <input type="hidden" name="question" value="{{ question }}" />
                <label>Your answer:</label><br>
                <input type="text" name="user_answer" value="{{ user_answer }}" autocomplete="off" />
                <input type="submit" value="Check Answer" />
            </form>

            <!-- Same Arabic keyboard as in index -->
            <h3>Arabic Keyboard</h3>
            <div id="arabicKeyboard" style="margin-top: 10px; display: flex; flex-wrap: wrap; gap: 5px;">
                <button onclick="insertChar('ا')">ا</button>
                <button onclick="insertChar('ب')">ب</button>
                <button onclick="insertChar('ت')">ت</button>
                <button onclick="insertChar('ث')">ث</button>
                <button onclick="insertChar('ج')">ج</button>
                <button onclick="insertChar('ح')">ح</button>
                <button onclick="insertChar('خ')">خ</button>
                <button onclick="insertChar('د')">د</button>
                <button onclick="insertChar('ذ')">ذ</button>
                <button onclick="insertChar('ر')">ر</button>
                <button onclick="insertChar('ز')">ز</button>
                <button onclick="insertChar('س')">س</button>
                <button onclick="insertChar('ش')">ش</button>
                <button onclick="insertChar('ص')">ص</button>
                <button onclick="insertChar('ض')">ض</button>
                <button onclick="insertChar('ط')">ط</button>
                <button onclick="insertChar('ظ')">ظ</button>
                <button onclick="insertChar('ع')">ع</button>
                <button onclick="insertChar('غ')">غ</button>
                <button onclick="insertChar('ف')">ف</button>
                <button onclick="insertChar('ق')">ق</button>
                <button onclick="insertChar('ك')">ك</button>
                <button onclick="insertChar('ل')">ل</button>
                <button onclick="insertChar('م')">م</button>
                <button onclick="insertChar('ن')">ن</button>
                <button onclick="insertChar('ه')">ه</button>
                <button onclick="insertChar('و')">و</button>
                <button onclick="insertChar('ي')">ي</button>
                <button onclick="insertChar('ء')">ء</button>
                <button onclick="insertChar('ئ')">ئ</button>
                <button onclick="insertChar('ؤ')">ؤ</button>
                <button onclick="insertChar('ة')">ة</button>
                <button onclick="insertChar('َ')">َ</button>
                <button onclick="insertChar('ُ')">ُ</button>
                <button onclick="insertChar('ِ')">ِ</button>
                <button onclick="insertChar('ً')">ً</button>
                <button onclick="insertChar('ٌ')">ٌ</button>
                <button onclick="insertChar('ٍ')">ٍ</button>
                <button onclick="insertChar('ْ')">ْ</button>
                <button onclick="insertChar('ٓ')">ٓ</button>
                <button onclick="clearInput()">Clear</button>
            </div>
            <!-- Microphone -->
            <button id="micButton" title="Speak" onclick="startRecognition()">🎤</button>
            <div id="speechStatus"></div>

            <p style="margin-top:20px;">
                <a href="{{ url_for('index') }}" style="background-color:#6c757d; color:white; padding:10px 20px; text-decoration:none; border-radius:6px;">Back to word list</a>
            </p>
        </div>

        <script>
        function insertChar(char) {
            const input = document.querySelector('input[name="user_answer"]');
            input.value += char;
        }
        function clearInput() {
            document.querySelector('input[name="user_answer"]').value = '';
        }

        // Speech Recognition
        var recognition;
        function startRecognition() {
            const statusDiv = document.getElementById('speechStatus');
            if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
                alert("Sorry, your browser doesn't support Speech Recognition.");
                return;
            }
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition();
            recognition.lang = 'ar-SA'; // Arabic dialect
            recognition.interimResults = false;
            recognition.maxAlternatives = 1;

            recognition.onstart = () => {
                document.getElementById('speechStatus').innerText = 'Listening...';
            };
            recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                document.querySelector('input[name="user_answer"]').value += transcript;
                document.getElementById('speechStatus').innerText = 'Recognized: ' + transcript;
            };
            recognition.onerror = (event) => {
                document.getElementById('speechStatus').innerText = 'Error: ' + event.error;
            };
            recognition.onend = () => {
                document.getElementById('speechStatus').innerText = '';
            };
            recognition.start();
        }
        </script>
    </body>
    </html>
    """, sentence=sentence, question=question, feedback=feedback, user_answer=user_answer)

if __name__ == "__main__":
    app.run(debug=True)