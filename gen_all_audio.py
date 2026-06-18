import asyncio
import edge_tts
import os
import subprocess

VOICE = "zh-CN-XiaoxiaoNeural"

# 乌鸦喝水配音脚本
lines_crow = [
    ("crow_title", "乌鸦喝水"),
    ("crow_find", "瓶子里面有水，但水太少了，喝不到"),
    ("crow_idea", "有办法了！"),
    ("crow_drop1", "一颗一颗地往里扔"),
    ("crow_water_up", "水慢慢升上来了"),
    ("crow_moral", "遇事要善于动脑筋想办法"),
]

# 龟兔赛跑配音脚本
lines_turtle = [
    ("turtle_title", "龟兔赛跑"),
    ("turtle_start", "比赛开始了！"),
    ("turtle_rabbit_fast", "兔子一马当先，跑得飞快"),
    ("turtle_sleep", "这乌龟太慢了，我先睡一觉"),
    ("turtle_tortoise_walk", "乌龟一步一步，坚持不懈地向前爬"),
    ("turtle_wakeup", "兔子醒来，发现乌龟快到终点了！"),
    ("turtle_win", "乌龟赢了！"),
    ("turtle_moral", "骄兵必败，持之以恒"),
]

async def gen_audio(filename, text, output_dir):
    """Stream audio from edge-tts, pipe through ffmpeg to produce valid mp3."""
    os.makedirs(output_dir, exist_ok=True)
    final_mp3 = os.path.join(output_dir, f"{filename}.mp3")

    communicate = edge_tts.Communicate(text, VOICE)

    # Collect all audio chunks
    audio_data = b''
    async for chunk in communicate.stream():
        if chunk['type'] == 'audio':
            audio_data += chunk['data']

    if not audio_data:
        print(f"  FAIL {filename}: no audio data")
        return

    # Pipe raw data through ffmpeg. Must use -f mp3 for pipe input.
    result = subprocess.run([
        "ffmpeg", "-y", "-v", "error",
        "-f", "mp3", "-i", "pipe:0",
        "-codec:a", "libmp3lame", "-b:a", "128k",
        "-ar", "44100",
        final_mp3
    ], input=audio_data, capture_output=True)

    if result.returncode != 0:
        print(f"  FAIL {filename}: ffmpeg error: {result.stderr.decode()[-200:]}")
        return

    dur = float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", final_mp3
    ]).decode().strip())
    print(f"  OK: {filename}.mp3 ({dur:.1f}s)")

async def main():
    base = os.path.dirname(os.path.abspath(__file__))

    print("=== 乌鸦喝水 ===")
    for fname, text in lines_crow:
        await gen_audio(fname, text, os.path.join(base, "crow-water", "audio"))

    print("\n=== 龟兔赛跑 ===")
    for fname, text in lines_turtle:
        await gen_audio(fname, text, os.path.join(base, "turtle-rabbit", "audio"))

    print("\nDone!")

asyncio.run(main())
