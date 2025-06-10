# YouTube Video Automation Script 📹

![AI YouTube Automation](https://envs.sh/OmS.jpg)

## Overview 📋

This Python script automates the creation and upload of short-form YouTube Shorts using AI-generated content. The AI dynamically generates unique video ideas based on your YouTube channel's data (e.g., existing video themes, audience preferences, or trending topics), featuring a customizable mascot (e.g., Zesty the Cat Chef 🐾). The script adds background music, maintains a 9:16 aspect ratio for mobile optimization, and uploads videos to YouTube with SEO-optimized metadata. Users can easily adapt the video and metadata prompts to align with their channel’s niche or style.

## Features ✨

- **AI-Driven Video Ideas**: Generates video concepts tailored to your YouTube channel’s data, ensuring relevance and engagement.
- **Customizable Prompts**: Modify video and metadata prompts to match your channel’s theme (e.g., food, lifestyle, tutorials).
- **Video Generation**: Creates 8-second YouTube Shorts with 3–4 fast-paced scenes using AI (e.g., Veo model).
- **Music Integration**: Adds background music from a local directory, preserving the 9:16 aspect ratio.
- **SEO-Optimized Metadata**: Produces titles (<100 characters), descriptions (<4500 characters, 15+ hashtags), and exactly 40 keywords, avoiding apostrophes.
- **YouTube Upload**: Authenticates via OAuth 2.0 and uploads videos as public YouTube Shorts.
- **File Management**: Saves videos in a `generated_videos` folder and tracks used prompts in `used_prompts.json`.

## Prerequisites 🛠️

To use and customize the script, ensure you have:

- **Python 3.8+** installed.
- **Required Libraries**:
  ```bash
  pip install google-auth-oauthlib google-api-python-client moviepy
  ```
- **Google API Credentials**:
  - Download `client_secrets.json` from the [Google Cloud Console](https://console.cloud.google.com/) for YouTube API access.
  - Set the `GENAI_API_KEY` environment variable for the AI model (e.g., Gemini, Veo).
- **Music Tracks**:
  - Place `.mp3` files in a `music_tracks` directory in the project root.
- **Output Folder**:
  - Videos are saved in a `generated_videos` folder, created automatically.

## Setup ⚙️

1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd <repository-folder>
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Google API**:
   - Place `client_secrets.json` in the project root.
   - Enable the YouTube Data API v3 in the Google Cloud Console.

4. **Set Environment Variables**:
   ```bash
   export GENAI_API_KEY="your-api-key-here"
   ```

5. **Prepare Music Tracks**:
   - Add `.mp3` files to the `music_tracks` directory for random background music selection.

## Customizing Prompts with Channel Data 🎨

The script uses two main prompts that leverage your YouTube channel’s data to generate tailored video ideas and metadata. The AI analyzes your channel’s content (e.g., video titles, descriptions, or viewer engagement) to suggest relevant concepts.

### 1. Video Prompt ✍️

The `video_prompt_text` variable (in the `main` function) instructs the AI to generate a video idea based on your channel’s data. The default prompt creates an 8-second food video with Zesty the Cat Chef. To customize:

- **Incorporate Channel Data**: Instruct the AI to analyze your channel’s niche, themes, or trending topics (e.g., “base the idea on my channel’s focus on vegan recipes”).
- **Change the Niche**: Replace “food or drink item” with your channel’s focus (e.g., “vegan dessert,” “budget travel tip”).
- **Modify the Mascot**: Update “Zesty the Cat Chef” to a character fitting your brand (e.g., “Vegan Vicky” or “Travel Buddy”).
- **Adjust Scene Details**: Specify camera angles (e.g., top-down, slow-motion), sound effects (e.g., ASMR, upbeat music), or lighting (e.g., natural, vibrant).
- **Track Used Prompts**: The script stores used prompts in `used_prompts.json` to avoid duplicates.

**Example Modified Video Prompt (for a Vegan Recipe Channel)**:
```python
video_prompt_text = """
Analyze my YouTube channel's data to suggest a unique vegan recipe that aligns with my audience's preferences and trending vegan topics. Generate a vibrant, high-engagement 8-second YouTube Short video idea for preparing that recipe. The video should follow this format:

The video features a recurring mascot character (e.g., a friendly avocado named 'Vegan Vicky'), who helps prepare the recipe in a fun, fast-paced, and visually playful way.

Include 3 to 4 fast cuts or sequences, each no more than 2 seconds, that show key stages of the preparation: chopping, mixing, plating, or garnishing.

Use specific camera angles (e.g., top-down, macro, slow-motion, side-shot) and sound design elements (e.g., ASMR chopping sounds, upbeat music, or cartoon SFX like a 'pop' or 'sizzle').

Suggest lighting style (natural, warm, vibrant) and color/sensory appeal (e.g., creamy, colorful, fresh).

End with a hero shot of the finished dish presented by the character with a cheeky action (like a wink or spin), plus overlay text and a catchy sound.

Make sure the video is full of energy, charm, and irresistible visuals, all within an 8-second runtime. Output the recipe first, followed by the video prompt in this structure:

Recipe: <unique vegan recipe>
[0.0s–2s] → [Scene Description + Angle/Sound/Action]
[2s–4s] → [Scene Description + Angle/Sound/Action]
[4s–6s] → [Scene Description + Angle/Sound/Action]
[6s–8s] → [Final Scene + Overlay Text + Mascot Gag + Sound Effect]

Ensure the suggested recipe is not in this list of previously used items: {used_prompts}
"""
```

- Replace the original `video_prompt_text` in the `main` function.
- Update references to `food_item` to match your niche (e.g., `recipe`).
- Ensure the AI model (e.g., Gemini) has access to your channel data via the API or prompt context.

### 2. Metadata Prompt 📝

The `metadata_prompt` variable generates SEO-optimized YouTube metadata tailored to your channel’s niche. To customize:

- **Align with Channel Data**: Instruct the AI to create metadata based on your channel’s keywords or audience interests.
- **Update the Niche**: Replace `{food_item}` with your item (e.g., `{recipe}`).
- **Change the Mascot**: Use your character name (e.g., “Vegan Vicky”).
- **Adjust Keywords**: Include hashtags and keywords relevant to your niche (e.g., `#VeganRecipes`, `#PlantBased`).
- **Maintain Structure**: Use double quotes, no apostrophes, and exactly 40 keywords.

**Example Modified Metadata Prompt (for a Vegan Recipe Channel)**:
```python
metadata_prompt = f"""
Based on my YouTube channel's data and the following video prompt, generate comprehensive SEO-optimized YouTube video metadata for an 8-second video about preparing {recipe} with a mascot named Vegan Vicky. 

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
    "keywords": ["keyword1", "keyword2", "keyword3", ..., "keyword40"]
}}
```

Make sure:
- ALL quotes are DOUBLE quotes (") and NO APOSTROPHES anywhere
- Instead of "Vicky's" use "Vegan Vicky" or "Vicky the Avocado"
- Instead of "It's" use "It is" or "This is"
- Instead of "Don't" use "Do not"
- Description includes 15+ hashtags like #VeganRecipes #PlantBased #HealthyEating #VeganFood #Shorts #Viral #Trending #EasyRecipes #VeganCooking #RecipeIdeas #FoodVideo #QuickRecipes #VeganLife #HealthyRecipes #FoodPrep
- Keywords cover: recipe name, cooking terms, social media terms, trending vegan hashtags, techniques, ingredients, and viral food trends
- JSON is perfectly formatted and valid with no apostrophes
- Description is engaging and includes clear call-to-action like "Try this recipe!" or "Subscribe for more!"

Video prompt: {video_prompt}
"""
```

- Replace the original `metadata_prompt` in the `main` function.
- Ensure `{video_prompt}` references your customized video prompt.

## Usage 🚀

Run the script after customizing the prompts:

```bash
python youtube_automation.py
```

### Workflow 🔄

1. **Idea Generation**: The AI analyzes your YouTube channel’s data to suggest a unique video idea, tracked in `used_prompts.json`.
2. **Video Creation**: Generates an 8-second YouTube Short with your specified scenes and mascot.
3. **Music Addition**: Overlays a random `.mp3` from `music_tracks` at 30% volume.
4. **Metadata Creation**: Produces SEO-optimized metadata based on your channel’s niche.
5. **YouTube Upload**: Uploads the video as a public YouTube Short (category: Howto & Style).
6. **File Storage**: Saves videos in `generated_videos` with filenames like `<item>_<uuid>.mp4`.

## Tips for Customization 💡

- **Channel Data Access**: Provide the AI with channel context (e.g., via YouTube API or prompt descriptions) for accurate video ideas.
- **Keyword Strategy**: Use channel-specific hashtags and keywords to boost discoverability.
- **Music Variety**: Add diverse `.mp3` files to `music_tracks` for unique videos.
- **Testing**: Start with a small prompt tweak to verify AI output aligns with your channel’s style.

## Error Handling 🛡️

The script handles:
- **JSON Parsing**: Fallback methods for malformed metadata.
- **API Errors**: Manages YouTube API or AI model failures.
- **File Issues**: Checks for missing music tracks or directories.
- **YouTube Compliance**: Limits tags to 15, <30 characters each.

## Notes 📝

- **Aspect Ratio**: Videos are in 9:16 for YouTube Shorts.
- **Apostrophe Avoidance**: Uses “It is” or “Vegan Vicky” for YouTube compliance.
- **Prompt Tracking**: Stores used prompts to ensure uniqueness.
- **Channel Data**: AI performance improves with detailed channel context.

## Contributing 🤝

To contribute:
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/YourFeature`).
3. Commit changes (`git commit -m "Add YourFeature"`).
4. Push to the branch (`git push origin feature/YourFeature`).
5. Open a pull request.

## License 📜

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Contact 📧

For support, contact [@szteamdev](https://t.me/szteamdev).

---

🌟 **Let the AI craft YouTube Shorts tailored to your channel!** 🌟
