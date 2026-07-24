[English](README.en.md)

# Fuse Bead Designer

把参考图转换为可复核的拼豆图纸：编译器从唯一的 `pattern.json` 生成网格、配色数量和报告，避免手工抄数不一致。

![真实图纸示例](plugins/fuse-bead-designer/assets/screenshot-template.png)

## 为什么有这个项目

成品拼豆照片、像素画和普通插画都可能含背景、阴影、遮挡或连续色。这个项目把“看懂图像”和“确定性出图”拆开：前者由 Agent 判断和清理，后者由本地 Python/Pillow 编译器完成，因此每个输出数量都能回溯到 `pattern.json`。

## 支持的输入与不确定性边界

支持干净的像素画、高分辨率主体图，以及已完成拼豆作品的照片。编译器接受经清理的主体图；它不会自行可靠地识别复杂语义、校正严重透视或重建大面积遮挡。

Agent 对小面积、可解释的补全必须标记坐标并输出 `review.png`。`verified` 表示没有影响主体的语义补全；`inferred-low` 表示有限补全；`review-required` 表示关键区域不确定。最后一种状态的数量仅为暂定值，不能当作已确认用料。默认不会虚构品牌色号；只有你提供的调色板中已有 `brand_code` 才会保留。

## 快速开始：Codex Plugin

```bash
git clone https://github.com/MrLQQ/fuse-bead-designer.git
cd fuse-bead-designer
codex plugin marketplace add "$PWD"
codex plugin add fuse-bead-designer@personal
```

安装后，在带图像理解能力的 Codex 对话中调用 `$create-fuse-bead-patterns`，先得到干净、正视的主体中间图；再用下面的本地编译命令产出图纸。没有图像能力时，遇到主体不明确或遮挡无法解释，应停下向用户确认，而不是猜测。

## 独立安装 Agent Skill

只需要可移植 Skill 时，将其复制到 Codex 的 Skills 目录：

```bash
cp -R plugins/fuse-bead-designer/skills/create-fuse-bead-patterns \
  "${CODEX_HOME:-$HOME/.codex}/skills/"
```

## 其他兼容 Agent Skills 的工具

任何支持 [Agent Skills](https://agentskills.io/) 格式的工具都可以使用 `plugins/fuse-bead-designer/skills/create-fuse-bead-patterns`。不同宿主的 Skills 目录、启用方式和图像工具能力不同；请按宿主文档放置该目录。该 Skill 不承诺替代宿主的图像理解或编辑能力。

## 使用示例

安装运行依赖后，以下命令将公开像素画样例编译为一张标准 29 × 29 板的图纸：

```bash
python -m pip install -e ".[test]"
python plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/create_pattern.py \
  --input examples/inputs/clean-pixel-art.png \
  --output-dir work/cat-pattern \
  --width 29 --height 29 \
  --classification pixel-art
```

高分辨率图可让编译器自动在 29 × 29、58 × 29、29 × 58、58 × 58 等标准板组合中选择。显式尺寸必须同时给出 `--width` 和 `--height`；超过四块板需要 `--confirm-large-board`。使用含遮挡的照片时，由 Agent 明确给出经过审查的补全坐标，例如：

```bash
python plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/scripts/create_pattern.py \
  --input examples/inputs/occluded-finished-beads.png \
  --output-dir work/occluded-pattern \
  --verification inferred-low --inferred-cells 12,8 13,8 \
  --classification finished-bead-photo
```

## 输出

每次成功编译都会写入：

- `pattern.json`：唯一可信源，含网格、调色板、每色数量、板布局和不确定性状态。
- `template.png`：可制作的坐标网格、每五格辅助线、29 格板边界（标准尺寸时）与图例。
- `colors.csv`：`id,name,name_zh,hex,brand_code,count` 和精确数量。
- `report.json`：输入分类、清理记录、板与调色板决策、警告和不确定性状态。
- `review.png`：仅在有推断单元或清理标记时生成。

`total_beads` 必须等于 `color_counts` 之和；输出目录非空时命令会拒绝覆盖，除非显式使用 `--force`。

## 板尺寸

标准模块为 29 × 29。自动选择优先考虑 1、2 或 4 块板，按裁切、留白、轮廓保留和总珠数权衡。自定义尺寸可以使用，但会明确标为不等同于标准拼豆板；超过四块板的最终设计应先获得用户确认。

## 通用与品牌调色板

未传 `--palette` 时，使用内置的 16 色通用 JSON 调色板。也可传入 JSON 数组，每项有 `id`、`name`、`name_zh`、`hex`，并可选 `brand_code`；或严格使用 CSV 表头：

```text
id,name,name_zh,hex,brand_code
```

编译器只映射到给定调色板中的颜色，默认 8–16 色且不抖动。品牌名称与色号由你提供，不由本项目推断。

## 已知限制

输出的“精确”是指已确定输入、网格和调色板下的确定性计数，不代表对模糊照片、被遮挡区域或现实库存的客观真值。透明背景与白色珠子是不同状态，但主体遮罩错误仍会影响结果。请在拼制前检查 `review.png`、`report.json` 和实际库存；图纸不提供熨烫、材料安全或成品质量保证。

## 开发与测试

```bash
python -m pip install -e ".[test]"
pytest -q
python tools/package_release.py
```

打包会生成两个确定性归档：

```text
dist/fuse-bead-designer-plugin-v0.1.0.zip
dist/create-fuse-bead-patterns-skill-v0.1.0.zip
```

## 贡献

请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。提交前运行测试，公开示例必须可再分发，且不要提交用户图像、凭据或 `work/` 中的私有中间文件。

## 许可证

[MIT](LICENSE) © 2026 MrLQQ。
