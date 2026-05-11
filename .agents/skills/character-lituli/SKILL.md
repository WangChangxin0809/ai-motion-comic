---
name: character-lituli
description: 角色立绘提示词生成器 - 为 Gemini 网页版图像生成优化英文 prompt。支持角色档案管理、多视图/多表情/多服装批量生成立绘 prompt。零 API 依赖，纯提示词工程工具。适用于生成角色立绘、人物参考图、角色设计表等。
---

# Character Lituli (角色立绘)

为 Gemini 网页版图像生成（Imagen/Nano Banana）优化的英文角色立绘 prompt 生成器。

## 核心功能

- **角色档案管理**：创建、查看、管理 JSON 格式的角色设定档案
- **立绘 Prompt 生成**：根据角色档案生成 Gemini 优化的英文 prompt
- **多视图支持**：front / three-quarter / side / back
- **多表情支持**：neutral / happy / angry / sad / surprised / thinking / smug / blushing / serious / laughing
- **风格预设**：anime / manga / manhua / realistic / semi-realistic / cyberpunk / fantasy
- **多服装管理**：每个角色可定义多套服装
- **零 API 依赖**：纯本地运行，手动复制 prompt 到 Gemini 网页

## 使用方法

### 1. 创建角色档案

```bash
cd .agents/skills/character-lituli
python3 scripts/character_lituli.py create --name maya_chen
```

交互式输入角色外观描述，也可跳过交互直接指定：

```bash
python3 scripts/character_lituli.py create --name maya_chen \
  --description "young woman with short red hair, green eyes" \
  --style manga \
  --outfit-default "navy blue bomber jacket over white tee, dark jeans, red sneakers"
```

### 2. 生成立绘 Prompt

```bash
# 正面立绘
python3 scripts/character_lituli.py generate --name maya_chen --views front

# 多视图
python3 scripts/character_lituli.py generate --name maya_chen --views front side back

# 多表情（正面）
python3 scripts/character_lituli.py generate --name maya_chen --expressions neutral happy angry

# 指定服装和风格
python3 scripts/character_lituli.py generate --name maya_chen \
  --views front --outfit formal --style anime

# 生成全部（4视图 + 6基础表情）
python3 scripts/character_lituli.py generate --name maya_chen --all

# 保存到文件
python3 scripts/character_lituli.py generate --name maya_chen --all --output ~/Desktop/maya_prompts.md
```

### 3. 管理角色

```bash
# 列出所有角色
python3 scripts/character_lituli.py list

# 查看角色详情
python3 scripts/character_lituli.py show --name maya_chen
```

## 角色档案格式

角色档案保存在 `~/character_bible/` 目录下：

```json
{
  "name": "maya_chen",
  "description_anchor": "young woman in her mid-twenties with short asymmetric auburn red hair...",
  "color_palette": {
    "skin": "#F5D0A9",
    "hair": "#C0392B",
    "eyes": "#27AE60",
    "primary": "#2C3E50",
    "accent": "#E74C3C"
  },
  "style_keywords": "manga art style, hand-drawn aesthetic...",
  "default_pose": "standing, full body, hands at sides, looking at viewer",
  "outfits": {
    "default": "navy blue bomber jacket over white tee, dark jeans, red sneakers",
    "formal": "..."
  }
}
```

## Prompt 模板

生成的 prompt 结构：

```
[Style keywords]. Full body character standing illustration of
[character description anchor]. [View/pose]. Wearing [outfit].
[Expression]. Clean white background, character reference sheet,
professional concept art, high detail, consistent character design,
sharp focus.
```

## 风格预设

| 预设 | 说明 |
|------|------|
| `anime` | 日式动画风格，赛璐珞上色 |
| `manga` | 日式漫画风格，手绘质感（默认） |
| `manhua` | 国漫风格，半写实渲染 |
| `realistic` | 写实风格 |
| `semi-realistic` | 半写实 |
| `cyberpunk` | 赛博朋克 |
| `fantasy` | 奇幻插画风 |

## Gemini 使用技巧

1. **复制 prompt** — 将生成的英文 prompt 粘贴到 Gemini 输入框
2. **保持锚点一致** — 同一角色使用相同的 `description_anchor`，Gemini 能保持较高的角色一致性
3. **逐张生成** — Gemini 网页版每次生成一张，不能批量
4. **引用之前图片** — 如果想微调某张图，可以上传之前的图片 + 修改后的 prompt
5. **比例建议** — 立绘推荐在 prompt 中明确提到竖版比例，如 "vertical 9:16 portrait orientation"

## 输出结构

```
~/character_bible/
├── maya_chen.json              # 角色档案
└── maya_chen_prompts/          # 生成的 prompt 存档（可选）
    └── prompts_2026-05-11.md
```
