from flask import Flask, request, jsonify
from flask_cors import CORS
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import JSONFormatter
from http import HTTPStatus
from gensim.summarization import summarize
from googletrans import Translator
import json

app = Flask(__name__)
CORS(app)


def transcript_to_text(transcript):
    formatter = JSONFormatter()
    json_formatted = formatter.format_transcript(transcript)
    parsed_transcript = json.loads(json_formatted)
    speech_text = " ".join([item['text'] for item in parsed_transcript])
    return speech_text


@app.errorhandler(400)
@app.errorhandler(404)
@app.errorhandler(500)
def handle_error(e):
    error_code = e.code
    error_message = HTTPStatus(e.code).phrase
    return f'Bad Request! Error: {error_code}, {error_message}'


@app.route('/api/summarize/lsa', methods=['GET'])
def summarize_lsa():
    youtube_url = request.args.get('youtube_url')
    max_length = int(request.args.get('max_length', 200))

    if not youtube_url:
        return jsonify({"error": "Missing 'youtube_url' parameter"}), 400

    video_id = youtube_url.split("v=")[1]
    transcript = YouTubeTranscriptApi.get_transcript(video_id)

    if not transcript:
        return jsonify({"error": "Video has no subtitles"}), 400

    script = transcript_to_text(transcript)

    # Perform extractive summarization using LSA
    summary_lsa = summarize(script, word_count=max_length)

    return jsonify({"summary_lsa": summary_lsa})


@app.route('/api/summarize/t5', methods=['GET'])
def summarize_t5():
    youtube_url = request.args.get('youtube_url')
    max_length = int(request.args.get('max_length', 200))
    translate_to_english = request.args.get('translate_to_english', 'false').lower() == 'true'

    if not youtube_url:
        return jsonify({"error": "Missing 'youtube_url' parameter"}), 400

    video_id = youtube_url.split("v=")[1]
    transcript = YouTubeTranscriptApi.get_transcript(video_id)

    if not transcript:
        return jsonify({"error": "Video has no subtitles"}), 400

    script = transcript_to_text(transcript)

    # Perform abstractive summarization using T5
    summary_t5 = text_summary_t5_tokenizer(script, translate_to_english=translate_to_english)

    return jsonify({"summary_t5": summary_t5})


if __name__ == '__main__':
    app.run(debug=True)
