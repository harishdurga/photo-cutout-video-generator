# Photo Cutout Video Generator



https://github.com/user-attachments/assets/5bb9392b-52a0-46fa-9927-13c444be624e


https://github.com/user-attachments/assets/fed6fe6f-0fb3-4eb1-8031-da1a7e153102

https://github.com/user-attachments/assets/4ada8f81-0d5f-4036-bce6-a00427519aec

A highly customizable, programmatic video generator that creates stunning vertical photo montages. It takes a collection of photos and creates a "cutout" effect (like a giant number, letter, or SVG shape) where your photos populate behind the cutout in a dense grid. It also applies a cinematic fluorescent "tubelight" flicker effect to the photos as they pop in!

Perfect for creating aesthetic anniversary videos, birthday reels, or customized status updates for Instagram, WhatsApp, and TikTok.

## Features
- **Dynamic Cutout Masks**: Specify any text, number (e.g., "3"), provide an SVG file, or use a PNG image (with transparency or white background) to be cut out of the background.
- **Advanced Backgrounds**: Choose between a solid color, a linear gradient, or a background image (with cover, contain, or stretch sizing options).
- **Positioning Engine**: Precisely position your cutout mask and bottom text layer using `x`, `y` anchors (e.g., `center`, `bottom`) paired with detailed margin controls (`margin_top`, `margin_bottom`, etc.).
- **Beat-Sync & Dynamic Impact**: Synchronize the "pop-in" of photos to the audio track's beat. The engine analyzes beat strength, triggering explosive photo drops and bright visual flashes on major beats (drops), while subtly revealing tiles on softer beats.
- **Tubelight Flicker Animation**: Photos pop into the grid with a cool, randomized fluorescent blinking effect.
- **Fully Configurable JSON**: Completely control grid sizes, layout, colors, overlays, blur radius, fonts, and duration using a nested JSON configuration file.
- **EXIF Auto-Correction**: Automatically rotates portrait/landscape photos correctly based on EXIF data.

## Installation

1. Ensure you have [Python 3.7+](https://www.python.org/) installed.
2. If using `uv`, the dependencies are managed for you. Otherwise, install the required Python dependencies:
   ```bash
   pip install pillow moviepy numpy svglib reportlab librosa
   ```

## Usage

The generator relies completely on a nested JSON configuration file. To run the generator:

```bash
python main.py --config config.json
```

If you use `uv`, you can run:
```bash
uv run python main.py --config config.json
```

## Configuration Options

Below is an example of the structured `config.json` file. The schema is deeply nested for organization.

### Example `config.json`

```json
{
  "output": "output.mp4",
  "width": 1080,
  "height": 1920,
  "fps": 30,
  "target_duration": 10.0,
  "hold_duration": 3.0,
  "audio": "song.mp3",
  "grid": {
    "image_dir": "pictures",
    "square_size": 215,
    "gap": 5,
    "appear_interval": 0.2,
    "order": "random"
  },
  "bg": {
    "type": "image",
    "image": "DSC_0073.JPG",
    "size": "cover",
    "color": "#000000",
    "gradient": {
      "start": "#000000",
      "end": "#ffffff"
    },
    "blur_radius": 10,
    "overlay": {
      "color": "#000000",
      "opacity": 0.5
    }
  },
  "cutout": {
    "type": "text",
    "text": "3",
    "font": "AlfaSlabOne-Regular.ttf",
    "file": null,
    "scale": 1.0,
    "border_color": "#FFB7CE",
    "border_width": 0,
    "position": {
      "x": "center",
      "y": "center",
      "margin_top": 0,
      "margin_bottom": 50,
      "margin_left": 0,
      "margin_right": 0
    },
    "etched": {
      "enabled": true,
      "shadow_blur": 15,
      "offset_x": 15,
      "offset_y": 15,
      "shadow_opacity": 0.8,
      "shadow_color": "#000000",
      "highlight_opacity": 0.3,
      "highlight_color": "#ffffff"
    }
  },
  "text_layer": {
    "text": "Happy\nAnniversary",
    "font": "LavishlyYours-Regular.ttf",
    "font_size": 108,
    "color": "#FFB7CE",
    "position": {
      "x": "center",
      "y": "bottom",
      "margin_top": 0,
      "margin_bottom": 100,
      "margin_left": 0,
      "margin_right": 0
    }
  }
}
```

### Key Settings Explained
- **`audio` & `target_duration`**: Providing an audio file ensures photos synchronize to the beat of the music! The video will attempt to reach `target_duration` (seconds).
- **`bg.type`**: Can be `"image"`, `"solid"`, or `"gradient"`. Depending on the choice, the respective inner properties are used. 
- **`bg.size`**: Valid only for images. Options include `"cover"`, `"contain"`, and `"stretch"`.
- **`bg.overlay`**: Adds a color tint to your background. Set `opacity` between `0.0` (invisible) and `1.0` (solid).
- **`cutout.type`**: Can be `"text"`, `"svg"`, or `"image"`. If `"svg"` or `"image"`, use `cutout.file` to point to your `.svg` or `.png` (transparent or white background) file. If `"text"`, `cutout.text` is used.
- **`cutout.scale`**: (Optional) For `"svg"` and `"image"` types, a float multiplier (e.g., `1.2` or `0.8`) to finely adjust the final size of the cutout shape.
- **`cutout.border_width` & `cutout.border_color`**: Add a colored outline to your text or shape cutout (e.g., `border_width: 5`).
- **`cutout.etched`**: Gives your cutout shape a realistic "3D carved/etched-in" look using configurable inner shadows and highlights.
- **`position` blocks**: Specify exactly where elements are anchored (`"x"` can be `"center"`, `"left"`, `"right"`; `"y"` can be `"center"`, `"top"`, `"bottom"`). Further offset them using the `margin` properties.
