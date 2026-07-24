[English](README.en.md)

# Fuse Bead Designer

把拼豆成品照、物体照片或高清插画发给 Agent，就能得到可直接照着拼的网格图、逐色用量和可复核报告。Agent 负责识别主体、处理背景与遮挡；确定性编译器保证网格和数量来自同一份 `pattern.json`，不会靠看图猜数。

![现代拼豆图纸示例](plugins/fuse-bead-designer/assets/screenshot-template.png)

## 第一次使用：把这一句话发给 Agent

> 请安装这个 Codex 插件：https://github.com/MrLQQ/fuse-bead-designer 。请由你完成安装；安装成功后停止，不要运行示例或安装额外运行依赖，只提醒我新建任务。

安装会改动本机环境，因此 Agent 会先请求一次许可；同意后由 Agent 自行检查并完成安装，不需要你复制终端命令。安装完成即停止；请新建任务后，再发送下面的图片需求。

## 日常使用：上传图片，直接说需求

把素材图片拖进支持图像理解的 Agent 对话，然后发送：

> 把这张图生成拼豆设计图

也可以自然地补充限制，例如“尽量使用标准 29 × 29 拼豆板”“保留白色珠子”“这块遮挡不要猜，标出来让我确认”。正常流程不需要记 Skill 名称，也不需要运行本地命令。

## 从原图到可制作图纸

下面四组均为仓库中的真实输入和确定性编译产物，不是效果示意图。

<table>
  <tr>
    <th>场景</th>
    <th>原始素材</th>
    <th>拼豆设计图</th>
    <th>结果</th>
  </tr>
  <tr>
    <td><strong>有遮挡的拼豆成品</strong><br>手指、画板与环境干扰</td>
    <td><img src="examples/inputs/occluded-finished-beads.png" alt="有遮挡的拼豆成品原图" width="260"></td>
    <td><img src="examples/outputs/occluded-finished-beads/template.png" alt="有遮挡的拼豆成品设计图" width="360"></td>
    <td>58 × 58<br>1525 颗<br><code>review-required</code></td>
  </tr>
  <tr>
    <td><strong>有遮挡的高清图片</strong><br>主体局部被标签遮住</td>
    <td><img src="examples/inputs/occluded-high-resolution-image.png" alt="有遮挡的高清图片原图" width="260"></td>
    <td><img src="examples/outputs/occluded-high-resolution-image/template.png" alt="有遮挡的高清图片设计图" width="360"></td>
    <td>58 × 58<br>719 颗<br><code>review-required</code></td>
  </tr>
  <tr>
    <td><strong>实际物体照片</strong><br>从摄影背景中提取主体</td>
    <td><img src="examples/inputs/actual-object-photo.png" alt="实际物体照片原图" width="260"></td>
    <td><img src="examples/outputs/actual-object-photo/template.png" alt="实际物体拼豆设计图" width="360"></td>
    <td>58 × 29<br>501 颗<br><code>verified</code></td>
  </tr>
  <tr>
    <td><strong>高清非像素插画</strong><br>连续色主体转离散色网格</td>
    <td><img src="examples/inputs/high-resolution-mascot.png" alt="高清非像素插画原图" width="260"></td>
    <td><img src="examples/outputs/high-resolution-mascot/template.png" alt="高清非像素插画拼豆设计图" width="360"></td>
    <td>58 × 58<br>1234 颗<br><code>verified</code></td>
  </tr>
</table>

## 你会收到什么

每次生成都会交付以下文件：

- `template.png`：可制作的坐标网格、每五格辅助线、标准板边界和现代化用量图例。
- `colors.csv`：实际使用颜色、色值、可选品牌色号和精确数量。
- `pattern.json`：唯一可信源，包含网格、调色板、板布局和逐色数量。
- `report.json`：输入分类、清理记录、尺寸选择、警告和可信状态。
- `review.png`：存在遮挡补全或清理标记时，用于集中复核不确定区域。

可信状态不是装饰信息：

- `verified`：主体没有受语义补全影响，数量可作为已确认设计的用量。
- `inferred-low`：仅有少量、可解释补全，需要查看标记。
- `review-required`：关键区域仍不确定，当前数量只是暂定值；请先检查 `review.png` 和 `report.json`，确认后再采购或开拼。

这里的“精确数量”指固定输入、网格与调色板下的确定性统计，不代表模糊照片、未知遮挡或现实库存的绝对真值。

## 支持的素材与自动处理

Skill 面向通用输入，而不是只接受已经像素化的图片：

- 拼豆成品照：识别拼豆主体，区分手指、桌面、透明画板、反光和阴影。
- 有遮挡的照片或插画：只补全可解释区域；关键内容无法验证时保留为待复核状态。
- 实际物体照片：分离主体与摄影背景，同时保留白色等主体细节。
- 高清非像素图：简化轮廓和连续色，使每个网格只对应一颗拼豆。
- 干净像素画：尽量保留原始比例与硬边缘。

标准模块是 29 × 29。Agent 会根据主体比例在 29 × 29、58 × 29、29 × 58、58 × 58 等常规组合中选择，也可按你的自然语言要求使用自定义尺寸；超过四块板前会先确认。默认使用通用调色板且不虚构品牌色号，只有你提供品牌色表时才保留 `brand_code`。

## Codex 与其他 Agent 的安装边界

Codex 优先安装完整 Plugin；支持 [Agent Skills](https://agentskills.io/) 的其他工具可以安装 Release 中的独立 Skill。不同宿主的安装目录、权限模型、图像理解和图像编辑能力不同，因此同一句安装提示可能触发不同的内部步骤。

无论宿主如何实现，正常用户只需要发送安装提示和图片需求。Agent 应先获得安装许可，再自行完成可执行的安装；若宿主缺少必要图像能力，Agent 应说明限制并请求补充素材，而不是编造主体或遮挡区域。

## 开发者

> 以下命令只面向 Agent 实现者、维护者和希望调试编译器的开发者。普通用户不要运行这些命令，请使用上面的自然语言流程。

### Codex Marketplace / Plugin

固定安装 v0.2.0：

```bash
codex plugin marketplace add MrLQQ/fuse-bead-designer --ref v0.2.0
codex plugin add fuse-bead-designer@fuse-bead-designer
```

从本地克隆调试：

```bash
git clone https://github.com/MrLQQ/fuse-bead-designer.git
cd fuse-bead-designer
codex plugin marketplace add "$PWD"
codex plugin add fuse-bead-designer@fuse-bead-designer
```

### 独立 Skill

```bash
cp -R plugins/fuse-bead-designer/skills/create-fuse-bead-patterns \
  "${CODEX_HOME:-$HOME/.codex}/skills/"
```

### 本地开发、测试与打包

```bash
python -m pip install -e ".[test]"
pytest -q
python tools/package_release.py
```

v0.2.0 打包产物：

```text
dist/fuse-bead-designer-plugin-v0.2.0.zip
dist/create-fuse-bead-patterns-skill-v0.2.0.zip
```

### 直接调用确定性编译器

一般工作流由 Agent 内部调用。仅在调试时直接运行：

```bash
python plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/create_pattern.py \
  --input examples/intermediates/occluded-finished-beads-clean.png \
  --output-dir work/occluded-pattern \
  --width 58 --height 58 \
  --palette examples/palettes/octopus-generic.json \
  --verification review-required \
  --classification finished-bead-photo \
  --removed-interference hand fingers wooden-table transparent-pegboard pegs glare shadows background
```

显式尺寸必须同时提供宽高；超过四块板需显式确认。输出目录非空时编译器会拒绝覆盖，除非开发者明确使用强制选项。自定义调色板可以是包含 `id`、`name`、`name_zh`、`hex` 和可选 `brand_code` 的 JSON，也可以使用严格 CSV 表头 `id,name,name_zh,hex,brand_code`。

## 贡献

请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。公开示例必须可再分发；不要提交用户图片、凭据或 `work/` 中的私有中间文件。

## 许可证

[MIT](LICENSE) © 2026 MrLQQ。
