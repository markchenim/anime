"""
Mix edge-tts audio files into the rendered video.
Each audio file has a start time offset in seconds.
"""
import subprocess
import os
import glob

BASE = os.path.dirname(os.path.abspath(__file__))
PROJECT = "crow-water"
AUDIO_DIR = os.path.join(BASE, PROJECT, "audio")
RENDER_DIR = os.path.join(BASE, PROJECT, "renders")

# Audio cues: (filename, start_seconds)
cues = [
    ("crow_title", 0),
    ("crow_find", 4),
    ("crow_idea", 5.5),
    ("crow_drop1", 6),
    ("crow_water_up", 13.5),
    ("crow_moral", 16),
]

# Find the latest rendered mp4
mp4s = glob.glob(os.path.join(RENDER_DIR, "*.mp4"))
if not mp4s:
    print("No rendered MP4 found!")
    exit(1)
video_path = max(mp4s, key=os.path.getmtime)
print(f"Video: {video_path}")

# Get video duration
dur_str = subprocess.check_output([
    "ffprobe", "-v", "error", "-show_entries", "format=duration",
    "-of", "default=noprint_wrappers=1:nokey=1", video_path
]).decode().strip()
video_dur = float(dur_str)
print(f"Video duration: {video_dur}s")

filter_parts = []
inputs = ["-i", video_path]
audio_count = 0

for fname, start_sec in cues:
    audio_file = os.path.join(AUDIO_DIR, f"{fname}.mp3")
    if not os.path.exists(audio_file):
        print(f"  SKIP missing: {audio_file}")
        continue
    idx = len(inputs) // 2  # next input index
    inputs.extend(["-i", audio_file])
    delay_ms = int(start_sec * 1000)
    filter_parts.append(f"[{idx}:a]adelay={delay_ms}|{delay_ms}[a{idx}]")
    audio_count += 1

if not filter_parts:
    print("No audio files to mix!")
    exit(1)

# Mix all audio, use duration=longest so it covers the full video
amix_labels = "".join(f"[a{i+1}]" for i in range(audio_count))
# Use apad to extend the mixed audio to video duration
filter_expr = (
    ";".join(filter_parts) + 
    f";{amix_labels}amix=inputs={audio_count}:duration=longest:dropout_transition=0,apad=whole_dur={video_dur}[outa]"
)

output_path = video_path.replace(".mp4", "_voiced.mp4")

cmd = [
    "ffmpeg", "-y",
    *inputs,
    "-filter_complex", filter_expr,
    "-map", "0:v",
    "-map", "[outa]",
    "-c:v", "copy",
    "-c:a", "aac",
    output_path
]

print(f"Mixing {audio_count} audio tracks...")
subprocess.run(cmd, check=True)

# Replace original
os.replace(output_path, video_path)
print(f"Done! Output: {video_path}")
