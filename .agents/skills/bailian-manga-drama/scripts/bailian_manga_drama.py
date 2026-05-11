#!/usr/bin/env python3
"""
百炼漫剧生成器 - 基于 DashScope 通义万相 Wan 的漫画风格短剧生成工具
支持图生视频，以主角图片为基础生成漫剧分镜
"""

import os
import sys
import json
import argparse
import time
import base64
import requests
from pathlib import Path
from typing import List, Dict, Optional


# 默认配置
DEFAULT_MODEL = "wanx2.1-i2v-turbo"  # 图生视频模型
DEFAULT_SIZE = "720*1280"  # 竖屏 9:16
DEFAULT_DURATION = 10  # 每分镜10秒，3分镜=30秒
MAX_POLL_RETRIES = 120  # 最多轮询120次（每次5秒，共10分钟）

# 漫剧风格预设
MANGA_STYLE_PROMPT = "漫画风格，手绘质感，柔和的色彩过渡，线条清晰，日式或国漫风格，温馨治愈，电影级构图，高细节"

# 漫剧分镜模板
DRAMA_TEMPLATES = {
    "introduction": {
        "name": "主角登场",
        "description": "介绍主角，展示角色特征",
        "default_prompt": "{character}站在画面中央，微笑看向镜头，背景是柔和的光晕，漫画风格，温馨氛围，{style}"
    },
    "action": {
        "name": "动作场景",
        "description": "主角进行某个动作",
        "default_prompt": "{character}正在{action}，表情生动，动作流畅，漫画风格，{style}"
    },
    "emotion": {
        "name": "情感表达",
        "description": "表达某种情感",
        "default_prompt": "{character}露出{emotion}的表情，眼神传达情感，漫画风格，{style}"
    },
    "interaction": {
        "name": "互动场景",
        "description": "与环境或其他元素互动",
        "default_prompt": "{character}与{object}互动，场景温馨，漫画风格，{style}"
    },
    "ending": {
        "name": "结尾定格",
        "description": "漫剧结尾，定格画面",
        "default_prompt": "{character}的定格画面，{ending_scene}，漫画风格，温馨治愈，{style}"
    }
}


def get_api_key() -> str:
    """获取 DashScope API Key"""
    api_key = os.environ.get("DASHSCOPE_API_KEY", "")
    if not api_key:
        print("❌ 错误: 请设置 DASHSCOPE_API_KEY 环境变量")
        print("   export DASHSCOPE_API_KEY='your-api-key'")
        print("   获取地址: https://bailian.console.aliyun.com")
        sys.exit(1)
    return api_key


def image_to_base64(image_path: str) -> str:
    """将图片转为base64"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def analyze_image(image_path: str) -> str:
    """分析图片，提取角色特征描述"""
    filename = Path(image_path).stem
    return f"图片中的主角（基于文件名: {filename}）"


def submit_video_task(
    api_key: str,
    model: str,
    prompt: str,
    image_path: str,
    duration: int = DEFAULT_DURATION,
    size: str = DEFAULT_SIZE,
    seed: Optional[int] = None
) -> str:
    """
    提交图生视频任务到 DashScope

    Returns:
        task_id
    """
    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "enable"
    }

    # 读取图片并转为base64
    image_base64 = image_to_base64(image_path)
    ext = Path(image_path).suffix.lower().lstrip(".")
    mime_type = "png" if ext == "png" else "jpeg"

    body = {
        "model": model,
        "input": {
            "prompt": prompt,
            "img_url": f"data:image/{mime_type};base64,{image_base64}"
        },
        "parameters": {
            "duration": duration,
            "size": size
        }
    }

    if seed is not None:
        body["parameters"]["seed"] = seed

    resp = requests.post(url, headers=headers, json=body, timeout=30)
    data = resp.json()

    if resp.status_code != 200:
        raise Exception(f"API 请求失败: {data}")

    task_id = data.get("output", {}).get("task_id", "")
    if not task_id:
        raise Exception(f"未获取到 task_id: {data}")

    return task_id


def poll_video_task(api_key: str, task_id: str) -> dict:
    """
    轮询视频生成任务状态

    Returns:
        包含 video_url 的字典
    """
    url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"

    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    for i in range(MAX_POLL_RETRIES):
        resp = requests.get(url, headers=headers, timeout=30)
        data = resp.json()

        status = data.get("output", {}).get("task_status", "")

        if status == "SUCCEEDED":
            video_url = data.get("output", {}).get("video_url", "")
            return {"status": "SUCCEEDED", "video_url": video_url}
        elif status == "FAILED":
            message = data.get("output", {}).get("message", "未知错误")
            return {"status": "FAILED", "message": message}
        else:
            print(f"   [{i+1}/{MAX_POLL_RETRIES}] 状态: {status}，等待中...", end="\r", flush=True)
            time.sleep(5)

    return {"status": "TIMEOUT", "message": "任务超时"}


def download_video(video_url: str, output_path: str):
    """下载视频文件"""
    print(f"\n📥 下载视频...")
    resp = requests.get(video_url, timeout=120)
    with open(output_path, "wb") as f:
        f.write(resp.content)
    print(f"✅ 下载完成: {output_path}")


def generate_scene_prompt(
    template_key: str,
    character_desc: str,
    style: str = MANGA_STYLE_PROMPT,
    **kwargs
) -> str:
    """根据模板生成分镜提示词"""
    template = DRAMA_TEMPLATES.get(template_key, DRAMA_TEMPLATES["introduction"])
    prompt = template["default_prompt"].format(
        character=character_desc,
        style=style,
        **kwargs
    )
    return prompt


def create_drama_script(
    title: str,
    character_desc: str,
    scenes: List[Dict],
    output_file: str = None
) -> str:
    """创建漫剧脚本"""
    script = {
        "title": title,
        "character": character_desc,
        "style": "漫画风格",
        "total_scenes": len(scenes),
        "scenes": []
    }

    for i, scene in enumerate(scenes, 1):
        scene_data = {
            "scene_number": i,
            "type": scene.get("type", "introduction"),
            "name": DRAMA_TEMPLATES.get(scene.get("type", "introduction"), {}).get("name", "自定义场景"),
            "prompt": scene.get("prompt", ""),
            "duration": scene.get("duration", DEFAULT_DURATION),
            "size": scene.get("size", DEFAULT_SIZE)
        }
        script["scenes"].append(scene_data)

    script_json = json.dumps(script, indent=2, ensure_ascii=False)

    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(script_json)
        print(f"✅ 脚本已保存: {output_file}")

    return script_json


def generate_scene_video(
    scene: Dict,
    character_image: str,
    api_key: str,
    output_dir: str
) -> str:
    """生成分镜视频"""
    print(f"\n🎬 生成分镜 {scene['scene_number']}: {scene['name']}")
    print(f"📝 提示词: {scene['prompt'][:80]}...")

    task_id = submit_video_task(
        api_key=api_key,
        model=DEFAULT_MODEL,
        prompt=scene['prompt'],
        image_path=character_image,
        duration=scene.get('duration', DEFAULT_DURATION),
        size=scene.get('size', DEFAULT_SIZE)
    )
    print(f"✅ 任务已提交: {task_id}")

    result = poll_video_task(api_key, task_id)

    if result["status"] != "SUCCEEDED":
        raise Exception(f"视频生成失败: {result.get('message', '未知错误')}")

    # 下载视频
    output_file = Path(output_dir) / f"scene_{scene['scene_number']}_{scene['type']}.mp4"
    download_video(result["video_url"], str(output_file))

    return str(output_file)


def generate_drama(
    script_file: str,
    character_image: str,
    output_dir: str = "~/Desktop"
) -> List[str]:
    """根据脚本生成完整漫剧"""
    api_key = get_api_key()

    with open(script_file, 'r', encoding='utf-8') as f:
        script = json.load(f)

    print(f"\n{'='*60}")
    print(f"🎭 开始生成漫剧: {script['title']}")
    print(f"{'='*60}")
    print(f"👤 主角: {script['character']}")
    print(f"📊 分镜数: {script['total_scenes']}")
    print(f"🎨 风格: {script['style']}")
    print()

    output_path = Path(output_dir).expanduser()
    drama_dir = output_path / f"drama_{script['title'].replace(' ', '_')}"
    drama_dir.mkdir(parents=True, exist_ok=True)

    video_files = []
    for scene in script['scenes']:
        try:
            video_path = generate_scene_video(
                scene=scene,
                character_image=character_image,
                api_key=api_key,
                output_dir=str(drama_dir)
            )
            video_files.append(video_path)
        except Exception as e:
            print(f"❌ 分镜 {scene['scene_number']} 生成失败: {e}")

    print(f"\n{'='*60}")
    print(f"✅ 漫剧生成完成!")
    print(f"📁 输出目录: {drama_dir}")
    print(f"🎬 生成视频: {len(video_files)} 个")
    print(f"{'='*60}")

    return video_files


def quick_generate(
    character_image: str,
    theme: str,
    num_scenes: int = 3,
    output_dir: str = "~/Desktop"
) -> List[str]:
    """快速生成漫剧 - 自动创建脚本并生成"""
    api_key = get_api_key()

    print("🔍 分析主角图片...")
    character_desc = analyze_image(character_image)
    print(f"👤 主角特征: {character_desc}")
    print()

    scenes = []
    scene_types = ["introduction", "action", "emotion", "interaction", "ending"]

    for i in range(min(num_scenes, len(scene_types))):
        scene_type = scene_types[i]

        if scene_type == "introduction":
            prompt = generate_scene_prompt(
                "introduction", character_desc
            )
        elif scene_type == "action":
            prompt = generate_scene_prompt(
                "action", character_desc,
                action="进行日常活动"
            )
        elif scene_type == "emotion":
            prompt = generate_scene_prompt(
                "emotion", character_desc,
                emotion="开心"
            )
        elif scene_type == "interaction":
            prompt = generate_scene_prompt(
                "interaction", character_desc,
                object="周围的环境"
            )
        else:
            prompt = generate_scene_prompt(
                "ending", character_desc,
                ending_scene="温馨的结尾"
            )

        prompt = f"{theme}主题，{prompt}"

        scenes.append({
            "type": scene_type,
            "prompt": prompt,
            "duration": DEFAULT_DURATION,
            "size": DEFAULT_SIZE
        })

    output_path = Path(output_dir).expanduser()
    output_path.mkdir(parents=True, exist_ok=True)
    script_file = output_path / f"drama_script_{int(time.time())}.json"
    create_drama_script(
        title=f"漫剧-{theme}",
        character_desc=character_desc,
        scenes=scenes,
        output_file=str(script_file)
    )

    return generate_drama(
        script_file=str(script_file),
        character_image=character_image,
        output_dir=output_dir
    )


def main():
    parser = argparse.ArgumentParser(
        description="百炼漫剧生成器 - 基于 DashScope 通义万相 Wan 的漫画风格短剧生成工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 快速生成漫剧
  python3 bailian_manga_drama.py generate --image character.png --theme "校园日常"

  # 根据脚本生成漫剧
  python3 bailian_manga_drama.py from-script --script drama_script.json --image character.png

  # 创建脚本模板
  python3 bailian_manga_drama.py create-script --output my_drama.json
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    p_generate = subparsers.add_parser("generate", help="快速生成漫剧")
    p_generate.add_argument("--image", "-i", required=True, help="主角图片路径")
    p_generate.add_argument("--theme", "-t", required=True, help="漫剧主题/剧情")
    p_generate.add_argument("--scenes", "-n", type=int, default=3, help="分镜数量（默认3）")
    p_generate.add_argument("--output", "-o", default="~/Desktop", help="输出目录")

    p_from_script = subparsers.add_parser("from-script", help="根据脚本生成漫剧")
    p_from_script.add_argument("--script", "-s", required=True, help="脚本文件路径")
    p_from_script.add_argument("--image", "-i", required=True, help="主角图片路径")
    p_from_script.add_argument("--output", "-o", default="~/Desktop", help="输出目录")

    p_create = subparsers.add_parser("create-script", help="创建脚本模板")
    p_create.add_argument("--output", "-o", required=True, help="输出脚本文件路径")
    p_create.add_argument("--title", default="我的漫剧", help="漫剧标题")
    p_create.add_argument("--character", default="可爱的主角", help="主角描述")
    p_create.add_argument("--num-scenes", type=int, default=3, help="分镜数量")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "generate":
            video_files = quick_generate(
                character_image=args.image,
                theme=args.theme,
                num_scenes=args.scenes,
                output_dir=args.output
            )
            print(f"\n🎉 漫剧生成完成! 共 {len(video_files)} 个视频")
            for i, vf in enumerate(video_files, 1):
                print(f"   分镜{i}: {vf}")

        elif args.command == "from-script":
            video_files = generate_drama(
                script_file=args.script,
                character_image=args.image,
                output_dir=args.output
            )
            print(f"\n🎉 漫剧生成完成! 共 {len(video_files)} 个视频")

        elif args.command == "create-script":
            scenes = []
            for i in range(args.num_scenes):
                scene_type = ["introduction", "action", "emotion", "interaction", "ending"][i % 5]
                scenes.append({
                    "type": scene_type,
                    "prompt": f"请修改此分镜{i+1}的提示词",
                    "duration": DEFAULT_DURATION
                })

            create_drama_script(
                title=args.title,
                character_desc=args.character,
                scenes=scenes,
                output_file=args.output
            )
            print(f"\n✅ 脚本模板已创建: {args.output}")
            print("📝 请编辑脚本文件，修改分镜提示词后使用 from-script 命令生成漫剧")

    except Exception as e:
        print(f"\n❌ 错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()