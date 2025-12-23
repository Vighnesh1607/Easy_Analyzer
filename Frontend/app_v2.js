console.log("EasyAnalyzer — Workspace UI Loaded");

////////////////////////////////////////////////////////////////////////////////
// SIDEBAR
////////////////////////////////////////////////////////////////////////////////
const Sidebar = ({ currentPage, setPage }) => {
  const menu = [
    { name: "Dashboard", key: "dashboard" },
    { name: "Transcription", key: "transcribe" },
    { name: "RAG", key: "rag" },
    { name: "Settings", key: "settings" },
  ];

  return (
    <aside className="w-44 bg-slate-900 text-white flex flex-col py-6 border-r border-slate-800">
      <div className="px-4 mb-8">
        <div className="text-sm font-semibold text-gray-400">EasyAnalyzer</div>
      </div>

      <nav className="flex-1 space-y-1 px-3">
        {menu.map((m) => (
          <button
            key={m.key}
            onClick={() => setPage(m.key)}
            className={
              "w-full py-2 px-3 text-left rounded text-sm transition-all " +
              (currentPage === m.key
                ? "bg-blue-600 text-white font-medium"
                : "text-gray-300 hover:bg-slate-800 hover:text-white")
            }
          >
            {m.name}
          </button>
        ))}
      </nav>
    </aside>
  );
};

////////////////////////////////////////////////////////////////////////////////
// TOPBAR
////////////////////////////////////////////////////////////////////////////////
const Topbar = ({ title }) => {
  return (
    <header className="h-14 border-b border-gray-200 bg-white px-8 flex items-center justify-between">
      <div>
        <h1 className="text-xl font-semibold text-gray-800">{title}</h1>
        <p className="text-xs text-gray-500">Audio analysis workspace</p>
      </div>
      <div className="flex items-center gap-3">
        <span className="w-2 h-2 rounded-full bg-green-500"></span>
        <span className="text-sm text-gray-600">Connected</span>
      </div>
    </header>
  );
};

////////////////////////////////////////////////////////////////////////////////
// TRANSCRIPTION
////////////////////////////////////////////////////////////////////////////////
const TranscriptionCenter = () => {
  const [logData, setLogData] = React.useState([]);
  const [outputType, setOutputType] = React.useState("analysis");
  const [pdfLink, setPdfLink] = React.useState("");
  const [isRecording, setIsRecording] = React.useState(false);
  const [sessionId, setSessionId] = React.useState("");

  const wsRef = React.useRef(null);
  const recorderRef = React.useRef(null);

  const addLog = (msg) =>
    setLogData((prev) => [new Date().toLocaleTimeString() + " — " + msg, ...prev]);

  const safeSend = (p) => {
    try {
      if (wsRef.current?.readyState === 1) wsRef.current.send(p);
    } catch {}
  };

  ////////////////////////////////////////////////////////////////////////////
  // START LIVE CAPTURE
  ////////////////////////////////////////////////////////////////////////////
  const startLive = async () => {
    if (isRecording) return;

    const sid = "meeting_" + Date.now();
    setSessionId(sid);
    addLog("Starting session...");

    const ws = new WebSocket("ws://localhost:8000/ws/live/" + sid);
    wsRef.current = ws;

    ws.onopen = () => safeSend(`__OUTPUT_TYPE__::${outputType}`);

    ws.onmessage = (e) => {
      if (e.data.startsWith("__REPORT_READY__")) {
        const id = e.data.split("::")[1];
        setPdfLink("http://localhost:8000/live-report/" + id);
        addLog("PDF Ready");
      } else {
        addLog(e.data);
      }
    };

    const stream = await navigator.mediaDevices.getDisplayMedia({
      audio: true, video: true
    });

    const ctx = new AudioContext();
    const dest = ctx.createMediaStreamDestination();
    ctx.createMediaStreamSource(stream).connect(dest);

    const recorder = new MediaRecorder(dest.stream);
    recorderRef.current = recorder;

    recorder.ondataavailable = async (ev) => {
      wsRef.current?.send(await ev.data.arrayBuffer());
    };

    recorder.start(1000);
    setIsRecording(true);
  };

  ////////////////////////////////////////////////////////////////////////////
  // STOP LIVE
  ////////////////////////////////////////////////////////////////////////////
  const stopLive = () => {
    recorderRef.current?.stop();
    wsRef.current?.send("__END_MEETING__");
    setIsRecording(false);
    addLog("Stopped");
  };

  ////////////////////////////////////////////////////////////////////////////
  // UPLOAD VIDEO
  ////////////////////////////////////////////////////////////////////////////
  const uploadVideo = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    addLog("Uploading...");
    const fd = new FormData();
    fd.append("file", file);
    fd.append("output_type", outputType);

    const res = await fetch("http://localhost:8000/upload-video", {
      method: "POST",
      body: fd,
    });

    const data = await res.json();

    if (data.session_id) setSessionId(data.session_id);

    // FIX: SUPPORT ANALYSIS + NOTES
    if (outputType === "analysis" && data.analysis) {
      setPdfLink(data.analysis);
    } else if (outputType === "notes" && data.notes) {
      setPdfLink(data.notes);
    } else if (data.pdf_url) {
      setPdfLink(data.pdf_url);
    }

    addLog("Processed");
  };

  ////////////////////////////////////////////////////////////////////////////
  // INDEX FOR RAG
  ////////////////////////////////////////////////////////////////////////////
  const indexNow = async () => {
    if (!sessionId) return addLog("No session ID.");

    await fetch(`http://localhost:8000/rag/store/${sessionId}`, {
      method: "POST",
    });

    addLog("Indexed");
  };

  ////////////////////////////////////////////////////////////////////////////
  // UI RETURN
  ////////////////////////////////////////////////////////////////////////////
  return (
    <div className="flex w-full h-full bg-gray-50">
      {/* LEFT PANEL */}
      <div className="w-72 bg-white border-r border-gray-200 p-5">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Recording Settings</h3>

        <label className="block text-xs text-gray-600 mb-1.5">Output Format</label>
        <select
          className="w-full border border-gray-300 rounded px-2.5 py-1.5 text-xs mb-5"
          value={outputType}
          onChange={(e) => setOutputType(e.target.value)}
        >
          <option value="analysis">Analysis PDF</option>
          <option value="notes">Notes PDF</option>
        </select>

        <button
          onClick={startLive}
          disabled={isRecording}
          className={
            "w-full mb-2 px-3 py-2 rounded text-xs font-medium transition " +
            (isRecording
              ? "bg-gray-200 text-gray-500"
              : "bg-blue-500 hover:bg-blue-600 text-white")
          }
        >
          {isRecording ? "Recording..." : "Start Live Capture"}
        </button>

        <button
          onClick={stopLive}
          disabled={!isRecording}
          className={
            "w-full mb-2 px-3 py-2 rounded text-xs font-medium transition " +
            (!isRecording
              ? "bg-gray-200 text-gray-500"
              : "bg-red-500 hover:bg-red-600 text-white")
          }
        >
          Stop Recording
        </button>

        <button
          onClick={indexNow}
          className="w-full mb-4 px-3 py-2 rounded text-xs font-medium bg-indigo-500 hover:bg-indigo-600 text-white"
        >
          Index for Search
        </button>

        <label className="block text-xs text-gray-600 mb-2">Or upload a video file</label>
        <input type="file" onChange={uploadVideo} className="text-xs" />

        {pdfLink && (
          <div className="mt-5 p-3 bg-green-50 border border-green-200 rounded">
            <p className="text-xs text-green-700">Report ready!</p>
            <a
              href={pdfLink}
              target="_blank"
              className="text-sm text-green-600 underline"
            >
              Download PDF →
            </a>
          </div>
        )}
      </div>

      {/* CENTER PANEL */}
      <div className="flex-1 p-8 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-800 mb-2">
            Ready to capture
          </h2>
          <p className="text-gray-500 text-xs">
            Click "Start Live Capture" to begin recording your meeting.
          </p>
        </div>
      </div>

      {/* RIGHT PANEL */}
      <div className="w-80 bg-white border-l border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <h3 className="text-sm font-medium text-gray-700">Activity Feed</h3>
        </div>

        <div className="flex-1 overflow-auto p-3 space-y-1.5">
          {logData.length === 0 ? (
            <div className="text-xs text-gray-400 italic text-center py-4">
              No activity yet
            </div>
          ) : (
            logData.map((l, i) => (
              <div key={i} className="text-xs text-gray-700 py-1 px-2 bg-gray-50 rounded">
                {l}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

////////////////////////////////////////////////////////////////////////////////
// RAG UI
////////////////////////////////////////////////////////////////////////////////
const RagUI = () => {
  const [question, setQuestion] = React.useState("");
  const [answer, setAnswer] = React.useState("");

  const ask = async () => {
    const res = await fetch("http://localhost:8000/rag/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });

    const data = await res.json();
    setAnswer(data.answer || "No answer.");
  };

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h2 className="text-2xl font-semibold mb-2">Knowledge Search</h2>
      <textarea
        rows={4}
        className="w-full border border-gray-300 p-2.5 rounded text-xs mb-3"
        placeholder="Ask something..."
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
      />

      <button
        onClick={ask}
        className="px-4 py-1.5 bg-blue-500 text-white rounded text-xs"
      >
        Search
      </button>

      {answer && (
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded text-xs">
          {answer}
        </div>
      )}
    </div>
  );
};

////////////////////////////////////////////////////////////////////////////////
// DASHBOARD
////////////////////////////////////////////////////////////////////////////////
const Dashboard = () => {
  return (
    <div className="p-8">
      <h2 className="text-2xl font-semibold mb-2">Welcome Back</h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
        <div className="p-4 bg-white rounded border hover:shadow cursor-pointer">
          <h3 className="text-sm font-medium">Live Transcription</h3>
        </div>

        <div className="p-4 bg-white rounded border hover:shadow cursor-pointer">
          <h3 className="text-sm font-medium">Upload & Analyze</h3>
        </div>

        <div className="p-4 bg-white rounded border hover:shadow cursor-pointer">
          <h3 className="text-sm font-medium">Search with RAG</h3>
        </div>
      </div>
    </div>
  );
};

////////////////////////////////////////////////////////////////////////////////
// MAIN APP
////////////////////////////////////////////////////////////////////////////////
function MainUI() {
  const [page, setPage] = React.useState("dashboard");

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar currentPage={page} setPage={setPage} />

      <div className="flex-1 flex flex-col">
        <Topbar title={page.toUpperCase()} />

        <div className="flex-1 overflow-auto">
          {page === "dashboard" && <Dashboard />}
          {page === "transcribe" && <TranscriptionCenter />}
          {page === "rag" && <RagUI />}
          {page === "settings" && (
            <div className="p-8">Settings coming soon...</div>
          )}
        </div>
      </div>
    </div>
  );
}

window.MainUI = MainUI;
