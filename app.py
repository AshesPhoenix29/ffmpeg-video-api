from flask import Flask, request, jsonify, send_file
import subprocess
import requests
import os
import uuid

app = Flask(__name__)

@app.route('/build-video', methods=['POST'])
def build_video():
    data = request.json
    video_url = data['videoUrl']
    audio_url = data['audioUrl']
    job_id = str(uuid.uuid4())[:8]
    
    bg_path = f'/tmp/bg_{job_id}.mp4'
    audio_path = f'/tmp/audio_{job_id}.mp3'
    output_path = f'/tmp/output_{job_id}.mp4'
    
    # Download background video
    r = requests.get(video_url, timeout=30)
    with open(bg_path, 'wb') as f:
        f.write(r.content)
    
    # Download audio
    r2 = requests.get(audio_url, timeout=30)
    with open(audio_path, 'wb') as f:
        f.write(r2.content)
    
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
    subprocess.run(cmd, check=True)
    
    return send_file(output_path, mimetype='video/mp4')

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

