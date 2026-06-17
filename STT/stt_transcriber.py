from groq import Groq
from config import GROQ_API_KEY
import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

audio_folder = os.path.join(BASE_DIR, "audio")
transcript_folder = os.path.join(BASE_DIR, "transcripts")
processed_file = os.path.join(BASE_DIR, "processed_audio.json")

os.makedirs(transcript_folder, exist_ok=True)

def load_processed_audios():
    if os.path.exists(processed_file):
        try:
            with open(processed_file, "r") as f:
                return json.load(f).get("audios", [])
        except:
            return []
    return []

def save_processed_audios(processed_list):
    with open(processed_file, "w") as f:
        json.dump({"audios": processed_list}, f, indent=4)

def transcribe_new_audios():
    client = Groq(api_key=GROQ_API_KEY)

    processed = load_processed_audios()

    all_audios = [f for f in os.listdir(audio_folder) if f.lower().endswith(".wav")]
    new_audios = [a for a in all_audios if a not in processed]

    if not new_audios:
        print("\n✔ No new audios to transcribe.")
        return

    print("\n🆕 New audios:", new_audios)

    for audio in new_audios:
        input_path = os.path.join(audio_folder, audio)
        base_name = os.path.splitext(audio)[0]

        print(f"\n🎤 Transcribing: {audio}")

        with open(input_path, "rb") as f:
            response = client.audio.transcriptions.create(
                file=f,
                model="whisper-large-v3",
                response_format="verbose_json",
                timestamp_granularities=["word"]
            )

        json_output_path = os.path.join(transcript_folder, base_name + ".json")
        with open(json_output_path, "w", encoding="utf-8") as jf:
            json.dump(response.model_dump(), jf, indent=4, ensure_ascii=False)

        text_output_path = os.path.join(transcript_folder, base_name + ".txt")
        with open(text_output_path, "w", encoding="utf-8") as tf:
            tf.write(response.text)

        processed.append(audio)

    save_processed_audios(processed)

    print("\n🎉 All new audios transcribed successfully!\n")


if __name__ == "__main__":
    transcribe_new_audios()
