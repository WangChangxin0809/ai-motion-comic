#!/bin/bash
# 测试版 - 下载前5章（含分页处理）
NOVEL_DIR="d:/0_Study/Python_project/ai-motion-comic/novels/天眼风水师"
mkdir -p "$NOVEL_DIR"

grep -o 'href="/biqu96978/[0-9]*\.html"' "d:/0_Study/Python_project/ai-motion-comic/index.html" | \
  sed 's/href="\(.*\)"/\1/' | sort -t/ -k3 -n | head -5 > "$NOVEL_DIR/urls.txt"

TOTAL=$(wc -l < "$NOVEL_DIR/urls.txt")
echo "共 $TOTAL 章 (测试)"

COMBINED="$NOVEL_DIR/天眼风水师_前5章.txt"
> "$COMBINED"
COUNT=0

while IFS= read -r path; do
  COUNT=$((COUNT + 1))

  # 从path提取base number: 例如 /biqu96978/45523663.html -> 45523663
  base_num=$(echo "$path" | grep -o '[0-9]\+' | tail -1)

  all_content=""
  title=""
  page=1

  # 下载同一章的所有分页
  while true; do
    if [ $page -eq 1 ]; then
      page_url="https://www.22biqu.com${path}"
    else
      page_url="https://www.22biqu.com/biqu96978/${base_num}_${page}.html"
    fi

    html="$NOVEL_DIR/.tmp_p${page}.html"
    curl -s -L -o "$html" --connect-timeout 10 \
      -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
      "$page_url"

    # 第一页时获取标题
    if [ $page -eq 1 ]; then
      title=$(grep '<h1 class="title">' "$html" | head -1 | sed 's/<[^>]*>//g' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
      echo "[$COUNT/$TOTAL] 第1章: $title"
    fi

    # 提取本页正文
    page_content=$(sed -n '/div class="content" id="content"/,/\/div>/p' "$html" | \
      sed '1d;$d' | \
      sed 's/<[^>]*>//g' | \
      sed 's/&nbsp;/ /g' | \
      sed 's/&ldquo;/"/g' | \
      sed 's/&rdquo;/"/g' | \
      sed 's/&hellip;/.../g' | \
      sed 's/&mdash;/--/g' | \
      sed '/^[[:space:]]*$/d')

    if [ -n "$page_content" ]; then
      all_content="${all_content}${page_content}"
    fi

    # 检查下一页
    next_url=$(grep 'id="next_url"' "$html" | head -1 | sed 's/.*href="\([^"]*\)".*/\1/')
    rm -f "$html"

    # 判断下一页是不是同一章的续页
    if [ -z "$next_url" ]; then
      break
    fi

    next_num=$(echo "$next_url" | grep -o '[0-9]\+' | head -1)

    # 如果下一页的基础号 = 当前页的基础号 + 续号模式，则继续
    # 例如: 45523663_2 -> 继续(同一章); 45523664 -> 结束(下一章)
    next_page=$(echo "$next_url" | grep -o '_\([0-9]\+\)\.html' | grep -o '[0-9]\+')
    if [ -n "$next_page" ]; then
      page=$((page + 1))
      echo "  └ 第${page}页: ${page_url}"
      sleep 1
      continue
    fi

    # 下一页没有 _N 后缀 -> 不同章节
    break
  done

  if [ -z "$title" ]; then
    title="未命名$COUNT"
  fi

  # 保存单章
  safe_name=$(echo "$title" | sed 's/[\\/*?"<>|:]/_/g')
  ch_file="$NOVEL_DIR/${safe_name}.txt"
  printf '%s\n\n%s\n' "$title" "$all_content" > "$ch_file"

  # 追加到合并文件
  {
    echo ""
    echo "========================================"
    echo "$title"
    echo "========================================"
    echo ""
    echo "$all_content"
  } >> "$COMBINED"

  chars=$(echo "$all_content" | wc -m)
  echo "  => 共${page}页, ${chars}字"

  sleep 1
done < "$NOVEL_DIR/urls.txt"

rm -f "$NOVEL_DIR/.tmp_p"*.html "$NOVEL_DIR/urls.txt"
echo ""
echo "完成！📁 $NOVEL_DIR"
ls -la "$NOVEL_DIR/"*.txt