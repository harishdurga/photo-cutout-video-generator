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

### Configuration Reference

| JSON Key | Type | Description |
|----------|------|-------------|
| **`output`** | `String` | Filename and path for the final rendered video (e.g., `"output.mp4"`). |
| **`width` / `height`** | `Integer` | The resolution of the video in pixels (e.g., 1080x1920 for vertical). |
| **`fps`** | `Integer` | Frames per second for the rendered video. |
| **`target_duration`** | `Float` | The target duration of the photo reveal sequence in seconds. |
| **`hold_duration`** | `Float` | Extra duration in seconds to pause at the end after all photos have appeared. |
| **`audio`** | `String` | Path to an audio file (`.mp3`, `.wav`) to sync the photo pop-ins to the beat. |
| **`grid.image_dir`** | `String` | Path to the directory containing the photos. |
| **`grid.square_size`** | `Integer` | Size of each individual square photo tile in pixels. |
| **`grid.gap`** | `Integer` | Spacing gap between the photo tiles in pixels. |
| **`grid.appear_interval`** | `Float` | Time in seconds between photo appearances (used if no audio is provided). |
| **`grid.order`** | `String` | Appearance order: `"random"`, `"top_to_bottom"`, `"bottom_to_top"`, `"left_to_right"`, `"right_to_left"`. |
| **`bg.type`** | `String` | Background type: `"image"`, `"solid"`, or `"gradient"`. |
| **`bg.image`** | `String` | Path to the background image (used if `bg.type` is `"image"`). |
| **`bg.size`** | `String` | Sizing method for background image: `"cover"`, `"contain"`, or `"stretch"`. |
| **`bg.color`** | `String` | Hex color for solid backgrounds. |
| **`bg.gradient.start / end`**| `String` | Top and bottom hex colors for the gradient background. |
| **`bg.blur_radius`** | `Integer` | Gaussian blur radius applied to the background (0 to disable). |
| **`bg.overlay.color`** | `String` | Hex color for the background overlay tint. |
| **`bg.overlay.opacity`** | `Float` | Opacity of the background overlay (`0.0` invisible to `1.0` solid). |
| **`cutout.type`** | `String` | The type of mask to create: `"text"`, `"svg"`, or `"image"`. |
| **`cutout.text`** | `String` | The text string to use as a cutout (if type is `"text"`). |
| **`cutout.font`** | `String` | Path to a `.ttf` font file for the text cutout. |
| **`cutout.file`** | `String` | Path to a `.svg` or `.png` file (if type is `"svg"` or `"image"`). |
| **`cutout.scale`** | `Float` | Size multiplier for SVG/PNG shape cutouts (e.g., `1.2` or `0.8`). |
| **`cutout.border_color`** | `String` | Hex color for the border drawn around the cutout shape or text. |
| **`cutout.border_width`** | `Integer` | Thickness of the cutout border in pixels (set to `0` to disable). |
| **`cutout.position.x / y`** | `String` | Positional anchors: `"center"`, `"left"`, `"right"`, `"top"`, `"bottom"`. |
| **`cutout.position.margin_*`**| `Integer` | Additional offset margins (`margin_top`, `margin_bottom`, `margin_left`, `margin_right`). |
| **`cutout.etched.enabled`** | `Boolean` | Turn the inner shadow/highlight realistic "carved 3D" effect on or off. |
| **`cutout.etched.shadow_blur`** | `Integer` | Blur radius for the etched shadow. |
| **`cutout.etched.offset_x/y`** | `Integer` | Offset distance for the etched shadow and highlight. |
| **`cutout.etched.shadow_*`** | `String/Float`| Hex color and opacity for the inner shadow. |
| **`cutout.etched.highlight_*`**| `String/Float`| Hex color and opacity for the inner highlight. |
| **`text_layer.text`** | `String` | Optional text displayed globally on top of the final video. |
| **`text_layer.font`** | `String` | Path to a `.ttf` font file for the text overlay. |
| **`text_layer.font_size`** | `Integer` | Font size for the text overlay. |
| **`text_layer.color`** | `String` | Hex color for the text overlay. |
| **`text_layer.position.*`** | `Object` | Positioning rules for the text layer (same schema as `cutout.position`). |
