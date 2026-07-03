<div align="center">

# 🎮 Game Maker

**AI game asset generator — characters, backgrounds, scripts, and a full game plan in a zip**

![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=flat&logo=openai&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)

🌐 **[Live Demo → game-maker.streamlit.app](https://game-maker.streamlit.app)**

</div>

---

Game Maker is a Streamlit app that uses DALL·E 3 and GPT to generate all the assets you need to start building a game — then packages everything into a downloadable zip file.

## ✨ Features

- **Image Generation** — DALL·E 3 characters, enemies, backgrounds, and objects
- **Document Generation** — game plans, character sheets, level designs, plot outlines
- **Script Generation** — Unity C# scripts for player controls, enemies, game objects, level backgrounds
- **Selective Generation** — choose specific asset types or generate everything at once
- **Full Game Plan Download** — one zip file with all images, docs, and scripts

## 🚀 Quick Start

```bash
git clone https://github.com/RhythrosaLabs/game-maker.git
cd game-maker
pip install streamlit openai
streamlit run app.py
```

Or try the live demo at [game-maker.streamlit.app](https://game-maker.streamlit.app).

Enter your OpenAI API key in the sidebar, describe your game concept, and generate!

## 🛠️ Tech Stack

- **Python + Streamlit** — web app UI
- **OpenAI GPT-4o-mini** — document and script generation
- **DALL·E 3** — image generation
- **zipfile** — bundle export

## 📦 Output Structure

```
game_plan.zip
├── images/         # character, enemy, background, object PNGs
├── documents/      # game plan, character sheets, level designs
└── scripts/        # Unity C# scripts ready to use
```

## 🤝 Contributing

PRs welcome. Open an issue first for major changes.

## 📄 License

MIT

## 💛 Support

If Game Maker helps you ship your game, consider supporting development:

👉 [Donate via PayPal](https://paypal.me/noodlebake) — @noodlebake

---
<div align="center">Made with ❤️ by <a href="https://github.com/RhythrosaLabs">RhythrosaLabs</a></div>
