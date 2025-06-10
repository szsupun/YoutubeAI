import time
import os
import re
import json
import ast
import random
from google import genai
from google.genai import types
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import uuid
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
import google.oauth2.credentials
import google.auth.transport.requests

# Define YouTube OAuth 2.0 scopes
SCOPES = ['https://www.googleapis.com/auth/youtube']

# File to store used prompts/food items
USED_PROMPTS_FILE = "used_prompts.json"
VIDEOS_OUTPUT_FOLDER = "generated_videos"  # Folder to save all generated videos


def create_output_folder():
    """Create the output folder for generated videos if it doesn't exist."""
    if not os.path.exists(VIDEOS_OUTPUT_FOLDER):
        os.makedirs(VIDEOS_OUTPUT_FOLDER)
        print(f"Created output folder: {VIDEOS_OUTPUT_FOLDER}")
    return VIDEOS_OUTPUT_FOLDER


def load_used_prompts():
    """Load previously used prompts/food items from a file."""
    if os.path.exists(USED_PROMPTS_FILE):
        with open(USED_PROMPTS_FILE, 'r') as f:
            return json.load(f)
    return []


def save_used_prompt(food_item):
    """Save a new food item to the used prompts file."""
    used_prompts = load_used_prompts()
    if food_item not in used_prompts:
        used_prompts.append(food_item)
        with open(USED_PROMPTS_FILE, 'w') as f:
            json.dump(used_prompts, f, indent=2)


def authenticate_youtube():
    # Set up OAuth 2.0 flow
    flow = InstalledAppFlow.from_client_secrets_file(
        'client_secrets.json', SCOPES)
    credentials = flow.run_local_server(port=0)
    # Build the YouTube API client
    return build('youtube', 'v3', credentials=credentials)


def clean_keywords_for_youtube(keywords):
    """
    Clean and validate keywords for YouTube API with strict rules
    - Remove duplicates
    - Limit to 30 characters per tag (conservative limit)
    - Limit total tags to 15 (conservative limit)
    - Remove all special characters except spaces and hyphens
    - Only allow alphanumeric characters, spaces, and hyphens
    """
    if not keywords:
        return []

    import re

    cleaned_keywords = []
    for keyword in keywords:
        # Convert to string and strip whitespace
        clean_keyword = str(keyword).strip()

        # Skip empty keywords
        if not clean_keyword:
            continue

        # Remove all special characters except letters, numbers, spaces, and hyphens
        clean_keyword = re.sub(r'[^a-zA-Z0-9\s\-]', '', clean_keyword)

        # Replace multiple spaces with single space
        clean_keyword = re.sub(r'\s+', ' ', clean_keyword)

        # Strip again after cleaning
        clean_keyword = clean_keyword.strip()

        # Skip if empty after cleaning
        if not clean_keyword:
            continue

        # Limit keyword length to 30 characters (conservative)
        if len(clean_keyword) > 30:
            clean_keyword = clean_keyword[:30].strip()

        # Skip very short keywords (less than 3 characters)
        if len(clean_keyword) < 3:
            continue

        # Add if not already in list (remove duplicates, case insensitive)
        if clean_keyword.lower() not in [k.lower() for k in cleaned_keywords]:
            cleaned_keywords.append(clean_keyword)

        # Limit to 15 tags to be conservative
        if len(cleaned_keywords) >= 15:
            break

    return cleaned_keywords


def upload_video(youtube, video_file, title, description, category_id, keywords, privacy_status):
    """Upload a video to YouTube with metadata."""
    # Clean the keywords first
    clean_tags = clean_keywords_for_youtube(keywords)

    print(f"Original keywords count: {len(keywords) if keywords else 0}")
    print(f"Cleaned keywords count: {len(clean_tags)}")
    print(f"Cleaned tags: {clean_tags}")

    body = {
        'snippet': {
            'title': title,
            'description': description,
            'categoryId': category_id
        },
        'status': {
            'privacyStatus': privacy_status
        }
    }

    # Only add tags if we have valid ones
    if clean_tags:
        body['snippet']['tags'] = clean_tags

    media = MediaFileUpload(video_file, chunksize=-1, resumable=True)
    request = youtube.videos().insert(
        part='snippet,status',
        body=body,
        media_body=media
    )

    try:
        response = request.execute()
        video_id = response['id']
        print(f"Video uploaded successfully! Video ID: {video_id}")
        print(f"Video URL: https://www.youtube.com/watch?v={video_id}")
        return response
    except Exception as e:
        print(f"Upload failed: {e}")
        return None


def sanitize_filename(food_item):
    """Sanitize the food item name for use as a file name."""
    sanitized = re.sub(r'[^\w\s-]', '', food_item)
    sanitized = re.sub(r'\s+', '_', sanitized)
    return sanitized[:50]


def parse_metadata(metadata_text):
    """Parse metadata with improved JSON handling and validation."""
    print(f"Raw metadata: {metadata_text}")
    metadata_text = metadata_text.strip()

    # Extract JSON from code block
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', metadata_text, re.DOTALL)
    if not json_match:
        raise ValueError("No JSON code block found. Metadata must be wrapped in ```json ... ```")

    json_str = json_match.group(1).strip()

    print(f"Cleaned JSON string for parsing: {json_str}")

    try:
        # Try parsing the JSON directly first (should work if AI generates proper JSON)
        metadata = json.loads(json_str)
        title = metadata.get("title", "").strip()
        description = metadata.get("description", "").strip()
        keywords = metadata.get("keywords", [])

        # Ensure keywords is a list
        if isinstance(keywords, str):
            try:
                keywords = ast.literal_eval(keywords)
            except:
                keywords = [k.strip() for k in keywords.split(',')]

        # Ensure all keywords are strings and clean them
        keywords = [str(k).strip().strip('"\'') for k in keywords if k]

    except json.JSONDecodeError as e:
        print(f"Initial JSON parsing failed: {e}")

        # Fallback parsing for malformed JSON
        try:
            # More careful approach to fix the JSON
            # First, handle newlines and clean whitespace
            clean_json = re.sub(r'\s*\n\s*', ' ', json_str)
            clean_json = re.sub(r'\s+', ' ', clean_json)

            # Fix unescaped quotes within strings (like apostrophes)
            # This regex finds quoted strings and escapes internal quotes
            def escape_internal_quotes(match):
                content = match.group(1)
                # Escape any unescaped quotes within the content
                content = content.replace('\\"', '###ESCAPED_QUOTE###')  # Temporarily mark already escaped
                content = content.replace('"', '\\"')  # Escape unescaped quotes
                content = content.replace('###ESCAPED_QUOTE###', '\\"')  # Restore previously escaped
                return f'"{content}"'

            # Apply the fix to string values
            clean_json = re.sub(r'"([^"]*(?:\\"[^"]*)*)"', escape_internal_quotes, clean_json)

            # Try parsing again
            metadata = json.loads(clean_json)
            title = metadata.get("title", "").strip()
            description = metadata.get("description", "").strip()
            keywords = metadata.get("keywords", [])
            keywords = [str(k).strip().strip('"\'') for k in keywords if k]

        except json.JSONDecodeError as e2:
            print(f"Fallback JSON parsing also failed: {e2}")

            # Last resort: manual extraction using regex
            try:
                # Extract title
                title_match = re.search(r'"title":\s*"([^"]*(?:\\"[^"]*)*)"', json_str)
                title = title_match.group(1).replace('\\"', '"') if title_match else ""

                # Extract description
                desc_match = re.search(r'"description":\s*"([^"]*(?:\\"[^"]*)*)"', json_str)
                description = desc_match.group(1).replace('\\"', '"').replace('\\n', '\n') if desc_match else ""

                # Extract keywords array
                keywords_match = re.search(r'"keywords":\s*\[(.*?)\]', json_str, re.DOTALL)
                if keywords_match:
                    keywords_str = keywords_match.group(1)
                    # Extract individual keywords
                    keyword_matches = re.findall(r'"([^"]*)"', keywords_str)
                    keywords = [k.strip() for k in keyword_matches if k.strip()]
                else:
                    keywords = []

                print(f"Manual extraction successful: {len(keywords)} keywords found")

            except Exception as e3:
                raise ValueError(
                    f"All metadata parsing methods failed. Original error: {e}. "
                    f"Fallback error: {e2}. Manual extraction error: {e3}. "
                    f"Raw metadata:\n{metadata_text}")

    # Truncate description to 4500 characters (YouTube limit is 5000, leaving buffer)
    if len(description) > 4500:
        description = description[:4497] + "..."
        print(f"Description truncated to 4500 characters")

    # Validate and fix metadata
    if len(title) > 100:
        title = title[:97] + "..."
        print(f"Title truncated to 100 characters: {title}")

    if not (30 <= len(keywords) <= 50):
        print(f"Warning: Keywords count is {len(keywords)}, expected 30-50")

    # Limit keywords to 40 for YouTube (YouTube allows up to 500 chars total for tags)
    if len(keywords) > 40:
        keywords = keywords[:40]
        print(f"Keywords limited to 40 items")

    return title, description, keywords


def get_random_music_track():
    """Return a random .mp3 file from the music_tracks folder."""
    music_dir = os.path.join(os.path.dirname(__file__), "music_tracks")
    if os.path.exists(music_dir):
        music_files = [f for f in os.listdir(music_dir) if f.endswith('.mp3')]
        return os.path.join(music_dir, random.choice(music_files)) if music_files else None
    print(f"Warning: music_tracks directory not found at {music_dir}")
    return None


def add_music_to_video(video_file, music_file, output_file, volume=0.3):
    """Add background music to the video at a specified volume while maintaining 9:16 aspect ratio."""
    try:
        # Load video and music
        video = VideoFileClip(video_file)
        music = AudioFileClip(music_file)

        # Trim music to match video duration (8 seconds)
        music = music.subclip(0, min(music.duration, video.duration)).volumex(volume)

        # Get original video audio (if any) and mix with music
        if video.audio is not None:
            # Mix original audio with background music
            final_audio = CompositeAudioClip([video.audio.volumex(0.7), music])
        else:
            # Use only background music
            final_audio = music

        # Set the final audio to video
        final_video = video.set_audio(final_audio)

        # Write the final video with same aspect ratio (9:16 is preserved automatically)
        final_video.write_videofile(
            output_file,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile='temp-audio.m4a',
            remove_temp=True,
            verbose=False,
            logger=None  # Reduce verbose output
        )

        # Clean up
        video.close()
        music.close()
        final_video.close()

        print(f"✓ Music added successfully. Video aspect ratio maintained: 9:16")
        return output_file

    except Exception as e:
        print(f"Error adding music to video: {e}")
        return video_file  # Return original video file if music addition fails


def main():
    """Main function to orchestrate the video generation and upload process."""
    # Create output folder for generated videos
    output_folder = create_output_folder()

    client = genai.Client(api_key=os.getenv("GENAI_API_KEY", "123"))

    used_prompts = load_used_prompts()

    video_prompt_text = """
    Suggest a unique food or drink item that has not been used before, and generate a vibrant, high-engagement 8-second short-form video idea for making that item, designed for Instagram Reels, TikTok, or YouTube Shorts. The video should follow this format:

    The video features a recurring mascot character (e.g., a quirky yellow cat chef named "Zesty"), who helps prepare the item in a fun, fast-paced, and visually playful way.

    Include 3 to 4 fast cuts or sequences, each no more than 2 seconds, that show key stages of the preparation: pouring, layering, mixing, topping, or serving.

    Use specific camera angles (e.g., top-down, macro, slow-motion, side-shot) and sound design elements (e.g., ASMR splashes, crunches, upbeat music, or cartoon SFX like a "meow" or "boing").

    Suggest lighting style (natural, warm, vibrant) and color/sensory appeal (e.g., creamy, bubbly, sizzling, melty).

    End with a hero shot of the finished dish or drink being presented by the character with a cheeky action (like a wink, tail flick, or dance), plus overlay text and a catchy sound.

    Make sure the video is full of energy, charm, and irresistible food visuals, all within an 8-second runtime. Output the food item first, followed by the video prompt in this structure:

    Food Item: <unique food or drink item>
    [0.0s–2s] → [Scene Description + Angle/Sound/Action]
    [2s–4s] → [Scene Description + Angle/Sound/Action]
    [4s–6s] → [Scene Description + Angle/Sound/Action]
    [6s–8s] → [Final Scene + Overlay Text + Mascot Gag + Sound Effect]

    Ensure the suggested food item is not in this list of previously used items: {used_prompts}
    """

    try:
        video_response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[video_prompt_text.format(used_prompts=used_prompts)],
            config=types.GenerateContentConfig(max_output_tokens=500, temperature=0.7)
        )
        video_text = video_response.text.strip()
        print("Generated response:", video_text)

        food_item_match = re.search(r'Food Item:\s*(.+?)(?=\[0\.0s|$)', video_text, re.IGNORECASE | re.DOTALL)
        if not food_item_match:
            raise ValueError("Failed to extract food item from AI response.")
        food_item = food_item_match.group(1).strip()
        if food_item in used_prompts:
            raise ValueError(f"Generated food item '{food_item}' is already used. Please try again with a new item.")
        video_prompt = video_text[food_item_match.end():].strip()
        print(f"Selected food item: {food_item}")
        print("Generated video prompt:", video_prompt)

    except Exception as e:
        print(f"Process failed during food item and video prompt generation: {e}")
        return

    save_used_prompt(food_item)

    music_file = get_random_music_track()
    if music_file:
        print(f"Selected music track: {os.path.basename(music_file)}")
    else:
        print("No music track selected, using default behavior.")
        music_file = "sugar_rush.mp3"

    metadata_prompt = f"""
    Based on the following video prompt, generate comprehensive SEO-optimized YouTube video metadata for an 8-second video about making {food_item} with a quirky mascot character named Zesty. 

    CRITICAL REQUIREMENTS:
    - Include AT LEAST 15 hashtags in the description
    - Generate EXACTLY 40 keywords for maximum SEO coverage
    - Description must be engaging and include call-to-action
    - Title must be under 100 characters and keyword-rich
    - NO APOSTROPHES in title or description (use alternative phrasing)
    - Use proper JSON escape sequences for any special characters

    Provide the metadata EXCLUSIVELY as a valid JSON object within ```json ... ```. Do NOT include any text outside the ```json ... ``` block. Use this exact structure with DOUBLE QUOTES only and NO APOSTROPHES:

    ```json
    {{
        "title": "engaging title here without apostrophes, max 100 characters, keyword-rich",
        "description": "engaging description with AT LEAST 15 hashtags, call-to-action, max 4500 characters, NO APOSTROPHES",
        "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5", "keyword6", "keyword7", "keyword8", "keyword9", "keyword10", "keyword11", "keyword12", "keyword13", "keyword14", "keyword15", "keyword16", "keyword17", "keyword18", "keyword19", "keyword20", "keyword21", "keyword22", "keyword23", "keyword24", "keyword25", "keyword26", "keyword27", "keyword28", "keyword29", "keyword30", "keyword31", "keyword32", "keyword33", "keyword34", "keyword35", "keyword36", "keyword37", "keyword38", "keyword39", "keyword40"]
    }}
    ```

    Make sure:
    - ALL quotes are DOUBLE quotes (") and NO APOSTROPHES anywhere
    - Instead of "Zesty's" use "Zesty the Cat" or "Zesty Cat Chef"
    - Instead of "It's" use "It is" or "This is"
    - Instead of "Don't" use "Do not"
    - Description includes 15+ hashtags like #FoodHacks #Cooking #Recipe #DIY #Shorts #Viral #Trending #Food #Yummy #Delicious #HomeCooking #FoodPrep #QuickRecipes #EasyRecipes #FoodVideo
    - Keywords cover: food name, cooking terms, social media terms, trending food hashtags, cooking techniques, ingredients, food categories, and viral food trends
    - JSON is perfectly formatted and valid with no apostrophes
    - Description is engaging and includes clear call-to-action like "Try this recipe!" or "Follow for more!"

    Video prompt: {video_prompt}
    """.strip()

    try:
        metadata_response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[metadata_prompt],
            config=types.GenerateContentConfig(max_output_tokens=800, temperature=0.7)
        )
        metadata_text = metadata_response.text.strip()
        title, description, keywords = parse_metadata(metadata_text)
        print("Generated metadata:", {'title': title, 'description': description, 'keywords_count': len(keywords)})

    except Exception as e:
        print(f"Process failed during metadata generation: {e}")
        return

    # Generate unique filenames and save in output folder
    sanitized_food_item = sanitize_filename(food_item)
    video_filename = f"{sanitized_food_item}_{uuid.uuid4().hex[:8]}.mp4"
    video_file = os.path.join(output_folder, video_filename)

    try:
        print("Starting video generation...")
        operation = client.models.generate_videos(
            model="veo-2.0-generate-001",
            prompt=video_prompt,
            config=types.GenerateVideosConfig(
                person_generation="allow_all",
                aspect_ratio="9:16",  # Maintain 9:16 aspect ratio
                number_of_videos=1,
                duration_seconds=8,
                enhance_prompt=True
            )
        )

        while not operation.done:
            print("Waiting for video generation... (checking every 20 seconds)")
            time.sleep(20)
            operation = client.operations.get(operation)

        for n, generated_video in enumerate(operation.response.generated_videos):
            print(f"Saving video as {video_file}")
            client.files.download(file=generated_video.video)
            generated_video.video.save(video_file)
            print(f"✓ Video generation complete. Saved to: {video_file}")

    except Exception as e:
        print(f"Process failed during video generation or saving: {e}")
        return

    try:
        # Create filename for video with music in the same output folder
        music_video_filename = f"{sanitized_food_item}_with_music_{uuid.uuid4().hex[:8]}.mp4"
        video_with_music = os.path.join(output_folder, music_video_filename)

        # Add music while maintaining 9:16 aspect ratio
        final_video = add_music_to_video(video_file, music_file, video_with_music)
        print(f"✓ Final video with music saved to: {final_video}")

    except Exception as e:
        print(f"Process failed during music addition: {e}")
        final_video = video_file  # Use original video if music addition fails

    try:
        youtube = authenticate_youtube()

    except Exception as e:
        print(f"Process failed during YouTube authentication: {e}")
        return

    try:
        upload_response = upload_video(
            youtube,
            final_video,
            title=title,
            description=description,
            category_id='26',  # Howto & Style - best for cooking videos
            keywords=keywords,
            privacy_status='public'
        )

        if upload_response:
            print(f"✓ Upload complete! All files saved in: {output_folder}")
            print(f"✓ Video uploaded successfully with cleaned keywords")
        else:
            print(f"Upload failed, but video files are still saved in: {output_folder}")

    except Exception as e:
        print(f"Process failed during YouTube upload: {e}")
        print(f"Video files are still saved in: {output_folder}")
        return


if __name__ == '__main__':
    main()
