#!/usr/bin/env python3
"""
Character Lituli Prompt Generator + Seedream Renderer
Generates optimized English prompts and renders images via Doubao Seedream API.
"""

import os
import sys
import json
import base64
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

SEEDREAM_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
SEEDREAM_MODEL = "doubao-seedream-4-5-251128"


DEFAULT_BIBLE_DIR = Path.home() / "character_bible"

STYLE_PRESETS = {
    "anime": "anime art style, clean cel shading, vibrant colors, Japanese animation style, Studio Ghibli inspired aesthetic",
    "manga": "manga art style, hand-drawn aesthetic, soft color gradients, clean expressive linework, Japanese comic illustration style, warm and cinematic atmosphere",
    "manhua": "Chinese manhua donghua style, semi-realistic rendering, rich detailed shading, elegant color palette, refined linework, webcomic aesthetic",
    "realistic": "photorealistic style, detailed skin textures, natural cinematic lighting, realistic anatomical proportions, high fidelity rendering",
    "semi-realistic": "semi-realistic art style, stylized features with realistic rendering, detailed painterly quality, soft lighting, 3D rendered look",
    "cyberpunk": "cyberpunk art style, neon lighting, dark dystopian atmosphere, sci-fi aesthetic, high tech low life mood, Blade Runner inspired, rain-slicked streets",
    "fantasy": "fantasy illustration style, magical ethereal atmosphere, Dungeons & Dragons aesthetic, rich painterly rendering, dramatic lighting, epic fantasy art",
}

VIEW_PROMPTS = {
    "front": "front view, standing facing the viewer directly, full body centered, hands relaxed at sides, looking at camera",
    "three-quarter": "three-quarter angle view, body turned approximately 45 degrees, natural contrapposto standing pose, looking slightly to the side",
    "side": "side profile view, standing perpendicular to the viewer, full body visible, looking straight ahead in profile",
    "back": "back view, facing away from the viewer, showing back details of outfit and hairstyle, looking over shoulder slightly",
}

EXPRESSION_PROMPTS = {
    "neutral": "neutral calm expression, relaxed natural face, resting expression, composed serene look",
    "happy": "warm genuine smile, bright happy joyful expression, eyes slightly narrowed with joy, cheerful upbeat mood",
    "angry": "furrowed brows, angry determined expression, tense jaw, intense sharp glare, frustrated aggressive mood",
    "sad": "sad melancholic expression, slightly downturned mouth, sorrowful glistening eyes, gentle quiet sadness",
    "surprised": "surprised shocked expression, eyes wide open, slightly parted lips, eyebrows raised high, startled look",
    "thinking": "thoughtful contemplative expression, one hand touching chin, pensive gaze looking into distance, deep in thought",
    "smug": "smug confident smirk, one eyebrow raised, self-satisfied arrogant expression, knowing sideways glance",
    "blushing": "shy blushing expression, rosy pink cheeks, looking slightly away embarrassed, timid flustered smile",
    "serious": "serious focused expression, determined intense eyes, composed stoic face, professional no-nonsense demeanor",
    "laughing": "joyful laughing expression, open mouth happy smile, eyes closed in pure happiness, carefree cheerful mood",
}


def slugify(name: str) -> str:
    return name.strip().lower().replace(" ", "_").replace("-", "_")


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def get_profile_path(name: str, bible_dir: Path) -> Path:
    return bible_dir / f"{slugify(name)}.json"


def load_profile(name: str, bible_dir: Path) -> dict:
    path = get_profile_path(name, bible_dir)
    if not path.exists():
        print(f"Character '{name}' not found in {bible_dir}. Use 'create' first.")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_profile(profile: dict, bible_dir: Path):
    ensure_dir(bible_dir)
    path = get_profile_path(profile["name"], bible_dir)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)
    print(f"Saved: {path}")


def ask(prompt: str, default: str = "") -> str:
    if default:
        result = input(f"{prompt} [{default}]: ").strip()
        return result if result else default
    return input(f"{prompt}: ").strip()


def ask_required(prompt: str) -> str:
    while True:
        result = input(f"{prompt}: ").strip()
        if result:
            return result
        print("  (required)")


def cmd_create(args):
    bible_dir = Path(args.bible_dir).expanduser().resolve()
    name = args.name
    profile = {"name": name}

    print(f"\n{'='*50}")
    print(f"Create Character: {name}")
    print(f"Bible dir: {bible_dir}")
    print(f"{'='*50}\n")

    if args.description:
        profile["description_anchor"] = args.description
    else:
        print("--- Character Appearance ---")
        age = ask("Age (e.g. 'young woman in her mid-twenties')", "young woman")
        hair = ask_required("Hair (color, length, style)")
        eyes = ask_required("Eye color")
        skin = ask("Skin tone", "fair warm skin")
        build = ask("Build (e.g. 'slim athletic', 'average height')", "slim")
        features = ask("Distinctive features (e.g. 'beauty mark below left eye')", "")
        accessories = ask("Accessories (e.g. 'silver stud earrings, wristwatch')", "")

        parts = [f"{age} with {hair}, {eyes} eyes, {skin}, {build} build"]
        if features:
            parts.append(f"distinctive {features}")
        if accessories:
            parts.append(f"wearing {accessories}")

        profile["description_anchor"] = " ".join(parts)

    if args.outfit_default:
        profile["outfits"] = {"default": args.outfit_default}
    else:
        print("\n--- Default Outfit ---")
        top = ask("Top", "white t-shirt")
        outerwear = ask("Outerwear (leave empty for none)", "")
        bottom = ask("Bottom", "dark jeans")
        shoes = ask("Shoes", "sneakers")

        outfit_parts = [top]
        if outerwear:
            outfit_parts.insert(0, outerwear)
        outfit = f"{', '.join(outfit_parts)}, {bottom}, {shoes}"
        profile["outfits"] = {"default": outfit}

    if args.colors:
        colors = {}
        for pair in args.colors.split(","):
            k, v = pair.split("=", 1)
            colors[k.strip()] = v.strip()
        profile["color_palette"] = colors
    else:
        print("\n--- Color Palette (hex codes, enter to skip) ---")
        palette = {}
        for key in ["skin", "hair", "eyes", "primary", "accent"]:
            val = ask(f"  {key} (e.g. #F5D0A9)", "").strip()
            if val:
                palette[key] = val.lstrip("#") if not val.startswith("#") else val
        if palette:
            profile["color_palette"] = palette

    style = args.style if args.style else ask(
        f"\nArt style ({'/'.join(STYLE_PRESETS.keys())})", "manga"
    )
    profile["style_keywords"] = STYLE_PRESETS.get(style, STYLE_PRESETS["manga"])

    profile["default_pose"] = "standing, full body, hands at sides, looking at viewer, upright posture"
    profile["expressions"] = list(EXPRESSION_PROMPTS.keys())

    save_profile(profile, bible_dir)
    slug = slugify(name)
    print(f"\n{'='*50}")
    print(f"Character '{name}' created successfully!")
    print(f"Next: python character_lituli.py generate -b {bible_dir} -n {slug} --views front")
    print(f"{'='*50}")


def build_prompt(profile: dict, view: str, expression: str, outfit_key: str, prompt_style: str = "lituli") -> str:
    anchor = profile["description_anchor"]
    outfits = profile.get("outfits", {"default": "casual clothes"})
    outfit_text = outfits.get(outfit_key, outfits.get("default", "casual clothes"))
    view_text = VIEW_PROMPTS.get(view, VIEW_PROMPTS["front"])
    expr_text = EXPRESSION_PROMPTS.get(expression, EXPRESSION_PROMPTS["neutral"])

    if prompt_style == "design-sheet":
        # character-design-sheet style: concise, clean, turnaround-focused
        return (
            f"character design reference sheet, {view_text} of {anchor}, "
            f"wearing {outfit_text}, {expr_text}, "
            f"full body, clean white background, clean lines, concept art style, sharp details, character turnaround"
        )
    else:
        # lituli style: full narrative prompt
        style = profile.get("style_keywords", STYLE_PRESETS["manga"])
        pose = profile.get("default_pose", "standing, full body")
        return (
            f"{style}. Full body character standing illustration of {anchor}. "
            f"{pose}. {view_text}. Wearing {outfit_text}. "
            f"{expr_text}. "
            f"Clean white background, character reference sheet style, "
            f"professional concept art, high detail, consistent character design, "
            f"sharp focus, studio lighting."
        )


def cmd_generate(args):
    bible_dir = Path(args.bible_dir).expanduser().resolve()
    profile = load_profile(args.name, bible_dir)
    style = args.style or "manga"

    if args.style:
        profile["style_keywords"] = STYLE_PRESETS.get(args.style, STYLE_PRESETS["manga"])

    if args.all:
        views = ["front", "three-quarter", "side", "back"]
    elif args.views:
        views = args.views
    else:
        views = ["front"]

    if args.all:
        expressions = ["neutral", "happy", "angry", "sad", "surprised", "thinking"]
    elif args.expressions:
        expressions = args.expressions
    else:
        expressions = ["neutral"]

    outfit_key = args.outfit or "default"

    lines = []
    lines.append(f"# {profile['name'].replace('_', ' ').title()} - Lituli Prompts")
    lines.append(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"# Style: {style}")
    lines.append(f"# Outfit: {outfit_key}")
    lines.append("")

    if len(views) > 1 or len(expressions) > 1:
        lines.append("---")
        lines.append("")

    count = 0
    for view in views:
        for expr in expressions:
            count += 1
            prompt = build_prompt(profile, view, expr, outfit_key, args.prompt_style)
            view_name = VIEW_PROMPTS[view].split(",")[0].title()
            expr_name = EXPRESSION_PROMPTS[expr].split(",")[0].title()

            lines.append(f"## {count}. {view_name} - {expr_name}")
            lines.append("")
            lines.append("```")
            lines.append(prompt)
            lines.append("```")
            lines.append("")

    output = "\n".join(lines)

    # Default output path: same dir as bible, under <name>_prompts/
    if args.output:
        output_path = Path(args.output).expanduser()
    else:
        prompts_dir = bible_dir / f"{slugify(args.name)}_prompts"
        ensure_dir(prompts_dir)
        output_path = prompts_dir / f"prompts_{datetime.now().strftime('%Y%m%d_%H%M')}.md"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output)
    print(f"Saved {count} prompts to: {output_path}")

    # Also print first prompt as preview
    first = lines[lines.index("```") + 1] if "```" in lines else ""
    if first:
        print(f"\n{'='*50}")
        print(f"Preview (copy to Gemini web):")
        print(f"{'='*50}")
        print(first)
        print(f"{'='*50}")


def cmd_show(args):
    bible_dir = Path(args.bible_dir).expanduser().resolve()
    profile = load_profile(args.name, bible_dir)

    print(f"\n{'='*50}")
    print(f"  {profile['name'].replace('_', ' ').title()}")
    print(f"{'='*50}\n")

    print(f"Description Anchor:")
    print(f"  {profile['description_anchor']}\n")

    if "color_palette" in profile:
        print("Color Palette:")
        for k, v in profile["color_palette"].items():
            print(f"  {k:12s} # {v}")
        print()

    print("Outfits:")
    for k, v in profile.get("outfits", {}).items():
        print(f"  [{k}] {v}")
    print()

    print(f"Style: {profile.get('style_keywords', 'N/A')[:80]}...")
    print(f"Pose:  {profile.get('default_pose', 'N/A')}")
    print()


def cmd_render(args):
    if not HAS_OPENAI:
        print("Error: 'openai' package required. Run: pip install openai")
        sys.exit(1)

    bible_dir = Path(args.bible_dir).expanduser().resolve()
    profile = load_profile(args.name, bible_dir)

    api_key = args.api_key or os.environ.get("ARK_API_KEY", "")
    if not api_key:
        print("Error: Set ARK_API_KEY env var or pass --api-key")
        sys.exit(1)

    # Determine views and expressions
    if args.all:
        views = ["front", "three-quarter", "side", "back"]
    elif args.views:
        views = args.views
    else:
        views = ["front"]

    if args.all:
        expressions = ["neutral", "happy", "angry", "sad", "surprised", "thinking"]
    elif args.expressions:
        expressions = args.expressions
    else:
        expressions = ["neutral"]

    outfit_key = args.outfit or "default"

    # Setup output dir
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else bible_dir
    char_dir = output_dir / f"{slugify(args.name)}_renders"
    char_dir.mkdir(parents=True, exist_ok=True)

    sizes = {"1K": "1024x1024", "2K": "2048x2048", "4K": "4096x4096"}
    size = sizes.get(args.size, "2048x2048") if args.size in sizes else args.size

    style = profile.get("style_keywords", STYLE_PRESETS.get(args.style or "manhua", ""))
    profile["style_keywords"] = style

    client = OpenAI(base_url=SEEDREAM_BASE_URL, api_key=api_key)

    print(f"\n{'='*50}")
    print(f"Rendering: {profile['name'].replace('_', ' ').title()}")
    print(f"Model: {SEEDREAM_MODEL}  Size: {size}")
    print(f"Views: {', '.join(views)}  Expressions: {', '.join(expressions)}")
    print(f"Output: {char_dir}")
    print(f"{'='*50}\n")

    saved = []
    for view in views:
        for expr in expressions:
            prompt = build_prompt(profile, view, expr, outfit_key, args.prompt_style)
            view_short = view[:4]
            expr_short = expr[:6]
            filename = f"{view_short}_{expr_short}.png"

            print(f"  [{view} / {expr}] Sending...", end=" ", flush=True)

            try:
                resp = client.images.generate(
                    model=SEEDREAM_MODEL,
                    prompt=prompt,
                    size=size,
                    n=1,
                    response_format="b64_json",
                )
                img_data = base64.b64decode(resp.data[0].b64_json)
                out_path = char_dir / filename
                with open(out_path, "wb") as f:
                    f.write(img_data)
                saved.append(str(out_path))
                print(f"OK -> {out_path.name}")
            except Exception as e:
                print(f"FAILED: {e}")

    print(f"\n{'='*50}")
    print(f"Done. {len(saved)}/{len(views)*len(expressions)} images saved to:")
    print(f"  {char_dir}")
    print(f"{'='*50}")


def cmd_list(args):
    bible_dir = Path(args.bible_dir).expanduser().resolve()
    if not bible_dir.exists():
        print(f"No character bible found at: {bible_dir}")
        return
    files = sorted(bible_dir.glob("*.json"))
    if not files:
        print(f"No characters found in: {bible_dir}")
        return
    print(f"\nCharacters in {bible_dir} ({len(files)}):")
    print("-" * 60)
    for f in files:
        try:
            with open(f, "r", encoding="utf-8") as fh:
                profile = json.load(fh)
            name = profile.get("name", f.stem)
            outfits = len(profile.get("outfits", {}))
            anchor = profile.get("description_anchor", "")[:60]
            print(f"  {name:20s}  {outfits} outfit(s)  {anchor}...")
        except Exception:
            print(f"  {f.stem:20s}  (invalid)")


def main():
    parser = argparse.ArgumentParser(
        description="Character Lituli Prompt Generator - Gemini-optimized English prompts for character standing illustrations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a character
  python character_lituli.py create -b ./characters -n maya_chen

  # Generate prompts
  python character_lituli.py generate -b ./characters -n maya_chen --views front

  # List all characters
  python character_lituli.py list -b ./characters
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --bible-dir shared across all subcommands
    def add_bible_arg(p):
        p.add_argument("--bible-dir", "-b", default=str(DEFAULT_BIBLE_DIR),
                       help=f"Character bible directory (default: {DEFAULT_BIBLE_DIR})")

    # create
    p_create = subparsers.add_parser("create", help="Create a new character profile")
    add_bible_arg(p_create)
    p_create.add_argument("--name", "-n", required=True, help="Character name (e.g. maya_chen)")
    p_create.add_argument("--description", help="Character description anchor text")
    p_create.add_argument("--style", "-s", choices=list(STYLE_PRESETS.keys()), help="Art style preset")
    p_create.add_argument("--outfit-default", help="Default outfit description")
    p_create.add_argument("--colors", help="Color palette as key=value pairs, comma-separated")

    # generate
    p_gen = subparsers.add_parser("generate", help="Generate lituli prompts from a character profile")
    add_bible_arg(p_gen)
    p_gen.add_argument("--name", "-n", required=True, help="Character name")
    p_gen.add_argument("--views", "-v", nargs="+", choices=list(VIEW_PROMPTS.keys()), help="Views to generate")
    p_gen.add_argument("--expressions", "-e", nargs="+", choices=list(EXPRESSION_PROMPTS.keys()), help="Expressions to generate")
    p_gen.add_argument("--outfit", "-o", help="Outfit key from character profile")
    p_gen.add_argument("--style", "-s", choices=list(STYLE_PRESETS.keys()), help="Override art style")
    p_gen.add_argument("--output", help="Save prompts to file (markdown)")
    p_gen.add_argument("--all", action="store_true", help="Generate all views + 6 basic expressions")

    # show
    p_show = subparsers.add_parser("show", help="Display a character profile")
    add_bible_arg(p_show)
    p_show.add_argument("--name", "-n", required=True, help="Character name")

    # list
    p_list = subparsers.add_parser("list", help="List all saved characters")
    add_bible_arg(p_list)

    # render
    p_render = subparsers.add_parser("render", help="Generate images via Doubao Seedream API")
    add_bible_arg(p_render)
    p_render.add_argument("--name", "-n", required=True, help="Character name")
    p_render.add_argument("--api-key", help="ARK API key (or set ARK_API_KEY env var)")
    p_render.add_argument("--views", "-v", nargs="+", choices=list(VIEW_PROMPTS.keys()), help="Views to render")
    p_render.add_argument("--expressions", "-e", nargs="+", choices=list(EXPRESSION_PROMPTS.keys()), help="Expressions to render")
    p_render.add_argument("--outfit", "-o", help="Outfit key")
    p_render.add_argument("--style", "-s", choices=list(STYLE_PRESETS.keys()), help="Override art style")
    p_render.add_argument("--size", default="2K", help="Image size: 1K, 2K, 4K, or WxH (default: 2K)")
    p_render.add_argument("--output-dir", help="Output directory for rendered images")
    p_render.add_argument("--all", action="store_true", help="Render all views + 6 basic expressions")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "create":
            cmd_create(args)
        elif args.command == "generate":
            cmd_generate(args)
        elif args.command == "show":
            cmd_show(args)
        elif args.command == "list":
            cmd_list(args)
        elif args.command == "render":
            cmd_render(args)
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
