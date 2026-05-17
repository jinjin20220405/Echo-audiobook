# Echo-audiobook 项目架构设计文档

## 一、项目定位

**一句话定义**：一个把"问答录/对话录/访谈录"类电子书自动拆分角色、配置多音色、生成有声书的本地开源工具。

**目标用户**：想给灵性书、访谈录、对话集做有声书的中文读者；具备基础电脑操作能力,能跟着 README 一步步装环境。

**非目标**：不做小说（角色太多太动态）；不做 pdf（解析坑太多）；不做在线服务（不维护服务器）。

---

## 二、技术栈选型

| 层 | 技术 | 原因 |
|---|---|---|
| 编程语言 | Python 3.10+ | 你已装 3.13.2,AI/TTS 生态最全 |
| Web UI | **Gradio** 4.x | 小白友好,几十行代码出网页,自带组件 |
| AI 接口 | OpenAI 兼容 SDK | DeepSeek / 智谱 / Kimi 都兼容 OpenAI 格式,一套代码切换不同供应商 |
| epub 解析（二期） | ebooklib | 行业事实标准 |
| TTS - 免费云端 | edge-tts（Python 库） | 微软 Edge 的免费接口,零配置 |
| TTS - 商用云端 | 阿里云 / 火山引擎 SDK | 国内访问稳定、声音库丰富 |
| TTS - 本地开源 | GPT-SoVITS（外部部署） | 通过 API 调用,不嵌入本项目 |
| 音频处理 | pydub + ffmpeg | 拼接、转换、生成 M4B |
| 配置存储 | YAML 文件 | 比 JSON 适合人手编辑 |
| 项目状态持久化 | SQLite | 单文件数据库,零运维 |

---

## 三、目录结构

```
H:\Ai-project\Echo-audiobook\
├── README.md                   # 项目说明（中文）
├── LICENSE                     # MIT 协议
├── requirements.txt            # Python 依赖
├── .gitignore                  # Git 忽略规则
├── CLAUDE.md                   # 给 Claude Code 的项目说明
├── config\
│   ├── default.yaml            # 默认配置（AI 模型、TTS 引擎选择等）
│   └── voices.yaml             # 三角色的默认音色配置
├── data\
│   ├── books\                  # 用户导入的原始 txt 文件
│   ├── scripts\                # AI 拆分后的 JSON 脚本（含角色标记）
│   ├── audio\                  # 生成的章节 mp3
│   ├── output\                 # 最终的 M4B 和打包 zip
│   └── echo.db                 # SQLite 数据库（任务状态、用户校对记录）
├── src\
│   ├── __init__.py
│   ├── app.py                  # Gradio 主程序入口
│   ├── parser\                 # 模块1：文本解析
│   │   ├── __init__.py
│   │   ├── txt_parser.py       # txt 文件读取、清洗
│   │   └── chapter_splitter.py # 章节切分
│   ├── splitter\               # 模块2：AI 角色拆分（核心）
│   │   ├── __init__.py
│   │   ├── llm_client.py       # 统一 LLM 调用接口（DeepSeek/GLM/Kimi 切换）
│   │   ├── role_splitter.py    # 角色拆分主逻辑
│   │   └── prompts.py          # 提示词模板
│   ├── editor\                 # 模块3：网页校对界面
│   │   ├── __init__.py
│   │   ├── chapter_view.py     # 分章校对页面
│   │   └── batch_ops.py        # 批量操作（框选、关键词批量改）
│   ├── tts\                    # 模块4：语音合成
│   │   ├── __init__.py
│   │   ├── base.py             # TTS 引擎抽象基类
│   │   ├── edge_tts_engine.py  # Edge-TTS 实现
│   │   ├── aliyun_engine.py    # 阿里云实现
│   │   ├── gptsovits_engine.py # GPT-SoVITS 实现
│   │   └── factory.py          # 引擎工厂（根据配置选用）
│   ├── audio\                  # 模块5：音频处理
│   │   ├── __init__.py
│   │   ├── merger.py           # 章节内片段拼接
│   │   └── m4b_packer.py       # 生成 M4B
│   ├── db\                     # 数据持久化
│   │   ├── __init__.py
│   │   ├── schema.py           # SQLite 表结构
│   │   └── repository.py       # 数据读写
│   └── utils\
│       ├── __init__.py
│       ├── config_loader.py    # 读 YAML
│       └── logger.py           # 日志
├── tests\                      # 单元测试
│   ├── test_parser.py
│   ├── test_splitter.py
│   └── fixtures\
│       └── sample_qa.txt       # 附件那段文本作为测试素材
└── docs\
    ├── ARCHITECTURE.md         # 本文档
    ├── DEVELOPMENT.md          # 开发路线图
    └── USAGE.md                # 用户使用手册
```

---

## 四、五个核心模块的职责

### 模块1：parser（文本解析）
- **输入**：用户上传的 .txt 文件
- **输出**：标准化的"章节列表"（每章包含：章节号、标题、原始文本）
- **关键工作**：去除多余空行、识别章节标题（"1、'我是'之意识"这种格式）、按章切分
- **复杂度**：低。正则表达式就够了,不用 AI

### 模块2：splitter（AI 角色拆分） ★项目核心
- **输入**：单个章节的原始文本
- **输出**：JSON 格式的"脚本",每一段标记好角色

```json
[
  {"role": "narrator", "text": "1、'我是'之意识"},
  {"role": "questioner", "text": "每天早晨醒来时都会有这样的体验……"},
  {"role": "maharaj", "text": "在任何东西出现之前……"}
]
```

- **关键工作**：调用 DeepSeek/GLM 分析每一段属于谁。提示词里要明确告诉 AI："文本中带'问：'前缀的是 questioner,带'马：'前缀的是 maharaj,其他叙述性段落是 narrator"
- **容错**：AI 偶尔会犯错,所以模块3的人工校对必须存在

### 模块3：editor（网页校对）
- **输入**：拆分后的脚本 JSON
- **输出**：用户修正过的脚本 JSON
- **关键工作**：用 Gradio 渲染一个表格——每章一个 tab,每段一行,左边显示文本,右边是角色下拉框。提供"框选多行批量改"、"按关键词批量改"两个批量操作按钮
- **保存**：用户每次修改自动写入 SQLite,支持中途关闭网页后下次接着改

### 模块4：tts（语音合成）
- **输入**：校对后的脚本 JSON + 三角色的音色配置
- **输出**：每一段一个 .wav/.mp3 小片段
- **关键工作**：根据用户选的 TTS 引擎（Edge / 阿里云 / GPT-SoVITS）,把每段文本转成音频。三个角色各自的音色参数从 voices.yaml 读
- **抽象设计**：base.py 定义一个 `TTSEngine` 抽象类,三个具体引擎各自继承实现 `synthesize(text, voice_config)` 方法,factory.py 根据配置返回对应实例。这样将来加新引擎（比如 ChatTTS、CosyVoice）只用新增一个文件,主流程不动

### 模块5：audio（音频后处理）
- **输入**：模块4生成的一堆小片段
- **输出**：每章一个 mp3 + 整本一个 M4B
- **关键工作**：用 pydub 拼接章节内的所有片段（中间加适当停顿——叙述者→问者切换时停顿短,问→答切换时停顿长,给一种对话呼吸感）；用 ffmpeg 把所有章节合成带章节标记的 M4B

---

## 五、依赖列表（requirements.txt 草案）

```
# Web UI
gradio>=4.0.0

# AI 调用
openai>=1.0.0          # DeepSeek/GLM/Kimi 都兼容这个 SDK
pyyaml>=6.0            # 读配置

# TTS
edge-tts>=6.1.0        # 免费云端

# 音频处理
pydub>=0.25.1
# ffmpeg 不是 Python 库,是系统级依赖,README 里要单独说明怎么装

# 开发工具
pytest>=7.0            # 测试
python-dotenv>=1.0     # API key 管理
```

**系统级依赖（不在 pip 里）**：
- ffmpeg（必装,pydub 和 M4B 生成都要用）
- Git（克隆仓库用）

---

## 六、开发路线图（七个里程碑）

### M1：环境搭建 + 项目骨架（预计 1 天）
- 创建 `H:\Ai-project\Echo-audiobook` 目录
- 初始化 Git 仓库 + .gitignore
- 装依赖、写 requirements.txt
- 建好目录结构（空文件夹 + 占位 README）
- **验收标准**：`python -c "import gradio; print('ok')"` 能跑通

### M2：txt 解析 + 章节切分（预计 1 天）
- 实现 parser 模块
- 用附件那段文本测试
- **验收标准**：把附件 txt 喂进去,输出 3 个章节,每章内容正确

### M3：AI 角色拆分 MVP（预计 2-3 天,最容易卡的环节）
- 申请 DeepSeek API key（很便宜,注册送额度）
- 实现 splitter 模块,写好提示词
- 用 M2 输出的章节测试
- **验收标准**：输入"2、对身体的执着",AI 输出的 JSON 中 95% 以上的角色标记正确

### M4：Gradio 校对界面（预计 2-3 天）
- 实现 editor 模块
- 分章 tab + 表格 + 下拉框 + 批量操作按钮
- 修改自动存 SQLite
- **验收标准**：网页上能看到拆分结果,能改,能保存,关掉重开数据还在

### M5：单 TTS 引擎打通（预计 1-2 天）
- 先只接 Edge-TTS（零配置、免费）
- 验证三角色用三个不同音色能正常出声
- **验收标准**：把"3、当下"这章生成出 mp3,三个角色声音明显不同

### M6：音频拼接 + M4B 打包（预计 1-2 天）
- 实现 audio 模块
- 章节内拼接 + 停顿插入 + M4B 生成
- **验收标准**：生成的 M4B 在苹果 Books 或 VLC 中能看到章节目录

### M7：补全 TTS 混合模式（预计 2-3 天）
- 添加阿里云引擎实现
- 添加 GPT-SoVITS 引擎实现（通过 HTTP 调用外部部署）
- 配置页加 TTS 引擎切换下拉框
- **验收标准**：在网页上切换三种 TTS 引擎,都能正常出声

**总工期估算**：10-15 个工作日（小白学习成本算在内的话,可能要 3-4 周）。

---

## 七、为 Claude Code orchestrator-worker 设计的接口

- **Claude Code（planner）**：读取本架构文档,按里程碑拆任务,给每个任务出详细 spec
- **Copilot CLI（worker）**：执行具体的"写函数、写测试、跑测试"工作
- **你（开发者）**：负责"卡壳时和 Claude 讨论"、"看 PR 决定 merge 不 merge"、"测试 UI"

每个里程碑都建议建一个 Git 分支（如 `feature/m2-parser`）,完成后合并主分支,这样出问题能回滚。

---

## 八、风险与坑（提前预警）

1. **AI 拆分准确率低于预期**：M3 里如果 DeepSeek 拆得乱七八糟,先调提示词(在 prompts.py 里加 few-shot 示例),还不行就升级到 Claude Haiku。
2. **Edge-TTS 中文音色僵硬**：可能不够"灵性书"该有的味道,M7 阶段如果用户反馈强烈,再优先做 GPT-SoVITS。
3. **ffmpeg 安装是 Windows 用户最大的坑**：README 必须写得手把手,最好附一个 winget 或者 scoop 的一键命令。
4. **Gradio 4.x 的 API 变动**：相比 3.x 有破坏性变化,找教程时注意版本。
5. **API key 管理**：用 .env 文件存,.gitignore 必须排除掉,别手滑提交到 GitHub。
