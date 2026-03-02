from flask import Flask, request, jsonify, send_file
import subprocess
import requests
import os
import uuid
import base64

app = Flask(__name__)

@app.route('/build-video', methods=['POST'])
def build_video():
    try:
        job_id = str(uuid.uuid4())[:8]
        bg_path = f'/tmp/bg_{job_id}.mp4'
        audio_path = f'/tmp/audio_{job_id}.mp3'
        output_path = f'/tmp/output_{job_id}.mp4'

        # Get raw bytes from request
        data = request.json
        video_url = data['videoUrl']
        audio_b64 = data['audioBase64']

        # Download video
        vr = requests.get(video_url, timeout=60)
        with open(bg_path, 'wb') as f:
            f.write(vr.content)

        # Decode audio - strip any whitespace/newlines first
        audio_b64_clean = audio_b64.strip().replace('\n','').replace('\r','').replace(' ','')
        # Add padding if needed
        padding = 4 - len(audio_b64_clean) % 4
        if padding != 4:
            audio_b64_clean += '=' * padding
        
        audio_bytes = base64.b64decode(audio_b64_clean)
        with open(audio_path, 'wb') as f:
            f.write(audio_bytes)

        # Verify audio file size
        audio_size = os.path.getsize(audio_path)
        if audio_size < 1000:
            return jsonify({"error": f"Audio file too small: {audio_size} bytes"}), 500

        # Build video
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
            return jsonify({"error": result.stderr[-500:]}), 500

        return send_file(output_path, mimetype='video/mp4')

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
