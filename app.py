from flask import Flask, request, jsonify, send_file
import subprocess
import requests
import os
import uuid
import base64

app = Flask(__name__)

@app.route('/build-video', methods=['POST'])
def build_video():
    data = request.json
    video_url = data['videoUrl']
    audio_base64 = data['audioBase64']
    job_id = str(uuid.uuid4())[:8]
    
    bg_path = f'/tmp/bg_{job_id}.mp4'
    audio_path = f'/tmp/audio_{job_id}.mp3'
    output_path = f'/tmp/output_{job_id}.mp4'
    
    # Download background video
    r = requests.get(video_url, timeout=60)
    with open(bg_path, 'wb') as f:
        f.write(r.content)
    
    # Decode audio from base64
    audio_data = base64.b64decode(audio_base64)
    with open(audio_path, 'wb') as f:
        f.write(audio_data)
    
    # Build video with ffmpeg
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
    subprocess.run(cmd, check=True, timeout=120)
    
    return send_file(output_path, mimetype='video/mp4')

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
