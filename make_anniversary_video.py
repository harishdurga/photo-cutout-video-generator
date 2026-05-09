import os
import random
import argparse
import json
import tempfile
import atexit
import shutil
from PIL import Image, ImageFilter, ImageDraw, ImageFont, ImageOps
from moviepy import ImageClip, CompositeVideoClip, ColorClip
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM

def parse_arguments():
    parser = argparse.ArgumentParser(description="Configurable Video Generator")
    parser.add_argument("--config", type=str, help="Path to JSON config file")
    
    # CLI arguments that override config
    parser.add_argument("--image-dir", type=str, help="Directory containing pictures")
    parser.add_argument("--bg-image", type=str, help="Background image file")
    parser.add_argument("--output", type=str, help="Output video file")
    parser.add_argument("--width", type=int, help="Video width")
    parser.add_argument("--height", type=int, help="Video height")
    parser.add_argument("--fps", type=int, help="Frames per second")
    parser.add_argument("--appear-interval", type=float, help="Seconds between photo appearance")
    parser.add_argument("--hold-duration", type=float, help="Seconds to hold the final shape")
    parser.add_argument("--square-size", type=int, help="Size of grid squares")
    parser.add_argument("--gap", type=int, help="Gap between grid squares")
    parser.add_argument("--grid-cols", type=int, help="Grid columns")
    parser.add_argument("--grid-rows", type=int, help="Grid rows")
    parser.add_argument("--font-number", type=str, help="Font file for the large number")
    parser.add_argument("--font-number-size", type=int, help="Font size for the large number")
    parser.add_argument("--font-text", type=str, help="Font file for the bottom text")
    parser.add_argument("--font-text-size", type=int, help="Font size for the bottom text")
    parser.add_argument("--number", type=str, help="The massive cutout text")
    parser.add_argument("--text", type=str, help="The text at the bottom. Use \\n for newlines.")
    parser.add_argument("--text-color", type=str, help="Color of the text")
    parser.add_argument("--blur-radius", type=int, help="Background blur radius")
    parser.add_argument("--cutout-border-color", type=str, help="Color of the cutout border")
    parser.add_argument("--cutout-border-width", type=int, help="Width of the cutout border")
    parser.add_argument("--svg-file", type=str, help="Path to an SVG file to use as the cutout shape instead of text")

    return parser.parse_args()

def load_config(args):
    # Default settings
    config = {
        "image_dir": "pictures",
        "bg_image": "DSC_0073.JPG",
        "output": "anniversary_video.mp4",
        "width": 1080,
        "height": 1920,
        "fps": 30,
        "appear_interval": 0.2,
        "hold_duration": 3.0,
        "square_size": 215,
        "gap": 5,
        "grid_cols": 6,
        "grid_rows": 6,
        "font_number": "AlfaSlabOne-Regular.ttf",
        "font_number_size": 1500,
        "font_text": r"fonts\Lavishly_Yours\LavishlyYours-Regular.ttf",
        "font_text_size": 108,
        "number": "3",
        "text": "Happy\nAnniversary",
        "text_color": "#FFB7CE",
        "blur_radius": 10,
        "cutout_border_color": "#FFB7CE",
        "cutout_border_width": 10,
        "svg_file": None
    }

    # Load JSON config if provided
    if args.config:
        try:
            with open(args.config, 'r') as f:
                file_config = json.load(f)
                config.update(file_config)
        except Exception as e:
            print(f"Error loading config file: {e}")

    # Override with CLI arguments if provided
    for key, value in vars(args).items():
        if value is not None and key != 'config':
            # Map argparse names to config names (e.g., image_dir)
            config[key] = value

    # Resolve paths relative to the config file's directory to make it robust across OS and working directories
    if args.config:
        config_dir = os.path.dirname(os.path.abspath(args.config))
        path_keys = ['image_dir', 'font_number', 'font_text', 'svg_file']
        for k in path_keys:
            if k in config and config[k] and not os.path.isabs(config[k]):
                config[k] = os.path.join(config_dir, config[k])
        # Note: bg_image is loaded relative to image_dir, so we don't need to resolve it here

    return config

def center_crop(img, target_width, target_height):
    width, height = img.size
    aspect = width / height
    target_aspect = target_width / target_height

    if aspect > target_aspect:
        new_width = int(height * target_aspect)
        left = (width - new_width) / 2
        top = 0
        right = (width + new_width) / 2
        bottom = height
    else:
        new_height = int(width / target_aspect)
        left = 0
        top = (height - new_height) / 2
        right = width
        bottom = (height + new_height) / 2

    img = img.crop((left, top, right, bottom))
    return img.resize((target_width, target_height), Image.Resampling.LANCZOS)

def create_background_mask(config):
    bg_path = os.path.join(config["image_dir"], config["bg_image"])
    video_size = (config["width"], config["height"])
    
    if not os.path.exists(bg_path):
        print(f"Warning: Background image {bg_path} not found. Using solid dark gray background.")
        img = Image.new('RGB', video_size, (230, 230, 230))
    else:
        img = Image.open(bg_path)
        img = ImageOps.exif_transpose(img) # FIX FOR LANDSCAPE/PORTRAIT ISSUE
        img = img.convert("RGB")
        img = center_crop(img, video_size[0], video_size[1])
        img = img.convert("L").convert("RGB")
        img = img.filter(ImageFilter.GaussianBlur(radius=config["blur_radius"]))
        
    mask = Image.new('L', video_size, color=255)
    mask_draw = ImageDraw.Draw(mask)
    img_draw = ImageDraw.Draw(img)
    
    try:
        font_small = ImageFont.truetype(config["font_text"], size=config["font_text_size"])
    except IOError:
        print("Warning: Could not load font for text. Using default.")
        font_small = ImageFont.load_default()

    # Determine cutout shape and borders
    svg_file = config.get("svg_file")
    border_width = config.get("cutout_border_width", 0)
    border_color = config.get("cutout_border_color", "#FFB7CE")
    
    if svg_file and os.path.exists(svg_file):
        drawing = svg2rlg(svg_file)
        if drawing:
            # Render SVG to PIL
            svg_img = renderPM.drawToPIL(drawing)
            
            # Create alpha channel by inverting the grayscale luminance.
            # svglib/renderPM defaults to a white background. By inverting, 
            # white background becomes 0 (transparent), and dark shapes become 255 (opaque).
            alpha_channel = ImageOps.invert(svg_img.convert('L'))
            
            # Scale SVG to fit nicely in the center. Similar to the text size, let's say max 80% of width, 50% of height.
            max_w, max_h = video_size[0] * 0.8, video_size[1] * 0.5
            scale = min(max_w / svg_img.width, max_h / svg_img.height)
            new_size = (int(svg_img.width * scale), int(svg_img.height * scale))
            alpha_channel = alpha_channel.resize(new_size, Image.Resampling.LANCZOS)
            
            x_num = int((video_size[0] - new_size[0]) / 2)
            y_num = int((video_size[1] - new_size[1]) / 2) - 300
            
            if border_width > 0:
                # Pillow's MaxFilter can only be an odd square.
                filter_size = border_width * 2 + 1
                dilated_alpha = alpha_channel.filter(ImageFilter.MaxFilter(filter_size))
                border_layer = Image.new('RGB', new_size, color=border_color)
                border_layer.putalpha(dilated_alpha)
                img.paste(border_layer, (x_num, y_num), border_layer)
            
            # Cutout from the mask
            # mask is white. We paste black using the original alpha to cut the hole
            cutout_shape = Image.new('L', new_size, color=0)
            mask.paste(cutout_shape, (x_num, y_num), alpha_channel)
        else:
            print(f"Warning: Could not load SVG {svg_file}. Falling back to text.")
            svg_file = None
            
    if not svg_file or not os.path.exists(svg_file):
        try:
            font_large = ImageFont.truetype(config["font_number"], size=config["font_number_size"])
        except IOError:
            print("Warning: Could not load thick font for cutout. Using default.")
            font_large = ImageFont.load_default()

        # Draw the massive cutout text
        text_number = str(config["number"])
        text_number = text_number.replace('\\n', '\n')
        
        bbox_num = mask_draw.textbbox((0, 0), text_number, font=font_large)
        w_num = bbox_num[2] - bbox_num[0]
        h_num = bbox_num[3] - bbox_num[1]
        
        x_num = (video_size[0] - w_num) / 2
        y_num = (video_size[1] - h_num) / 2 - bbox_num[1] - 300 
        
        mask_draw.multiline_text((x_num, y_num), text_number, font=font_large, fill=0, align="center")

        if border_width > 0:
            border_width_adjusted = border_width * 2 
            img_draw.multiline_text((x_num, y_num), text_number, font=font_large, fill=(0,0,0), stroke_width=border_width_adjusted, stroke_fill=border_color, align="center")

    # Draw bottom text
    raw_text = str(config["text"]).replace('\\n', '\n')
    lines = raw_text.split('\n')
    
    base_y = video_size[1] - 550
    line_spacing = config["font_text_size"] * 1.2
    
    for i, line in enumerate(lines):
        bbox = img_draw.textbbox((0, 0), line, font=font_small)
        w = bbox[2] - bbox[0]
        x = (video_size[0] - w) / 2
        y = base_y + (i * line_spacing)
        img_draw.text((x, y), line, font=font_small, fill=config["text_color"], stroke_width=2, stroke_fill=config["text_color"])
    
    img.putalpha(mask)
    return img

def get_random_images(image_dir, count, exclude_name):
    valid_extensions = ('.jpg', '.jpeg', '.png')
    if not os.path.exists(image_dir):
        return []
        
    all_files = os.listdir(image_dir)
    img_files = [f for f in all_files if f.lower().endswith(valid_extensions) and f != exclude_name]
    
    if not img_files:
        return []
        
    if len(img_files) < count:
        selected = random.choices(img_files, k=count)
    else:
        selected = random.sample(img_files, count)
        
    return [os.path.join(image_dir, f) for f in selected]

def main():
    args = parse_arguments()
    config = load_config(args)
    
    print(f"Loaded configuration:")
    for k, v in config.items():
        print(f"  {k}: {v}")
        
    # Ensure output directory exists so video saving doesn't fail
    out_dir = os.path.dirname(os.path.abspath(config["output"]))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    # Use a secure temporary directory that auto-cleans on exit
    temp_dir = tempfile.mkdtemp()
    atexit.register(lambda: shutil.rmtree(temp_dir, ignore_errors=True))

    print("\nPreparing cutout background...")
    bg_img = create_background_mask(config)
    bg_path_temp = os.path.join(temp_dir, "temp_bg_mask.png")
    bg_img.save(bg_path_temp)
    
    grid_cols = config["grid_cols"]
    grid_rows = config["grid_rows"]
    square_size = config["square_size"]
    gap = config["gap"]
    video_size = (config["width"], config["height"])
    
    grid_coords = [(c, r) for c in range(grid_cols) for r in range(grid_rows)]
    random.shuffle(grid_coords)
    
    total_photos = len(grid_coords)
    total_duration = total_photos * config["appear_interval"] + config["hold_duration"]
    
    # Base black layer
    base_clip = ColorClip(size=video_size, color=(0,0,0)).with_duration(total_duration)
    clips = [base_clip]
    
    print("Selecting and preparing photos...")
    photo_paths = get_random_images(config["image_dir"], total_photos, config["bg_image"])
    
    if not photo_paths:
        print(f"Error: No valid images found in {config['image_dir']}")
        return

    total_grid_width = grid_cols * square_size + (grid_cols - 1) * gap
    total_grid_height = grid_rows * square_size + (grid_rows - 1) * gap
    start_x = (video_size[0] - total_grid_width) // 2
    # Match the shift of the cutout (-300 upwards offset)
    start_y = (video_size[1] - total_grid_height) // 2 - 300 
    
    for i, (col, row) in enumerate(grid_coords):
        img_path = photo_paths[i]
        
        try:
            img = Image.open(img_path)
            img = ImageOps.exif_transpose(img) # EXIF Fix
            img = img.convert("RGB")
            img = center_crop(img, square_size, square_size)
            temp_name = os.path.join(temp_dir, f"temp_sq_{i}.jpg")
            img.save(temp_name)
            
            x_pos = start_x + col * (square_size + gap)
            y_pos = start_y + row * (square_size + gap)
            
            start_time = i * config["appear_interval"]
            
            # TUBELIGHT FLICKER EFFECT
            # Flicker 1: ON (0.05s)
            clip1 = (ImageClip(temp_name)
                    .with_start(start_time)
                    .with_duration(0.04)
                    .with_position((x_pos, y_pos)))
            
            # Flicker 2: ON (0.05s)
            clip2 = (ImageClip(temp_name)
                    .with_start(start_time + 0.08)
                    .with_duration(0.04)
                    .with_position((x_pos, y_pos)))
            
            # Final: Solid ON
            final_start = start_time + 0.16
            clip_solid = (ImageClip(temp_name)
                    .with_start(final_start)
                    .with_duration(total_duration - final_start)
                    .with_position((x_pos, y_pos)))
            
            clips.extend([clip1, clip2, clip_solid])
            
        except Exception as e:
            print(f"Error processing {img_path}: {e}")
            
    wall_clip = ImageClip(bg_path_temp).with_start(0).with_duration(total_duration).with_position((0,0))
    clips.append(wall_clip)
            
    print("Rendering video... This might take a few minutes because of the tubelight effect!")
    final_video = CompositeVideoClip(clips, size=video_size)
    final_video.write_videofile(config["output"], fps=config["fps"], codec="libx264", audio=False)
    
    print(f"\nDone! Your video is ready at: {os.path.abspath(config['output'])}")

if __name__ == "__main__":
    main()
