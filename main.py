import os
import random
import argparse
import json
import tempfile
import atexit
import shutil
import concurrent.futures
import numpy as np
import math
from PIL import Image, ImageFilter, ImageDraw, ImageFont, ImageOps
from moviepy import ImageClip, CompositeVideoClip, ColorClip, VideoClip, AudioFileClip
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
import librosa

def parse_arguments():
    parser = argparse.ArgumentParser(description="Configurable Video Generator")
    parser.add_argument("--config", type=str, help="Path to JSON config file", default="config.json")
    return parser.parse_args()

def load_config(args):
    # Base defaults for nested config
    config = {
        "output": "output.mp4",
        "width": 1080,
        "height": 1920,
        "fps": 30,
        "target_duration": 10.0,
        "hold_duration": 3.0,
        "audio": None,
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
            "gradient": {"start": "#000000", "end": "#ffffff"},
            "blur_radius": 10,
            "overlay": {"color": "#000000", "opacity": 0.0}
        },
        "cutout": {
            "type": "text",
            "text": "3",
            "font": "AlfaSlabOne-Regular.ttf",
            "svg_file": None,
            "border_color": "#FFB7CE",
            "border_width": 0,
            "position": {"x": "center", "y": "center", "margin_top": 0, "margin_bottom": 0, "margin_left": 0, "margin_right": 0}
        },
        "text_layer": {
            "text": "Happy\nAnniversary",
            "font": "LavishlyYours-Regular.ttf",
            "font_size": 108,
            "color": "#FFB7CE",
            "position": {"x": "center", "y": "bottom", "margin_top": 0, "margin_bottom": 100, "margin_left": 0, "margin_right": 0}
        }
    }

    if args.config and os.path.exists(args.config):
        try:
            with open(args.config, 'r') as f:
                file_config = json.load(f)
                
                # Simple recursive update for nested dicts
                def update_dict(d, u):
                    for k, v in u.items():
                        if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                            update_dict(d[k], v)
                        else:
                            d[k] = v
                
                update_dict(config, file_config)
        except Exception as e:
            print(f"Error loading config file: {e}")

    # Resolve paths relative to config file directory
    if args.config and os.path.exists(args.config):
        config_dir = os.path.dirname(os.path.abspath(args.config))
        
        # Audio
        if config.get("audio") and not os.path.isabs(config["audio"]):
            config["audio"] = os.path.join(config_dir, config["audio"])
            
        # Grid image_dir
        if config["grid"].get("image_dir") and not os.path.isabs(config["grid"]["image_dir"]):
            config["grid"]["image_dir"] = os.path.join(config_dir, config["grid"]["image_dir"])
            
        # bg image
        if config["bg"].get("image") and not os.path.isabs(config["bg"]["image"]):
            # Relative to image_dir or config_dir
            if os.path.exists(os.path.join(config["grid"]["image_dir"], config["bg"]["image"])):
                config["bg"]["image"] = os.path.join(config["grid"]["image_dir"], config["bg"]["image"])
            else:
                config["bg"]["image"] = os.path.join(config_dir, config["bg"]["image"])
                
        # cutout font/svg/file
        for k in ["font", "svg_file", "file"]:
            if config["cutout"].get(k) and not os.path.isabs(config["cutout"][k]):
                config["cutout"][k] = os.path.join(config_dir, config["cutout"][k])
                
        # text_layer font
        if config["text_layer"].get("font") and not os.path.isabs(config["text_layer"]["font"]):
            config["text_layer"]["font"] = os.path.join(config_dir, config["text_layer"]["font"])

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

def contain_resize(img, target_width, target_height):
    width, height = img.size
    aspect = width / height
    target_aspect = target_width / target_height

    if aspect > target_aspect:
        new_width = target_width
        new_height = int(target_width / aspect)
    else:
        new_height = target_height
        new_width = int(target_height * aspect)
        
    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    canvas = Image.new('RGB', (target_width, target_height), (0,0,0))
    canvas.paste(img, ((target_width - new_width)//2, (target_height - new_height)//2))
    return canvas

def create_gradient(width, height, color1, color2):
    base = Image.new('RGB', (width, height), color1)
    top = Image.new('RGB', (width, height), color2)
    mask = Image.new('L', (width, height))
    mask_data = []
    for y in range(height):
        mask_data.extend([int(255 * (y / height))] * width)
    mask.putdata(mask_data)
    base.paste(top, (0, 0), mask)
    return base

def calculate_position(pos_config, item_w, item_h, container_w, container_h):
    x_spec = pos_config.get("x", "center")
    y_spec = pos_config.get("y", "center")
    
    if isinstance(x_spec, str):
        if x_spec == "center":
            x = (container_w - item_w) // 2
        elif x_spec == "left":
            x = 0
        elif x_spec == "right":
            x = container_w - item_w
        else:
            x = 0
    else:
        x = int(x_spec)
        
    if isinstance(y_spec, str):
        if y_spec == "center":
            y = (container_h - item_h) // 2
        elif y_spec == "top":
            y = 0
        elif y_spec == "bottom":
            y = container_h - item_h
        else:
            y = 0
    else:
        y = int(y_spec)
        
    x += pos_config.get("margin_left", 0) or 0
    x -= pos_config.get("margin_right", 0) or 0
    y += pos_config.get("margin_top", 0) or 0
    y -= pos_config.get("margin_bottom", 0) or 0
    
    return int(x), int(y)

def create_background_mask(config):
    video_size = (config["width"], config["height"])
    bg_config = config["bg"]
    
    # 1. Base Background
    if bg_config["type"] == "gradient":
        start_c = bg_config["gradient"].get("start", "#000000")
        end_c = bg_config["gradient"].get("end", "#ffffff")
        img = create_gradient(video_size[0], video_size[1], start_c, end_c)
    elif bg_config["type"] == "solid":
        img = Image.new('RGB', video_size, bg_config.get("color", "#000000"))
    else: # image
        bg_path = bg_config.get("image", "")
        if not os.path.exists(bg_path):
            print(f"Warning: Background image {bg_path} not found. Using solid dark gray.")
            img = Image.new('RGB', video_size, (50, 50, 50))
        else:
            img = Image.open(bg_path)
            img = ImageOps.exif_transpose(img)
            img = img.convert("RGB")
            
            size_mode = bg_config.get("size", "cover")
            if size_mode == "stretch":
                img = img.resize(video_size, Image.Resampling.LANCZOS)
            elif size_mode == "contain":
                img = contain_resize(img, video_size[0], video_size[1])
            else: # cover
                img = center_crop(img, video_size[0], video_size[1])
                
    # 2. Blur
    blur_radius = bg_config.get("blur_radius", 0)
    if blur_radius > 0:
        img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        
    # 3. Overlay
    overlay_cfg = bg_config.get("overlay")
    if overlay_cfg and overlay_cfg.get("opacity", 0) > 0:
        opacity = int(overlay_cfg["opacity"] * 255)
        overlay_color = overlay_cfg.get("color", "#000000")
        overlay_img = Image.new('RGBA', video_size, overlay_color)
        overlay_img.putalpha(opacity)
        img.paste(overlay_img, (0, 0), overlay_img)

    mask = Image.new('L', video_size, color=255)
    mask_draw = ImageDraw.Draw(mask)
    img_draw = ImageDraw.Draw(img)

    # 4. Cutout
    cutout_cfg = config["cutout"]
    border_width = cutout_cfg.get("border_width", 0)
    border_color = cutout_cfg.get("border_color", "#FFFFFF")
    
    cutout_center_x, cutout_center_y = video_size[0]//2, video_size[1]//2
    
    if cutout_cfg["type"] in ["svg", "image"]:
        file_path = cutout_cfg.get("file", cutout_cfg.get("svg_file"))
        if file_path and os.path.exists(file_path):
            alpha_channel = None
            if cutout_cfg["type"] == "svg":
                drawing = svg2rlg(file_path)
                if drawing:
                    svg_img = renderPM.drawToPIL(drawing)
                    alpha_channel = ImageOps.invert(svg_img.convert('L'))
            else:
                img_mask = Image.open(file_path)
                if img_mask.mode == 'RGBA':
                    alpha = img_mask.split()[3]
                    if alpha.getextrema() == (255, 255):
                        alpha_channel = ImageOps.invert(img_mask.convert('L'))
                    else:
                        alpha_channel = alpha
                else:
                    alpha_channel = ImageOps.invert(img_mask.convert('L'))
            
            if alpha_channel:
                bbox = alpha_channel.getbbox()
                if bbox:
                    alpha_channel = alpha_channel.crop(bbox)
                
                max_w, max_h = video_size[0] * 0.85, video_size[1] * 0.65
                scale = min(max_w / alpha_channel.width, max_h / alpha_channel.height)
                scale *= cutout_cfg.get("scale", 1.0)
                new_size = (int(alpha_channel.width * scale), int(alpha_channel.height * scale))
                alpha_channel = alpha_channel.resize(new_size, Image.Resampling.LANCZOS)
                
                x_num, y_num = calculate_position(cutout_cfg.get("position", {}), new_size[0], new_size[1], video_size[0], video_size[1])
                cutout_center_x, cutout_center_y = x_num + new_size[0]//2, y_num + new_size[1]//2
                
                if border_width > 0:
                    filter_size = border_width * 2 + 1
                    dilated_alpha = alpha_channel.filter(ImageFilter.MaxFilter(filter_size))
                    border_layer = Image.new('RGB', new_size, color=border_color)
                    border_layer.putalpha(dilated_alpha)
                    img.paste(border_layer, (x_num, y_num), border_layer)
                
                cutout_shape = Image.new('L', new_size, color=0)
                mask.paste(cutout_shape, (x_num, y_num), alpha_channel)
    else:
        # Text cutout
        cutout_text = str(cutout_cfg.get("text", "")).replace('\\n', '\n')
        font_path = cutout_cfg.get("font", "")
        
        target_width = video_size[0] * 0.90
        target_height = video_size[1] * 0.70
        
        try:
            base_size = 100
            font_large = ImageFont.truetype(font_path, size=base_size)
            bbox = mask_draw.textbbox((0, 0), cutout_text, font=font_large)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            
            if w > 0 and h > 0:
                scale_ratio = min(target_width / w, target_height / h)
                optimal_size = int(base_size * scale_ratio)
                font_large = ImageFont.truetype(font_path, size=optimal_size)
                
                bbox = mask_draw.textbbox((0, 0), cutout_text, font=font_large)
                while (bbox[2] - bbox[0] > target_width or bbox[3] - bbox[1] > target_height) and optimal_size > 10:
                    optimal_size -= 20
                    font_large = ImageFont.truetype(font_path, size=optimal_size)
                    bbox = mask_draw.textbbox((0, 0), cutout_text, font=font_large)
            else:
                font_large = ImageFont.truetype(font_path, size=1500)
        except IOError:
            print("Warning: Could not load thick font for cutout. Using default.")
            font_large = ImageFont.load_default()

        bbox_num = mask_draw.textbbox((0, 0), cutout_text, font=font_large)
        w_num = bbox_num[2] - bbox_num[0]
        h_num = bbox_num[3] - bbox_num[1]
        
        x_num, y_num = calculate_position(cutout_cfg.get("position", {}), w_num, h_num, video_size[0], video_size[1])
        # Textbbox offset needs to be accounted for in Pillow text drawing
        actual_x = x_num - bbox_num[0]
        actual_y = y_num - bbox_num[1]
        
        cutout_center_x, cutout_center_y = x_num + w_num//2, y_num + h_num//2
        
        mask_draw.multiline_text((actual_x, actual_y), cutout_text, font=font_large, fill=0, align="center")

        if border_width > 0:
            border_width_adjusted = border_width * 2 
            img_draw.multiline_text((actual_x, actual_y), cutout_text, font=font_large, fill=(0,0,0), stroke_width=border_width_adjusted, stroke_fill=border_color, align="center")

    # Etched Inner Shadow & Highlight
    etched_cfg = cutout_cfg.get("etched", {})
    if etched_cfg.get("enabled", False):
        from PIL import ImageChops
        shadow_blur = etched_cfg.get("shadow_blur", 15)
        offset_x = etched_cfg.get("offset_x", 15)
        offset_y = etched_cfg.get("offset_y", 15)
        shadow_opacity = etched_cfg.get("shadow_opacity", 0.8)
        shadow_color = etched_cfg.get("shadow_color", "#000000")
        highlight_opacity = etched_cfg.get("highlight_opacity", 0.3)
        highlight_color = etched_cfg.get("highlight_color", "#ffffff")
        
        # Blur the mask (wall is white, hole is black)
        mask_blur = mask.filter(ImageFilter.GaussianBlur(shadow_blur))
        
        # Hole shape (white inside hole, black outside)
        S = ImageOps.invert(mask)
        
        # 1. Shadow (offset positive)
        if shadow_opacity > 0:
            shadow_intensity = Image.new('L', video_size, 0)
            shadow_intensity.paste(mask_blur, (offset_x, offset_y))
            # Restrict to hole
            inner_shadow_alpha = ImageChops.darker(shadow_intensity, S)
            if shadow_opacity < 1.0:
                inner_shadow_alpha = inner_shadow_alpha.point(lambda p: int(p * shadow_opacity))
            
            shadow_layer = Image.new('RGB', video_size, shadow_color)
            img.paste(shadow_layer, (0, 0), inner_shadow_alpha)
            mask = ImageChops.lighter(mask, inner_shadow_alpha)
            
        # 2. Highlight (offset negative)
        if highlight_opacity > 0:
            highlight_intensity = Image.new('L', video_size, 0)
            highlight_intensity.paste(mask_blur, (-offset_x, -offset_y))
            inner_highlight_alpha = ImageChops.darker(highlight_intensity, S)
            if highlight_opacity < 1.0:
                inner_highlight_alpha = inner_highlight_alpha.point(lambda p: int(p * highlight_opacity))
                
            highlight_layer = Image.new('RGB', video_size, highlight_color)
            img.paste(highlight_layer, (0, 0), inner_highlight_alpha)
            mask = ImageChops.lighter(mask, inner_highlight_alpha)

    # 5. Text Layer
    text_cfg = config.get("text_layer", {})
    if text_cfg and text_cfg.get("text"):
        try:
            font_small = ImageFont.truetype(text_cfg.get("font", ""), size=text_cfg.get("font_size", 50))
        except IOError:
            font_small = ImageFont.load_default()
            
        raw_text = str(text_cfg["text"]).replace('\\n', '\n')
        lines = raw_text.split('\n')
        line_spacing = text_cfg.get("font_size", 50) * 1.2
        
        # Calculate full text block size
        max_w = 0
        total_h = len(lines) * line_spacing
        for line in lines:
            bbox = img_draw.textbbox((0, 0), line, font=font_small)
            max_w = max(max_w, bbox[2] - bbox[0])
            
        text_x, text_y = calculate_position(text_cfg.get("position", {}), max_w, total_h, video_size[0], video_size[1])
        
        for i, line in enumerate(lines):
            bbox = img_draw.textbbox((0, 0), line, font=font_small)
            w = bbox[2] - bbox[0]
            # Center each line individually horizontally relative to the text block bounds, if position x is center, else just align left
            x_spec = text_cfg.get("position", {}).get("x", "center")
            if x_spec == "center":
                x = text_x + (max_w - w) / 2
            else:
                x = text_x
                
            y = text_y + (i * line_spacing)
            img_draw.text((x, y), line, font=font_small, fill=text_cfg.get("color", "#FFFFFF"), stroke_width=2, stroke_fill=text_cfg.get("color", "#FFFFFF"))
    
    img.putalpha(mask)
    return img, (cutout_center_x, cutout_center_y)

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
    
    print("Configuration loaded.")
    out_dir = os.path.dirname(os.path.abspath(config["output"]))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    temp_dir = tempfile.mkdtemp()
    atexit.register(lambda: shutil.rmtree(temp_dir, ignore_errors=True))

    print("\nPreparing background and mask...")
    bg_img, cutout_center = create_background_mask(config)
    bg_path_temp = os.path.join(temp_dir, "temp_bg_mask.png")
    bg_img.save(bg_path_temp)
    
    grid_cfg = config["grid"]
    square_size = grid_cfg["square_size"]
    gap = grid_cfg["gap"]
    video_size = (config["width"], config["height"])
    
    grid_cols = math.ceil(video_size[0] / (square_size + gap)) + 1 # +1 to ensure full coverage 
    grid_rows = math.ceil(video_size[1] / (square_size + gap)) + 1
    
    grid_coords = [(c, r) for c in range(grid_cols) for r in range(grid_rows)]
    order = grid_cfg.get("order", "random").lower().replace("-", "_")
    
    if order == "top_to_bottom":
        grid_coords.sort(key=lambda x: (x[1], x[0]))
    elif order == "bottom_to_top":
        grid_coords.sort(key=lambda x: (-x[1], x[0]))
    elif order == "left_to_right":
        grid_coords.sort(key=lambda x: (x[0], x[1]))
    elif order == "right_to_left":
        grid_coords.sort(key=lambda x: (-x[0], x[1]))
    else: # random
        random.shuffle(grid_coords)
    
    total_photos = len(grid_coords)
    
    reveal_duration = float(config.get("target_duration") or 10.0)
    total_duration = reveal_duration + config["hold_duration"]
    grid_cfg["appear_interval"] = max(0.01, reveal_duration / total_photos)
    
    audio_clip = None
    beat_times = []
    
    if config.get("audio") and os.path.exists(config["audio"]):
        print(f"Loading audio and detecting beats from {config['audio']}...")
        y, sr = librosa.load(config["audio"], duration=reveal_duration)
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        beat_times = librosa.frames_to_time(beat_frames, sr=sr).tolist()
        
        audio_file = AudioFileClip(config["audio"])
        audio_duration = min(total_duration, audio_file.duration)
        audio_clip = audio_file.subclipped(0, audio_duration)
        
    base_clip = ColorClip(size=video_size, color=(0,0,0)).with_duration(total_duration)
    
    print("Selecting photos...")
    exclude_img = config["bg"].get("image", "") if config["bg"]["type"] == "image" else ""
    if exclude_img:
        exclude_img = os.path.basename(exclude_img)
        
    photo_paths = get_random_images(grid_cfg["image_dir"], total_photos, exclude_img)
    
    if not photo_paths:
        print(f"Error: No valid images found in {grid_cfg['image_dir']}")
        return

    total_grid_width = grid_cols * square_size + (grid_cols - 1) * gap
    total_grid_height = grid_rows * square_size + (grid_rows - 1) * gap
    
    # Align the grid center with the cutout center so the photo tiles fully back the cutout
    start_x = cutout_center[0] - total_grid_width // 2
    start_y = cutout_center[1] - total_grid_height // 2
    
    def process_image(i, img_path):
        try:
            img = Image.open(img_path)
            img = ImageOps.exif_transpose(img)
            img = img.convert("RGB")
            img = center_crop(img, square_size, square_size)
            temp_name = os.path.join(temp_dir, f"temp_sq_{i}.jpg")
            img.save(temp_name)
            return i, temp_name
        except Exception as e:
            return None

    print("Processing images in parallel...")
    processed_images = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for i, (col, row) in enumerate(grid_coords):
            img_path = photo_paths[i]
            futures.append(executor.submit(process_image, i, img_path))
        
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res:
                processed_images.append(res)
    
    processed_images.sort(key=lambda x: x[0])
    
    print("Preparing frame generation logic...")
    wall_img = Image.open(bg_path_temp).convert("RGBA")
    
    loaded_photos = []
    
    photos_per_beat = 1
    if audio_clip and beat_times:
        photos_per_beat = math.ceil(len(processed_images) / max(1, len(beat_times)))

    for i, temp_name in processed_images:
        col, row = grid_coords[i]
        
        x_pos = start_x + col * (square_size + gap)
        y_pos = start_y + row * (square_size + gap)
        
        if x_pos + square_size <= 0 or y_pos + square_size <= 0 or x_pos >= video_size[0] or y_pos >= video_size[1]:
            continue
            
        if audio_clip and beat_times:
            beat_idx = min(i // photos_per_beat, len(beat_times) - 1)
            start_time = beat_times[beat_idx]
            start_time += (i % photos_per_beat) * 0.005 
        else:
            start_time = i * grid_cfg["appear_interval"]
            
        loaded_photos.append({
            'img': Image.open(temp_name).convert("RGB"),
            'x': int(x_pos),
            'y': int(y_pos),
            'start_time': start_time
        })

    def make_frame(t):
        frame = Image.new('RGB', video_size, (0, 0, 0))
        for photo in loaded_photos:
            if t >= photo['start_time'] + 0.16:
                frame.paste(photo['img'], (photo['x'], photo['y']))
            elif t >= photo['start_time']:
                dt = t - photo['start_time']
                if (0 <= dt < 0.041) or (0.08 <= dt < 0.121):
                    frame.paste(photo['img'], (photo['x'], photo['y']))
        
        frame.paste(wall_img, (0, 0), wall_img)
        return np.array(frame)

    print("Rendering video...")
    final_video = VideoClip(make_frame, duration=total_duration)
    if audio_clip:
        final_video = final_video.with_audio(audio_clip)
    final_video.write_videofile(config["output"], fps=config["fps"], codec="libx264", audio_codec="aac", threads=os.cpu_count())
    
    print(f"\nDone! Video is ready at: {os.path.abspath(config['output'])}")

if __name__ == "__main__":
    main()
