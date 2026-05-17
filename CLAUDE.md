# CLAUDE.md - Echo-audiobook 项目说明

> 这个文件是给 Claude Code 读的项目级 context。Claude Code 启动时会自动读取根目录的 CLAUDE.md,据此理解项目目标、约束、风格。

## 项目身份

- **名称**: Echo-audiobook
- **GitHub**: https://github.com/jinjin20220405/Echo-audiobook
- **协议**: MIT
- **语言**: Python 3.10+ (本地实际为 3.13.2)
- **平台**: Windows 优先（开发者环境）,Mac/Linux 兼容
- **类型**: 纯本地工具（用户克隆代码本地运行）

## 项目目标

把"问答录/对话录/访谈录"类电子书（如《我就是那》）自动拆分成三角色（叙述者/提问者/回答者）有声书。

## 关键决策（不要轻易推翻）

1. **只处理结构化问答类文本**,不做小说
2. **三角色固定**:narrator / questioner / maharaj
   - 注:"maharaj" 是项目第一本书的回答者代号,实际应抽象为 "responder"——这点在 M3 实施时落实
3. **校对方式**:分章 + 批量操作
4. **TTS 混合模式**:Edge-TTS / 阿里云 / GPT-SoVITS 三选一,通过抽象基类切换
5. **输入**:一期只支持 .txt,V2 加 .epub
6. **AI 策略**:全程使用便宜模型（DeepSeek 优先,GLM-4 次选）,通过 OpenAI 兼容 SDK 调用
7. **复用策略**:Gradio 做 UI、edge-tts 库、ebooklib 解析,中间逻辑自写
8. **输出**:章节 mp3 + 整本 M4B

## 目录约定

详见 `docs/ARCHITECTURE.md` 第三节。重点:

- 业务代码全部在 `src/` 下,按模块分目录
- 测试在 `tests/`,固定测试素材在 `tests/fixtures/`
- 用户数据在 `data/`,已加入 .gitignore
- 配置在 `config/`,敏感信息走 .env

## 编码规范

- **风格**:遵循 PEP 8
- **命名**:模块/函数 snake_case,类 PascalCase
- **类型注解**:public 函数必须加 type hints
- **docstring**:public 函数必须写,用中文说清"做什么、入参、出参",不要写废话
- **错误处理**:用户输入相关的错误必须友好提示,不要让 traceback 直接暴露
- **日志**:用 logging 模块,不用 print

## 测试要求

- 每个模块的核心函数必须有 pytest 单元测试
- 测试素材统一放在 `tests/fixtures/`,《我就是那》节选作为标准测试样本
- 跑测试:`pytest tests/ -v`

## Git 工作流

- 主分支:`main`
- 每个里程碑(M1-M7)在独立分支开发:`feature/m1-skeleton`、`feature/m2-parser`...
- commit message 用中文,格式:`[M2] 实现章节切分逻辑`

## 与开发者协作的风格偏好

- 开发者(老金)是律师,有技术好奇心但非专业程序员
- 解释代码时,**优先讲"为什么这么写",不要只贴代码**
- 遇到选择题时,**列出选项 + 各自取舍**,让开发者选,不要替他做决定
- 避免冗长的过度解释,但关键技术点(API 调用错误、依赖冲突)要讲清楚

## 当前阶段

**M1: 环境搭建 + 项目骨架**

完成标准:
- [x] 目录结构建好
- [x] requirements.txt / README / LICENSE / .gitignore 就位
- [ ] 在 H:\Ai-project\Echo-audiobook 下 git init
- [ ] 安装依赖,验证 `python -c "import gradio; print('ok')"` 能跑通
- [ ] 推送到 GitHub
