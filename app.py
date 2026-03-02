from flask import Flask, request, jsonify, send_file, request as freq
import subprocess
import requests
import os
import uuid

app = Flask(__name__)

@app.route('/build-video', methods=['POST'])
def build_video():
    try:
        job_id = str(uuid.uuid4())[:8]
        bg_path = f'/tmp/bg_{job_id}.mp4'
        audio_path = f'/tmp/audio_{job_id}.mp3'
        output_path = f'/tmp/output_{job_id}.mp4'

        # Get URLs from form data or JSON
        data = request.json
        video_url = data['videoUrl']
        audio_url = data['audioUrl']

        # Download video
        vr = requests.get(video_url, timeout=60, headers={'User-Agent': 'Mozilla/5.0'})
        with open(bg_path, 'wb') as f:
            f.write(vr.content)

        # Download audio
        ar = requests.get(audio_url, timeout=60)
        with open(audio_path, 'wb') as f:
            f.write(ar.content)

        audio_size = os.path.getsize(audio_path)
        video_size = os.path.getsize(bg_path)

        if audio_size < 100:
            return jsonify({"error": f"Audio too small: {audio_size}"}), 500
        if video_size < 100:
            return jsonify({"error": f"Video too small: {video_size}"}), 500

        cmd = [
            'ffmpeg', '-y',
            '-i', bg_path,
            '-i', audio_path,
            '-vf', 'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920',
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
            '-c:a', 'aac', '-b:a', '128k',
            '-shortest',
            output_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)

        if result.returncode != 0:
            return jsonify({"error": result.stderr[-1000:]}), 500

        return send_file(output_path, mimetype='video/mp4')

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
