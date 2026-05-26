import { useState, useEffect, useRef } from "react";
import {
  Download,
  Music,
  Video,
  Folder,
  Link as LinkIcon,
  CheckCircle2,
  AlertCircle,
  Loader2,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

function App() {
  const [url, setUrl] = useState("");
  const [format, setFormat] = useState("mp3");
  const [quality, setQuality] = useState("192");
  const [folder, setFolder] = useState("downloads");
  const [isDownloading, setIsDownloading] = useState(false);
  const [progress, setProgress] = useState(null);
  const [error, setError] = useState(null);
  const [folders, setFolders] = useState([]);

  const eventSourceRef = useRef(null);

  const closeEventSource = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  };

  useEffect(() => {
    if (format === "mp4") {
      const mp4Qualities = ["144", "240", "360", "480", "720", "1080", "best"];
      if (!mp4Qualities.includes(quality)) {
        setQuality("360");
      }
    }
  }, [format, quality]);

  useEffect(() => {
    // Fetch available folders
    fetch("http://localhost:8000/api/folders")
      .then((res) => res.json())
      .then((data) => setFolders(data))
      .catch((err) => console.error("Failed to fetch folders", err));

    return () => {
      closeEventSource();
    };
  }, []);

  const startDownload = async () => {
    if (!url) return;

    setIsDownloading(true);
    setError(null);
    setProgress({
      status: "initializing",
      percent: 0,
      title: "Buscando informações...",
    });

    // Setup SSE
    closeEventSource();

    const eventSource = new EventSource("http://localhost:8000/api/events");
    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setProgress(data);

      if (data.status === "finished" && data.index === data.total) {
        setIsDownloading(false);
        closeEventSource();
      }
    };

    eventSource.onerror = () => {
      if (eventSourceRef.current === eventSource) {
        setIsDownloading(false);
        setError(
          "A conexão de progresso foi perdida. Tente iniciar o download novamente.",
        );
        closeEventSource();
      }
    };

    try {
      const response = await fetch("http://localhost:8000/api/download", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, format, quality, folder }),
      });

      if (!response.ok) throw new Error("Falha ao iniciar download");
    } catch (err) {
      setError(err.message);
      setIsDownloading(false);
      closeEventSource();
    }
  };

  return (
    <div className="container">
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1>Music Downloader</h1>
        <p className="subtitle">
          Baixe músicas e playlists com qualidade premium
        </p>
      </motion.header>

      <main className="glass premium-card">
        <div className="input-group">
          <label>
            <LinkIcon size={14} style={{ marginRight: 6 }} /> Link do YouTube
          </label>
          <input
            type="url"
            placeholder="Cole o link do vídeo ou playlist aqui..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={isDownloading}
          />
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: "1rem",
          }}
        >
          <div className="input-group">
            <label>
              <Music size={14} style={{ marginRight: 6 }} /> Formato
            </label>
            <select
              value={format}
              onChange={(e) => setFormat(e.target.value)}
              disabled={isDownloading}
            >
              <option value="mp3">MP3 (Áudio)</option>
              <option value="mp4">MP4 (Vídeo)</option>
            </select>
          </div>

          <div className="input-group">
            <label>
              <Video size={14} style={{ marginRight: 6 }} /> Qualidade
            </label>
            <select
              value={quality}
              onChange={(e) => setQuality(e.target.value)}
              disabled={isDownloading}
            >
              {format === "mp3" ? (
                <>
                  <option value="128">128 kbps</option>
                  <option value="192">192 kbps (Padrão)</option>
                  <option value="256">256 kbps</option>
                  <option value="320">320 kbps (Melhor)</option>
                </>
              ) : (
                <>
                  <option value="144">144p</option>
                  <option value="240">240p</option>
                  <option value="360">360p</option>
                  <option value="480">480p</option>
                  <option value="720">720p (HD)</option>
                  <option value="1080">1080p (Full HD)</option>
                  <option value="best">Melhor Disponível</option>
                </>
              )}
            </select>
          </div>
        </div>

        <div className="input-group">
          <label>
            <Folder size={14} style={{ marginRight: 6 }} /> Pasta de Destino
          </label>
          <input
            list="folder-list"
            type="text"
            value={folder}
            onChange={(e) => setFolder(e.target.value)}
            disabled={isDownloading}
            placeholder="Ex: downloads_mp3"
          />
          <datalist id="folder-list">
            {folders.map((f) => (
              <option key={f.path} value={f.name}>
                {f.path}
              </option>
            ))}
          </datalist>
        </div>

        <button
          className="btn-primary"
          onClick={startDownload}
          disabled={isDownloading || !url}
        >
          {isDownloading ? (
            <>
              <Loader2 className="animate-spin" /> Baixando...
            </>
          ) : (
            <>
              <Download /> Iniciar Download
            </>
          )}
        </button>

        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="error-message"
              style={{
                color: "var(--error)",
                marginTop: "1rem",
                display: "flex",
                alignItems: "center",
                gap: "0.5rem",
              }}
            >
              <AlertCircle size={18} /> {error}
            </motion.div>
          )}

          {progress && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="progress-container"
            >
              <div className="video-title">
                {progress.total > 1
                  ? `[${progress.index}/${progress.total}] `
                  : ""}
                {progress.title}
              </div>
              <div className="progress-info">
                <span>
                  {progress.status === "finished"
                    ? "Concluído"
                    : `${Math.round(progress.percent)}%`}
                </span>
                {progress.eta && <span>ETA: {progress.eta}</span>}
              </div>
              <div className="progress-bar-bg">
                <motion.div
                  className="progress-bar-fill"
                  initial={{ width: 0 }}
                  animate={{ width: `${progress.percent}%` }}
                  transition={{ type: "spring", stiffness: 50 }}
                />
              </div>
              {progress.status === "finished" &&
                progress.index === progress.total && (
                  <div
                    style={{
                      color: "var(--success)",
                      marginTop: "0.5rem",
                      display: "flex",
                      alignItems: "center",
                      gap: "0.5rem",
                      fontSize: "0.9rem",
                    }}
                  >
                    <CheckCircle2 size={16} /> Todos os downloads concluídos com
                    sucesso!
                  </div>
                )}
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}

export default App;
