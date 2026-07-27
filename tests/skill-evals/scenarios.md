# Skill Evaluation Scenarios

## Installation-only first use
请安装这个 Codex 插件：https://github.com/MrLQQ/fuse-bead-designer 。请由你完成安装；安装成功后停止，不要运行示例或安装额外运行依赖，只提醒我新建任务。

Expected behavior: request installation permission when needed, complete only the
Marketplace and Plugin installation, then stop and remind the user to start a
new task. It must not clone the repository, run examples, create a virtual
environment, or install runtime dependencies.

## A. Existing pixel art
Turn the supplied clean pixel-art subject into a practical fuse-bead template.
Include a grid and exact color quantities.

## B. High-resolution illustration
Turn the supplied non-pixel illustration into a practical fuse-bead template.
Preserve the subject's silhouette and identity.

## C. Occluded finished work
Turn the supplied photograph of finished fuse-bead work into a practical
template. A hand covers part of the subject and the table remains visible.

## D. Natural-language attached image
把我上传的图片生成拼豆设计图。优先使用常规 29×29 拼豆板，
自动处理背景或手指遮挡，并告诉我每种颜色和数量。

## E. Complex identity-preservation regression

The historical no-skill baseline produced these real failures:

- `58 x 58`: 1788 beads; facial detail was flattened.
- `87 x 87`: 3970 beads; still less similar than the 2875-bead reference.
- `110 x 122`: 10044 beads; display pixels were over-sampled as beads.

Turn a detailed dark character reference into a practical fuse-bead template.
Preserve its small eyes, facial marks, thin edge accents, isolated highlights,
and signature ornament. The target is not an exact `68 x 60` grid; choose and
verify a logical grid that preserves identity within a practical bead-count
band, then derive board layout.

## F. Baseline-first default

Turn the supplied image into a fuse-bead pattern.

Expected behavior: finish and deliver one baseline first, then ask the single
optional multi-size question. Do not spend resources generating variants
before the user accepts.

## G. Explicit multi-size semantic redesign

Create economy, balanced, detail, and baseline options for the supplied image.
Preserve meaning-bearing details even if a tier must become larger.

Expected behavior: treat this as explicit multi-size intent and skip the
optional question. Create independent semantic redraws rather than mechanical
downsampling. Cancel a tier whose hard features fail after one larger retry and
merge adjacent duplicates.

The generic matrix must cover **people or animals**, **objects**, **text or
logos**, **buildings or landscapes**, **plants or abstract art**, and
**occluded finished-bead photos**. Each fixture gets its own hard/soft feature
contract; no category inherits a human-face checklist.

## H. Repeated-grid and rare-color resource regression

The supplied rectified pattern is a 105 × 102 observed grid whose semantic
pixels are globally repeated 3 × 3. Its supplied palette contains 21 used
colors, including five rare single-cell accents.

Expected behavior: recover the 35 × 34 semantic grid, derive boards afterward,
and preserve all 21 colors in the baseline. Do not pass `--colors` unless the
request explicitly asks for a reduced-color variant. Report the 9× area
normalization and separate grid, color, and semantic fidelity.
