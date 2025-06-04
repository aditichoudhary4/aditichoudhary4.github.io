import json
import traceback
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound

# === Paths ===
CONFIG_FILE = "config.json"
INPUT_FILE = "input.json"
OUTPUT_FILE = "output.json"
LOG_FILE = "output.log"

def log(message):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(message + "\n")
    print(message)

def load_config():
    with open(CONFIG_FILE) as f:
        return json.load(f)

def load_input():
    with open(INPUT_FILE) as f:
        return json.load(f)

def save_output(data):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_video_id(url):
    parsed_url = urlparse(url)
    if 'youtu.be' in parsed_url.netloc:
        return parsed_url.path.strip("/")
    elif 'youtube.com' in parsed_url.netloc:
        return parse_qs(parsed_url.query)['v'][0]
    else:
        raise ValueError("Invalid YouTube URL format.")

def fetch_transcript(video_url, lang='en'):
    video_id = get_video_id(video_url)
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        try:
            transcript = transcript_list.find_transcript([lang])
        except:
            try:
                transcript = transcript_list.find_generated_transcript([lang])
            except:
                # Fallback: get first available transcript
                transcript = next(iter(transcript_list))

        log(f"✅ Found transcript in {transcript.language} ({'auto-generated' if transcript.is_generated else 'manual'})")

        try:
            transcript_data = transcript.fetch()
            if not transcript_data:
                log("⚠️ Transcript fetch returned empty.")
                return None

            text = " ".join([t['text'] for t in transcript_data])

            return {
                "video_id": video_id,
                "language": transcript.language,
                "is_generated": transcript.is_generated,
                "text": text
            }
        except Exception as fetch_error:
            log(f"❌ Failed to fetch actual transcript content: {fetch_error}")
            log(traceback.format_exc())
            return None

    except NoTranscriptFound:
        log(f"❌ No transcript available in language '{lang}'.")
        return None
    except Exception as e:
        log(f"❌ Error while fetching transcript: {e}")
        log(traceback.format_exc())
        return None

def main():
    config = load_config()
    input_data = load_input()
    lang = config.get("lang", "en")
    url = input_data.get("url")

    if not url:
        log("❌ No URL provided in input.json")
        return

    result = fetch_transcript(url, lang)
    if result:
        save_output(result)
        log("✅ Transcript saved to output.json")
    else:
        log("⚠️ Transcript could not be retrieved.")

if __name__ == "__main__":
    main()
