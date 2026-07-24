[English](README.en.md)

# Fuse Bead Designer

把拼豆成品照、像素画、物体照片或高清插画发给 Agent，就能得到可直接照着拼的网格图、逐色用量和可复核报告。Agent 负责理解与整理视觉内容；确定性编译器只接收已确认的逻辑图案，保证网格和数量来自同一份 `pattern.json`，不会靠看图猜数。

![现代拼豆图纸示例](plugins/fuse-bead-designer/assets/screenshot-template.png)

## 第一次使用：把这一句话发给 Agent

> 请安装这个 Codex 插件：https://github.com/MrLQQ/fuse-bead-designer 。请由你完成安装；安装成功后停止，不要运行示例或安装额外运行依赖，只提醒我新建任务。

安装会改动本机环境，因此 Agent 会先请求一次许可；同意后由 Agent 自行检查并完成安装，不需要你复制终端命令。安装完成即停止；请新建任务后，再发送下面的图片需求。

## 日常使用：上传图片，直接说需求

把素材图片拖进支持图像理解的 Agent 对话，然后发送：

> 把这张图生成拼豆设计图。

也可以自然地补充限制，例如“尽量使用标准 29 × 29 拼豆板”“保留白色珠子”“这块遮挡不要猜，标出来让我确认”。正常流程不需要记 Skill 名称，也不需要运行本地命令。

## v0.3.0 图案优先流程

v0.3.0 把“理解图片”和“生成可计数图纸”明确分开：先得到宽高已确认的逻辑图案，再由确定性编译器映射颜色、统计数量、推导拼板布局并渲染交付物。三条输入路线分别是：

1. **拼豆成品照**：先排除手指、桌面、反光等干扰，校正透视并得到声明宽高的正视图。只有校正后的规则网格才能进入编译器。
2. **像素画或现成图纸**：验证其逻辑像素宽高后直接编译。仅当最近邻缩放比例唯一可证明时才自动恢复网格；存在多种解释时会停止并请求确认。
3. **普通照片或高清插画**：先由图像理解或编辑能力生成简洁、网格对齐的**语义图案草稿**，再验证草稿尺寸并编译。该草稿表达要制作的形状和色块，不包含数量或最终图例。

普通照片没有预先存在的珠子网格。本项目不会自动检测普通照片中的通用拼豆晶格，也不会把显示像素直接当作珠子；这类素材必须先经过语义取舍。拼豆成品照也必须先完成透视校正和明确的网格声明，不能从倾斜、遮挡或反光照片中猜出最终格子。

## 图案尺寸、拼板与数量

**先确定图案尺寸，再推导拼板布局。** 编译器接受任意正整数宽高；29 × 29 是标准拼板模块，而不是图案内容的尺寸限制。宽高确定后，编译器再计算需要多少块完整或局部拼板，因此 37 × 22、68 × 60 等尺寸也能被如实表达。

`pattern.json` 是唯一可信源。模板、逐色清单和总数都由同一逻辑网格做确定性统计：固定输入草稿、宽高与调色板会得到相同结果。这里的“精确”只表示对当前图案的精确计数，不把来源中的歧义变成事实。

遮挡区域只有在补全范围小、依据可解释且结果可复现时才会作为**推断区域**记录，并标为 `inferred-low`；大面积、关键或存在多种合理解释的内容会标为 `review-required`。推断区域对应的数量是暂定值，确认前不要据此采购。

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
    <td>58 × 29<br>501 颗<br><code>review-required</code></td>
  </tr>
  <tr>
    <td><strong>高清非像素插画</strong><br>连续色主体转离散色网格</td>
    <td><img src="examples/inputs/high-resolution-mascot.png" alt="高清非像素插画原图" width="260"></td>
    <td><img src="examples/outputs/high-resolution-mascot/template.png" alt="高清非像素插画拼豆设计图" width="360"></td>
    <td>58 × 58<br>1234 颗<br><code>review-required</code></td>
  </tr>
</table>

## 你会收到什么

每次生成都会交付以下文件：

- `template.png`：可制作的坐标网格、每五格辅助线、标准板边界和现代化用量图例。
- `colors.csv`：实际使用颜色、色值、可选品牌色号和精确数量。
- `pattern.json`：唯一可信源，包含网格、调色板、板布局和逐色数量。
- `report.json`：输入分类、清理记录、尺寸选择、警告和可信状态。
- `review.png`：仅当存在已标记的推断格或清理变化坐标时生成，用于集中复核这些位置。

可信状态不是装饰信息：

- `verified`：主体没有受语义补全影响，数量可作为已确认设计的用量。高清图片路线包含语义图案草稿的设计取舍，不能使用此状态。
- `inferred-low`：仅有少量、可解释补全，需要查看标记。
- `review-required`：关键区域仍不确定，当前数量只是暂定值；请先检查 `report.json`，并对照原始素材与语义图案草稿。只有 `report.json` 记录了 `inferred_cells` 或 `cleanup_changes` 时才会生成 `review.png`，届时再检查其中的坐标标记；确认后再采购或开拼。

默认使用通用调色板且不虚构品牌色号，只有你提供品牌色表时才保留 `brand_code`。

## Codex 与其他 Agent 的安装边界

Codex 优先安装完整 Plugin；支持 [Agent Skills](https://agentskills.io/) 的其他工具可以安装 Release 中的独立 Skill。不同宿主的安装目录、权限模型、图像理解和图像编辑能力不同，因此同一句安装提示可能触发不同的内部步骤。

无论宿主如何实现，正常用户只需要发送安装提示和图片需求。Agent 应先获得安装许可，再自行完成可执行的安装；若宿主缺少必要图像能力，Agent 应说明限制并请求补充素材，而不是编造主体或遮挡区域。

## 开发者：高级与调试

> 以下命令只面向 Agent 实现者、维护者和希望调试编译器的开发者。普通用户不要运行这些命令，请使用上面的自然语言流程。

### Codex Marketplace / Plugin

固定安装 v0.3.0：

```bash
codex plugin marketplace add MrLQQ/fuse-bead-designer --ref v0.3.0
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

v0.3.0 打包产物：

```text
dist/fuse-bead-designer-plugin-v0.3.0.zip
dist/create-fuse-bead-patterns-skill-v0.3.0.zip
```

### 直接调用确定性编译器

一般工作流由 Agent 内部调用。仅在调试时直接运行：

```bash
python plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/create_pattern.py \
  --input examples/intermediates/occluded-finished-beads-pattern-draft.png \
  --output-dir work/occluded-pattern \
  --width 58 --height 58 \
  --palette examples/palettes/octopus-generic.json \
  --verification review-required \
  --classification finished-bead-photo \
  --rectified-grid \
  --removed-interference hand fingers wooden-table transparent-pegboard pegs glare shadows background
```

显式尺寸必须同时提供宽高；超过四块板需显式确认。输出目录非空时编译器会拒绝覆盖，除非开发者明确使用强制选项。自定义调色板可以是包含 `id`、`name`、`name_zh`、`hex` 和可选 `brand_code` 的 JSON，也可以使用严格 CSV 表头 `id,name,name_zh,hex,brand_code`。

## 贡献

请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。公开示例必须可再分发；不要提交用户图片、凭据或 `work/` 中的私有中间文件。

## 许可证

[MIT](LICENSE) © 2026 MrLQQ。
