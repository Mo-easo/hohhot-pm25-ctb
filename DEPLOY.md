# 部署说明 — 长期稳定公网地址

本项目已配置可部署到 **Render**（推荐）或 **Fly.io**。

## 方式一：Render 一键部署（推荐）

1. 打开：https://render.com/deploy?repo=https://github.com/Mo-easo/hohhot-pm25-ctb
2. 使用 GitHub 账号登录 Render（可选 `Mo-easo`）
3. 确认 Blueprint / 服务名 `hohhot-pm25-ctb`
4. 点击 **Apply** / **Deploy**
5. 等待 Build 完成（约 2–5 分钟）
6. 获得公网地址：`https://hohhot-pm25-ctb.onrender.com`（以控制台显示为准）

免费实例闲置一段时间后会休眠，首次访问可能需等待 30–60 秒唤醒。  
需要真正 7×24 不休眠时，在 Render 升级为付费实例即可。

## 方式二：Fly.io

```powershell
$env:Path = "C:\Users\12235\.fly\bin;" + $env:Path
flyctl auth login
cd C:\Users\12235\hohhot_pm25_ctb
flyctl launch --copy-config --yes
flyctl deploy
```

部署成功后地址形如：`https://hohhot-pm25-ctb.fly.dev`

## 本地生产依赖

生产镜像只安装 `requirements-prod.txt`（Flask + gunicorn），体积更小、构建更稳。
