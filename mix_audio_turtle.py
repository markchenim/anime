"""
Mix edge-tts audio files into the rendered turtle-rabbit video.
"""
import subprocess
import os
import glob

BASE = os.path.dirname(os.path.abspath(__file__))
PROJECT = "turtle-rabbit"
AUDIO_DIR = os.path.join(BASE, PROJECT, "audio")
RENDER_DIR = os.path.join(BASE, PROJECT, "renders")

cues = [
    ("turtle_title", 0),
    ("turtle_start", 2.5),
    ("turtle_rabbit_fast", 3.3),
    ("turtle_sleep", 6),
    ("turtle_tortoise_walk", 7),
    ("turtle_wakeup", 13),
    ("turtle_win", 14.5),
    ("turtle_moral", 17),
]

mp4s = glob.glob(os.path.join(RENDER_DIR, "*.mp4"))
if not mp4s:
    print("No rendered MP4 found!")
    exit(1)
video_path = max(mp4s, key=os.path.getmtime)
print(f"Video: {video_path}")

dur_str = subprocess.check_output([
    "ffprobe", "-v", "error", "-show_entries", "format=duration",
    "-of", "default=noprint_wrappers=1:nokey=1", video_path
]).decode().strip()
video_dur = float(dur_str)
print(f"Video duration: {video_dur}s")

inputs = ["-i", video_path]
filter_parts = []

for fname, start_sec in cues:
    audio_file = os.path.join(AUDIO_DIR, f"{fname}.mp3")
    if not os.path.exists(audio_file):
        print(f"  SKIP missing: {audio_file}")
        continue
    idx = len(inputs) // 2
    inputs.extend(["-i", audio_file])
    delay_ms = int(start_sec * 1000)
    filter_parts.append(f"[{idx}:a]adelay={delay_ms}:all=1[a{idx}]")
    print(f"  {fname}: delay={delay_ms}ms")

if not filter_parts:
    print("No audio files to mix!")
    exit(1)

audio_count = len(filter_parts)
amix_inputs = "".join(f"[a{i+1}]" for i in range(audio_count))
filter_expr = (
    f"anullsrc=channel_layout=stereo:sample_rate=44100:duration={video_dur}[silence];"
    + ";".join(filter_parts) + ";"
    + f"[silence]{amix_inputs}amix=inputs={audio_count + 1}:duration=longest:dropout_transition=0,volume=2[outa]"
)

output_path = video_path.replace(".mp4", "_voiced.mp4")

cmd = [
    "ffmpeg", "-y", "-v", "error",
    *inputs,
    "-filter_complex", filter_expr,
    "-map", "0:v",
    "-map", "[outa]",
    "-c:v", "copy",
    "-c:a", "aac",
    output_path
]

print(f"Mixing {audio_count} audio tracks...")
result = subprocess.run(cmd, capture_output=True)
if result.returncode != 0:
    print(f"FFmpeg error:\n{result.stderr.decode()[-500:]}")
    exit(1)

os.replace(output_path, video_path)
print(f"Done! Output: {video_path}")
