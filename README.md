# Photo Cutout Video Generator


https://github.com/user-attachments/assets/fed6fe6f-0fb3-4eb1-8031-da1a7e153102




https://github.com/user-attachments/assets/4ada8f81-0d5f-4036-bce6-a00427519aec



A highly customizable, programmatic video generator that creates stunning vertical photo montages. It takes a collection of photos and a background image, and creates a "cutout" effect (like a giant number or letter etched into a wall) where your photos populate behind the cutout in a dense grid. It also applies a cinematic fluorescent "tubelight" flicker effect to the photos as they pop in!

Perfect for creating aesthetic anniversary videos, birthday reels, or customized status updates for Instagram, WhatsApp, and TikTok.

## Features
- **Dynamic Cutout Masks**: Specify any text, number (e.g., "3"), or provide an SVG file to be cut out of the background.
- **Customizable Borders**: Add a colored outline around your text or SVG cutouts to make them pop.
- **Tubelight Flicker Animation**: Photos pop into the grid with a cool, randomized fluorescent blinking effect.
- **EXIF Auto-Correction**: Automatically rotates portrait/landscape photos correctly based on EXIF data.
- **Fully Configurable**: Tweak grid sizes, gaps, text formatting, blur radius, frame rates, and more using a simple JSON file or CLI arguments.
- **Custom Fonts**: Drop in any `.ttf` file to customize the cutout shape or the overlaid text.

## Installation

1. Ensure you have [Python 3.7+](https://www.python.org/) installed.
2. If using `uv`, the dependencies are managed for you. Otherwise, install the required Python dependencies:
   ```bash
   pip install pillow moviepy numpy svglib reportlab librosa
   ```

## Usage

The easiest way to use the generator is by passing a JSON configuration file:

```bash
python main.py --config config.json
```

You can also override any specific setting directly via the command line:
```bash
python main.py --config config.json --cutout-text "5" --text "Happy\nBirthday"
```

## Configuration Options

Below is the list of all available options you can define in your `config.json` file (or pass as CLI arguments):

| Option | Type | Description |
| :--- | :--- | :--- |
| `image_dir` | string | Directory containing the pictures to be used in the background grid. |
| `bg_image` | string | The image file to use for the blurred foreground "wall". Must be located in `image_dir`. |
| `output` | string | The name and path of the generated MP4 file (e.g., `video.mp4`). |
| `width` | integer | The width of the generated video (default: `1080`). |
| `height` | integer | The height of the generated video (default: `1920`). |
| `fps` | integer | Frames per second for the video (default: `30`). |
| `appear_interval` | float | Time in seconds between each photo appearing in the grid (default: `0.2`). |
| `hold_duration` | float | Time in seconds to hold the video after the final photo appears (default: `3.0`). |
| `square_size` | integer | Width/height in pixels of each photo tile in the background grid. |
| `gap` | integer | Space in pixels between each photo tile in the grid. |
| `target_duration` | float | Target duration of the video in seconds (default: `10.0`). The script will intelligently lay out photos to meet this duration. |
| `audio` | string | Optional path to an audio track to attach. If provided, the photo tiles will be synced to pop on the musical beats automatically! |
| `font_cutout` | string | Path to the `.ttf` font file used for the massive cutout mask. |
| `font_text` | string | Path to the `.ttf` font file used for the bottom text. |
| `font_text_size` | integer | Font size for the bottom text. |
| `cutout_text` | string | The character(s) or text to cut out from the center of the wall. |
| `text` | string | The text to draw at the bottom of the video. Use `\n` to insert line breaks. |
| `text_color` | string | Hex code for the bottom text color (e.g., `#FFB7CE`). |
| `blur_radius` | integer | Gaussian blur radius applied to the background wall (default: `10`). |
| `cutout_border_color`| string | Hex code for the cutout border outline color (e.g., `#FFB7CE`). |
| `cutout_border_width`| integer | Width of the cutout border in pixels. Set to 0 to disable. |
| `svg_file` | string | Optional path to an `.svg` file to use as the cutout shape. Overrides `number`. |

## Example `config.json`

```json
{
    "image_dir": "pictures",
    "bg_image": "DSC_0073.JPG",
    "output": "custom_video.mp4",
    "width": 1080,
    "height": 1920,
    "fps": 30,
    "appear_interval": 0.2,
    "hold_duration": 3.0,
    "square_size": 215,
    "gap": 5,
    "target_duration": 10.0,
    "audio": "song.mp3",
    "font_cutout": "AlfaSlabOne-Regular.ttf",
    "font_text": "fonts\\Lavishly_Yours\\LavishlyYours-Regular.ttf",
    "font_text_size": 108,
    "cutout_text": "3",
    "text": "Hello\nWorld",
    "text_color": "#FFB7CE",
    "blur_radius": 10
}
```
