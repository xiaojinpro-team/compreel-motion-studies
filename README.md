# compreel motion studies

Open, shot-by-shot **motion studies** of product films we admire, rebuilt as editable projects you can learn from and reuse: a web (Canvas 2D) version driven by a small keyframe protocol, plus After Effects and Blender versions of the same motion.

公开的「动作研究」:把我们喜欢的产品片逐镜复刻成可编辑的工程(网页 Canvas 2D + After Effects + Blender 三版),公开学习,手法学到手就分享出来。

## Studies · 研究

| Study | Subject | What it teaches |
|---|---|---|
| [`studies/launch-icon-orbit-01/`](studies/launch-icon-orbit-01/) | a launch-intro opening shot | eased log-space camera pull-back, per-item depth settle with one shared overshoot ease, per-item spin, radial rush-out with a per-frame shutter, title timing |

Each study folder has its own README (中英), the keyframe data, the generator that produced it, and three renderable projects (`canvas2d/`, `ae/`, `blender/`). Icons and other brand artwork are replaced by placeholder squares; put your own in.

## How it was made · 做法

The motion is recorded as **numbers**, not pixels: per-object keys (x, y, scale, rotation, opacity, z) plus a camera track and a shutter curve, in the [motion-kit](https://github.com/xiaojinpro-team) `keys.v1` protocol. The same file drives the web player, AE and Blender, so any of the three can be your starting point.

## License · 授权

Code and data in this repository: **MIT** (see `LICENSE`). These studies are educational reconstructions of *motion*; they contain no frames, textures or artwork from any original film.

Made by [compreel.com](https://compreel.com) · 小靳剪辑工作室
