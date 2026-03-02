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
        data = request.json
        video_url = data['videoUrl']
        job_id = str(uuid.uuid4())[:8]
        
        bg_path = f'/tmp/bg_{job_id}.mp4'
        audio_path = f'/tmp/audio_{job_id}.mp3'
        output_path = f'/tmp/output_{job_id}.mp4'
        
        # Download background video
        r = requests.get(video_url, timeout=60)
        with open(bg_path, 'wb') as f:
            f.write(r.content)
        
        # Handle audio - either base64 or URL
        if 'audioBase64' in data:
            audio_bytes = base64.b64decode(data['audioBase64'])
            with open(audio_path, 'wb') as f:
                f.write(audio_bytes)
        elif 'audioUrl' in data:
            r2 = requests.get(data['audioUrl'], timeout=60)
            with open(audio_path, 'wb') as f:
                f.write(r2.content)
        
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
            return jsonify({"error": result.stderr}), 500
            
        return send_file(output_path, mimetype='video/mp4')
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
