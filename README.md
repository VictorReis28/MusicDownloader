# 🎵 Music Downloader Web

Uma aplicação web moderna, rápida e "premium" para baixar músicas e playlists do YouTube com facilidade. Transforme links do YouTube em arquivos MP3 ou MP4 com um clique, acompanhando o progresso em tempo real.

## ✨ Funcionalidades

- **Interface Premium**: Design moderno com Glassmorphism e animações fluídas.
- **Download Flexível**: Suporte para vídeos individuais e playlists completas.
- **Formatos Personalizados**: Escolha entre **MP3 (Áudio)** e **MP4 (Vídeo)**.
- **Qualidade Ajustável**: Selecione o bitrate (MP3) ou a resolução (MP4) desejada.
- **Progresso em Tempo Real**: Barra de progresso visual que mostra exatamente o que está sendo baixado.
- **Organização Inteligente**: Nomes de arquivos limpos (apenas o título do vídeo) e seletor de pasta de destino.

## 🚀 Como Rodar

### Pré-requisitos
- **Python 3.10+**
- **Node.js & npm**
- **FFmpeg**: Configurado automaticamente via `static-ffmpeg`.

### Passo a Passo

1.  **Iniciar a Aplicação**:
    Na pasta raiz do projeto, execute o script de inicialização automática:
    ```bash
    python start.py
    ```

2.  **Acessar a Interface**:
    Abra seu navegador e vá para:
    👉 [http://localhost:5173](http://localhost:5173)

## 🛠️ Tecnologias Utilizadas

- **Backend**: FastAPI (Python), yt-dlp, static-ffmpeg.
- **Frontend**: React (Vite), Framer Motion (Animações), Lucide React (Ícones).
- **Estilização**: Vanilla CSS com variáveis modernas e Design System próprio.

## 📂 Estrutura do Projeto

```
.
├── web/
│   ├── backend/    # Servidor FastAPI e lógica de download
│   └── frontend/   # Aplicação React (Vite)
├── start.py        # Script para rodar backend e frontend simultaneamente
└── music-downloader.md # Plano de implementação e especificações
```

---
*Desenvolvido com foco em UX e performance.*
