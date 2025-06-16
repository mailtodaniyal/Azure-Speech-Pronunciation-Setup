from flask import Flask, request, render_template
import azure.cognitiveservices.speech as speechsdk
import os
import json
import matplotlib.pyplot as plt
import tempfile
import subprocess

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

if not os.path.exists('uploads'):
    os.makedirs('uploads')

if not os.path.exists('static'):
    os.makedirs('static')

speech_key = "AZURE_SPEECH_KEY"
service_region = "AZURE_SERVICE_REGION"

def extract_audio(file_path):
    if file_path.endswith('.mp4') or file_path.endswith('.mov'):
        audio_path = file_path.rsplit('.', 1)[0] + '.wav'
        subprocess.run([
            'ffmpeg', '-i', file_path, '-vn', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1', audio_path
        ], check=True)
        return audio_path
    return file_path

def analyze_pronunciation(audio_file_path, reference_text):
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    audio_input = speechsdk.AudioConfig(filename=audio_file_path)
    pronunciation_config = speechsdk.PronunciationAssessmentConfig(
        reference_text=reference_text,
        grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
        granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
        enable_miscue=True)
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_input)
    pronunciation_config.apply_to(recognizer)
    result = recognizer.recognize_once()
    json_result = json.loads(result.properties.get(speechsdk.PropertyId.SpeechServiceResponse_JsonResult))
    return json_result

def create_chart(scores):
    labels = ['Accuracy', 'Fluency', 'Completeness', 'Pronunciation']
    values = [
        scores.get('AccuracyScore', 0),
        scores.get('FluencyScore', 0),
        scores.get('CompletenessScore', 0),
        scores.get('PronunciationScore', 0)
    ]
    plt.figure(figsize=(6, 4))
    plt.bar(labels, values, color=['blue', 'green', 'orange', 'red'])
    plt.ylim(0, 100)
    plt.ylabel('Score (%)')
    plt.title('Pronunciation Assessment Scores')
    chart_path = os.path.join('static', 'result.png')
    plt.savefig(chart_path)
    plt.close()
    return chart_path

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    chart_path = None
    if request.method == 'POST':
        file = request.files['audio']
        reference_text = request.form['text']
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        audio_path = extract_audio(file_path)
        result = analyze_pronunciation(audio_path, reference_text)
        chart_path = create_chart(result['PronunciationAssessment'])
    return render_template('index.html', result=result, chart_path=chart_path)

if __name__ == '__main__':
    app.run(debug=True)
