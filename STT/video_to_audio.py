import ffmpeg
import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

video_folder = os.path.join(BASE_DIR, "videos")
audio_folder = os.path.join(BASE_DIR, "audio")
processed_file = os.path.join(BASE_DIR, "processed_video.json")

os.makedirs(video_folder, exist_ok=True)
os.makedirs(audio_folder, exist_ok=True)

def load_processed_video():
    if os.path.exists(processed_file):
        with open(processed_file, "r") as f:
            return json.load(f).get("videos", [])
    return []

def save_processed_videos(processed_list):
    with open(processed_file, "w") as f:
        json.dump({"videos": processed_list}, f, indent=4)

def extract_audio_from_new_videos():
    print("\nExtracting audio from new videos...\n")

    processed = load_processed_video()

    all_videos = [
        f for f in os.listdir(video_folder)
        if f.lower().endswith((".mp4", ".mkv", ".mov", ".avi"))
    ]

    print("Found videos:", all_videos)

    new_videos = [v for v in all_videos if v not in processed]

    if not new_videos:
        print("No new videos found.")
        return []

    print("New videos:", new_videos)

    for video in new_videos:
        input_path = os.path.join(video_folder, video)
        audio_name = video.rsplit(".", 1)[0] + ".wav"
        output_path = os.path.join(audio_folder, audio_name)

        print(f"\nExtracting audio from {video}...")

        (
            ffmpeg
            .input(input_path)
            .output(output_path, ac=1, ar=16000)
            .overwrite_output()
            .run()
        )

        print(f"Saved audio: {output_path}")

        processed.append(video)

    save_processed_videos(processed)

    print("\nAll new videos converted to audio successfully.\n")

    return [v.rsplit(".", 1)[0] + ".wav" for v in new_videos]


if __name__ == "__main__":
    extract_audio_from_new_videos()
