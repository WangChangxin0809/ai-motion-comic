---
name: bailian-manga-drama
description: 百炼漫剧生成器 - 基于阿里云百炼通义万相Wan的漫画风格短剧生成工具。支持以主角图片为基础，自动生成漫剧分镜脚本并生成视频。使用DASHSCOPE_API_KEY。适用于创作漫画风格的短视频、角色故事、动画短片等。
---

# 百炼漫剧生成器

基于阿里云百炼 DashScope **通义万相 Wan** 视频生成能力，专门用于创作**漫画风格的短剧**（漫剧）。

## 核心功能

- **主角识别**：分析提供的角色图片，提取角色特征
- **自动分镜**：根据主题自动生成漫剧分镜脚本（通过 LLM）
- **图生视频**：以主角图片为基础生成各分镜视频
- **漫画风格**：内置漫画风格提示词模板
- **分镜管理**：支持自定义分镜脚本

## 前置要求

1. 安装依赖：
```bash
pip install requests
```

2. 设置 `DASHSCOPE_API_KEY` 环境变量：
```bash
export DASHSCOPE_API_KEY="your-api-key"
```

在[阿里云百炼控制台](https://bailian.console.aliyun.com)获取 API Key。

---

## 使用方法

### 1. 快速生成漫剧（推荐）

提供主角图片和主题，自动生成完整漫剧：

```bash
cd .agents/skills/bailian-manga-drama
python3 scripts/bailian_manga_drama.py generate \
  --image /path/to/character.png \
  --theme "校园日常" \
  --scenes 3
```

### 2. 根据脚本生成漫剧

先创建脚本，再生成视频：

```bash
# 创建脚本模板
python3 scripts/bailian_manga_drama.py create-script \
  --output my_drama.json \
  --title "我的漫剧" \
  --character "双马尾女孩" \
  --num-scenes 4

# 编辑脚本文件后生成
python3 scripts/bailian_manga_drama.py from-script \
  --script my_drama.json \
  --image /path/to/character.png
```

## 分镜模板

内置5种漫剧分镜类型：

| 分镜类型 | 名称 | 说明 |
|---------|------|------|
| introduction | 主角登场 | 介绍主角，展示角色特征 |
| action | 动作场景 | 主角进行某个动作 |
| emotion | 情感表达 | 表达某种情感 |
| interaction | 互动场景 | 与环境或其他元素互动 |
| ending | 结尾定格 | 漫剧结尾，定格画面 |

## 脚本格式

```json
{
  "title": "漫剧标题",
  "character": "主角描述",
  "style": "漫画风格",
  "total_scenes": 3,
  "scenes": [
    {
      "scene_number": 1,
      "type": "introduction",
      "name": "主角登场",
      "prompt": "双马尾女孩站在画面中央，微笑看向镜头，漫画风格...",
      "duration": 10,
      "size": "720*1280"
    }
  ]
}
```

## 参数说明

### generate 命令

| 参数 | 必需 | 说明 |
|------|------|------|
| `--image` | ✅ | 主角图片路径 |
| `--theme` | ✅ | 漫剧主题/剧情描述 |
| `--scenes` | ❌ | 分镜数量（默认3） |
| `--output` | ❌ | 输出目录（默认~/Desktop） |

### from-script 命令

| 参数 | 必需 | 说明 |
|------|------|------|
| `--script` | ✅ | 脚本文件路径 |
| `--image` | ✅ | 主角图片路径 |

### create-script 命令

| 参数 | 必需 | 说明 |
|------|------|------|
| `--output` | ✅ | 输出脚本文件路径 |
| `--title` | ❌ | 漫剧标题 |
| `--character` | ❌ | 主角描述 |
| `--num-scenes` | ❌ | 分镜数量 |

## 使用示例

### 示例 1：生成校园日常漫剧

```bash
python3 scripts/bailian_manga_drama.py generate \
  --image ~/Desktop/girl_character.png \
  --theme "校园日常" \
  --scenes 3
```

### 示例 2：创建自定义漫剧

```bash
python3 scripts/bailian_manga_drama.py create-script \
  --output spring_festival.json \
  --title "春节团圆" \
  --character "白发奶奶" \
  --num-scenes 5

# 编辑 spring_festival.json 后生成
python3 scripts/bailian_manga_drama.py from-script \
  --script spring_festival.json \
  --image ~/Desktop/grandma.png
```

## 视频规格

- **默认比例**：9:16 竖屏（size: 720*1280）
- **默认时长**：每分镜10秒（3分镜=30秒）
- **模型**：wanx2.1-i2v-turbo（图生视频，单次最长10秒）
- **风格**：漫画/手绘风格

## 输出结构

```
~/Desktop/drama_我的漫剧/
├── drama_script_xxx.json    # 脚本文件
├── scene_1_introduction.mp4 # 分镜1
├── scene_2_action.mp4       # 分镜2
├── scene_3_emotion.mp4      # 分镜3
└── ...
```

## 与 Seedance 版 manga-drama 的区别

- 使用阿里云百炼而不是火山方舟
- API Key 为 `DASHSCOPE_API_KEY` 而不是 `ARK_API_KEY`
- 使用 REST API 直接调用 DashScope 接口
- 不依赖 `env_utils` 等外部模块，完全自包含