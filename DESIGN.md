# 星源 UI 3：采样协作工作台

## 设计方向

依据用户要求推翻原有界面结构。奶油色 #F7F4EB、内容面板 #FFFDF7、重点黄色 #EED053、文字 #303128、次级文字 #747366。顶部导航、独立任务队列、边缘详情抽屉和人员目录构成业务工作空间；基础样式独立于旧版，不再加载 styles.css / theme.css。

## MotionSites 公开参考

- Animated Shader Hero：https://motionsites.org/prompts/ravikatiyar162-animated-shader-hero ，借鉴公开预览中的暖金流动方向。
- Freight Command：https://motionsites.org/prompts/freight-command ，借鉴公开预览中任务队列与详情并置的层级。
- Task Engine：https://motionsites.org/prompts/task-engine ，已查看，未作为主要布局依据。

完整提示词需要登录或权益验证，本次没有复制受限提示词或模板代码。ambient.js 是本项目独立编写的 WebGL 着色器，非参考组件原版。

## 布局与动效

顶部：品牌 / 业务导航 / 账户操作。工作台：今日工作引导和暖金流动区域 / 统计条 / 任务队列及日历团队。任务页：状态筛选 / 搜索与地区有效期筛选 / 可点击任务行 / 右侧详情。人员页：成员目录行。

动效仅用于入口氛围、抽屉展开和按钮反馈。着色器每秒最多约 30 帧，像素比最高 1.5；页面隐藏时停止，减少动态效果偏好下仅绘制静态帧，WebGL 不可用时保留 CSS 背景。

## 验证

前端现有 12 项检查通过。浏览器实际验证创建临时任务、任务队列、右侧详情、手机导航、390px 抽屉、桌面与手机登录布局。临时任务已按唯一编号清理，未改动用户原有数据。
