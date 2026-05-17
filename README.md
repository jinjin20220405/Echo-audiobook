# Echo-audiobook

> 把问答录、对话录、访谈录类电子书自动转成多角色有声书的开源工具。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## 这个项目是干什么的

把一本结构化的电子书——比如灵性问答录、访谈合集、对话录——自动拆分出**叙述者、提问者、回答者**三个角色,再用三种不同的声音读出来,最后输出一本带章节目录的 M4B 有声书。

适合谁用：

- 喜欢听书但想要"对话感"而不是单声播报的读者
- 想给私藏的灵性书、访谈录做有声版的爱好者
- 不想花钱买商业有声书,愿意自己跑工具的极客

不适合谁用：

- 想做小说有声书（角色太多,本项目不支持）
- 想做 PDF 电子书的（一期只支持 txt,二期加 epub）
- 想要"零配置、双击即用"的纯小白（需要装 Python 和 ffmpeg）

## 工作原理

```
txt 电子书 → 章节切分 → AI 角色拆分 → 网页人工校对 → 多音色 TTS → 章节 mp3 + 整本 M4B
```

## 快速开始

> 详细步骤见 [docs/USAGE.md](docs/USAGE.md)

```bash
# 1. 克隆仓库
git clone https://github.com/jinjin20220405/Echo-audiobook.git
cd Echo-audiobook

# 2. 安装依赖
pip install -r requirements.txt

# 3. 装 ffmpeg（Windows）
winget install ffmpeg

# 4. 配置 API key
copy .env.example .env
# 编辑 .env 填入 DeepSeek 的 API key

# 5. 启动
python src/app.py
```

打开浏览器访问 `http://localhost:7860`,上传 txt,跟着引导走完整个流程。

## 三种 TTS 引擎对比

| 引擎 | 成本 | 音质 | 部署难度 | 推荐场景 |
|---|---|---|---|---|
| Edge-TTS | 免费 | 一般 | 零配置 | 快速试用 |
| 阿里云 / 火山引擎 | 按字符计费 | 好 | 申请 key | 追求音质 |
| GPT-SoVITS | 免费 | 极好（可克隆） | 需 GPU + 部署 | 追求极致 + 个性化 |

## 路线图

- [x] M1：环境搭建 + 项目骨架
- [ ] M2：txt 解析 + 章节切分
- [ ] M3：AI 角色拆分（DeepSeek）
- [ ] M4：Gradio 网页校对界面
- [ ] M5：Edge-TTS 单引擎打通
- [ ] M6：音频拼接 + M4B 打包
- [ ] M7：TTS 混合模式（阿里云 + GPT-SoVITS）
- [ ] V2：支持 epub 输入

## 开发

详见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) 和 [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)。

## 许可证

[MIT](LICENSE)

## 致谢

- [Gradio](https://www.gradio.app/) - Web UI 框架
- [edge-tts](https://github.com/rany2/edge-tts) - 免费 TTS
- [DeepSeek](https://www.deepseek.com/) - 主用 LLM
