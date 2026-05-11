#!/bin/bash
# 批量下载小说章节 - 纯shell+curl实现
# 用法: bash dl_novel.sh

NOVEL_DIR="d:/0_Study/Python_project/ai-motion-comic/novels/天眼风水师"
mkdir -p "$NOVEL_DIR"

echo "=== 第1步: 提取章节URL列表 ==="

# 提取所有唯一章节URL，按HTML文件名排序
grep -o 'href="/biqu96978/[0-9]*\.html"' "d:/0_Study/Python_project/ai-motion-comic/index.html" | \
  sed 's/href="\(.*\)"/\1/' | sort -t/ -k3 -n > "$NOVEL_DIR/urls.txt"

TOTAL=$(wc -l < "$NOVEL_DIR/urls.txt")
echo "共 $TOTAL 个章节"
echo ""

COMBINED="$NOVEL_DIR/天眼风水师_全本.txt"
> "$COMBINED"
COUNT=0

while IFS= read -r path; do
  COUNT=$((COUNT + 1))
  base_num=$(echo "$path" | grep -o '[0-9]\+' | tail -1)

  all_content=""
  title=""
  page=1

  # 下载同一章所有分页
  while true; do
    if [ $page -eq 1 ]; then
      page_url="https://www.22biqu.com${path}"
    else
      page_url="https://www.22biqu.com/biqu96978/${base_num}_${page}.html"
    fi

    html_file="$NOVEL_DIR/.tmp_p${COUNT}_${page}.html"
    curl -s -L -o "$html_file" --connect-timeout 10 \
      -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
      "$page_url"

    if [ $page -eq 1 ]; then
      title=$(grep '<h1 class="title">' "$html_file" | head -1 | sed 's/<[^>]*>//g' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
      echo -n "[$COUNT/$TOTAL] $title"
    else
      echo -n " |p${page}"
    fi

    page_content=$(sed -n '/div class="content" id="content"/,/\/div>/p' "$html_file" | \
      sed '1d;$d' | \
      sed 's/<[^>]*>//g' | \
      sed 's/&nbsp;/ /g' | \
      sed 's/&ldquo;/"/g' | \
      sed 's/&rdquo;/"/g' | \
      sed '/^[[:space:]]*$/d')

    if [ -n "$page_content" ]; then
      all_content="${all_content}${page_content}"
    fi

    # 检查下一页是否同章续页
    next_url=$(grep 'id="next_url"' "$html_file" | head -1 | sed 's/.*href="\([^"]*\)".*/\1/')
    rm -f "$html_file"

    next_page=$(echo "$next_url" | grep -o '_\([0-9]\+\)\.html' | grep -o '[0-9]\+')
    if [ -n "$next_page" ]; then
      page=$((page + 1))
      sleep 1
      continue
    fi
    break
  done

  if [ -z "$title" ]; then
    title="未命名$COUNT"
  fi

  safe_name=$(echo "$title" | sed 's/[\\/*?"<>|:]/_/g')
  ch_file="$NOVEL_DIR/${safe_name}.txt"
  printf '%s\n\n%s\n' "$title" "$all_content" > "$ch_file"

  {
    echo ""
    echo "========================================"
    echo "$title"
    echo "========================================"
    echo ""
    echo "$all_content"
  } >> "$COMBINED"

  chars=$(echo "$all_content" | wc -m)
  echo " (${page}P ${chars}字)"

  sleep 1
done < "$NOVEL_DIR/urls.txt"

# 清理临时文件
rm -f "$NOVEL_DIR/.tmp_p"*.html "$NOVEL_DIR/urls.txt"

echo ""
echo "=== 完成 ==="
echo "📁 目录: $NOVEL_DIR"
echo "📄 合并: $COMBINED"
echo "📊 共: $TOTAL 章"