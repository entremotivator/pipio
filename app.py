import time
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

import requests
import streamlit as st

# ----------------- Configuration -----------------

PIPIO_GENERATE_URL = "https://generate.pipio.ai/single-clip"
PIPIO_JOB_STATUS_URL = "https://generate.pipio.ai/jobs/{job_id}"

MAX_POLL_SECONDS = 300
POLL_INTERVAL_SECONDS = 5

# Matrix theme colors
MATRIX_GREEN = "#00FF41"
MATRIX_DARK_GREEN = "#008F11"
MATRIX_BG = "#0D0208"
MATRIX_ACCENT = "#003B00"

# ----------------- Custom CSS -----------------

def apply_matrix_theme():
    st.markdown("""
    <style>
        /* Global Matrix Theme */
        @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');
        
        .stApp {
            background: linear-gradient(180deg, #0D0208 0%, #001a00 100%);
            font-family: 'Share Tech Mono', monospace;
        }
        
        /* Headers with glowing effect */
        h1, h2, h3 {
            color: #00FF41 !important;
            text-shadow: 0 0 10px #00FF41, 0 0 20px #00FF41, 0 0 30px #00FF41;
            font-family: 'Share Tech Mono', monospace !important;
            letter-spacing: 2px;
        }
        
        /* Main title animation */
        .main-title {
            font-size: 3em;
            text-align: center;
            color: #00FF41;
            text-shadow: 0 0 10px #00FF41, 0 0 20px #00FF41, 0 0 40px #00FF41;
            animation: glow 2s ease-in-out infinite alternate;
            margin-bottom: 20px;
        }
        
        @keyframes glow {
            from { text-shadow: 0 0 5px #00FF41, 0 0 10px #00FF41, 0 0 15px #00FF41; }
            to { text-shadow: 0 0 10px #00FF41, 0 0 20px #00FF41, 0 0 40px #00FF41, 0 0 50px #00FF41; }
        }
        
        /* Input fields */
        .stTextInput input, .stTextArea textarea, .stSelectbox select {
            background-color: rgba(0, 59, 0, 0.3) !important;
            color: #00FF41 !important;
            border: 1px solid #00FF41 !important;
            font-family: 'Share Tech Mono', monospace !important;
        }
        
        /* Buttons */
        .stButton button {
            background: linear-gradient(45deg, #003B00, #008F11) !important;
            color: #00FF41 !important;
            border: 2px solid #00FF41 !important;
            font-family: 'Share Tech Mono', monospace !important;
            font-weight: bold !important;
            transition: all 0.3s ease !important;
            text-shadow: 0 0 5px #00FF41;
        }
        
        .stButton button:hover {
            background: linear-gradient(45deg, #008F11, #00FF41) !important;
            box-shadow: 0 0 20px #00FF41 !important;
            transform: scale(1.05);
        }
        
        /* Sidebar */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #001a00 0%, #0D0208 100%);
            border-right: 2px solid #00FF41;
        }
        
        [data-testid="stSidebar"] * {
            color: #00FF41 !important;
        }
        
        /* Containers */
        .stContainer, div[data-testid="stExpander"] {
            background-color: rgba(0, 59, 0, 0.2) !important;
            border: 1px solid #008F11 !important;
            border-radius: 8px !important;
            box-shadow: 0 0 15px rgba(0, 255, 65, 0.2);
        }
        
        /* Status messages */
        .stSuccess {
            background-color: rgba(0, 143, 17, 0.2) !important;
            color: #00FF41 !important;
            border-left: 4px solid #00FF41 !important;
        }
        
        .stError {
            background-color: rgba(139, 0, 0, 0.2) !important;
            color: #FF4141 !important;
            border-left: 4px solid #FF4141 !important;
        }
        
        .stWarning {
            background-color: rgba(255, 165, 0, 0.2) !important;
            color: #FFA500 !important;
            border-left: 4px solid #FFA500 !important;
        }
        
        .stInfo {
            background-color: rgba(0, 59, 0, 0.2) !important;
            color: #00FF41 !important;
            border-left: 4px solid #00FF41 !important;
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            background-color: rgba(0, 59, 0, 0.3);
            border: 1px solid #00FF41;
        }
        
        .stTabs [data-baseweb="tab"] {
            color: #00FF41 !important;
            font-family: 'Share Tech Mono', monospace !important;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: rgba(0, 143, 17, 0.5) !important;
            border-bottom: 3px solid #00FF41 !important;
        }
        
        /* Progress bars */
        .stProgress > div > div {
            background-color: #00FF41 !important;
        }
        
        /* Metrics */
        [data-testid="stMetricValue"] {
            color: #00FF41 !important;
            font-size: 2em !important;
            text-shadow: 0 0 10px #00FF41;
        }
        
        /* Code blocks */
        .stCodeBlock {
            background-color: rgba(0, 59, 0, 0.3) !important;
            border: 1px solid #00FF41 !important;
        }
        
        code {
            color: #00FF41 !important;
            font-family: 'Share Tech Mono', monospace !important;
        }
        
        /* Captions */
        .caption {
            color: #008F11 !important;
            font-family: 'Share Tech Mono', monospace !important;
        }
        
        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 10px;
            background-color: #0D0208;
        }
        
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(180deg, #003B00, #00FF41);
            border-radius: 5px;
        }
        
        /* Matrix rain effect container */
        .matrix-rain {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: -1;
            opacity: 0.1;
        }
        
        /* Job cards */
        .job-card {
            background: rgba(0, 59, 0, 0.3);
            border: 1px solid #00FF41;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            box-shadow: 0 0 10px rgba(0, 255, 65, 0.3);
            transition: all 0.3s ease;
        }
        
        .job-card:hover {
            box-shadow: 0 0 20px rgba(0, 255, 65, 0.5);
            transform: translateX(5px);
        }
        
        /* Stats cards */
        .stat-card {
            background: linear-gradient(135deg, rgba(0, 59, 0, 0.4), rgba(0, 143, 17, 0.2));
            border: 2px solid #00FF41;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 0 15px rgba(0, 255, 65, 0.3);
        }
    </style>
    """, unsafe_allow_html=True)


# ----------------- Helper Functions -----------------

def _headers(api_key: str) -> Dict[str, str]:
    return {
        "Authorization": f"Key {api_key}",
        "Content-Type": "application/json",
    }


def call_pipio_generate(
    api_key: str,
    actor_id: str,
    voice_id: str,
    script: str,
    aspect_ratio: Optional[str] = None,
    resolution: Optional[str] = None,
    extras: Optional[Dict[str, Any]] = None,
) -> requests.Response:
    """Call Pipio API to generate a video."""
    payload: Dict[str, Any] = {
        "actorId": actor_id,
        "voiceId": voice_id,
        "script": script.strip(),
    }

    if aspect_ratio:
        payload["aspectRatio"] = aspect_ratio
    if resolution:
        payload["resolution"] = resolution
    if extras:
        payload.update(extras)

    return requests.post(
        PIPIO_GENERATE_URL,
        json=payload,
        headers=_headers(api_key),
        timeout=60,
    )


def poll_job_status(api_key: str, job_id: str) -> Dict[str, Any]:
    """Poll job status until completion or timeout."""
    status_url = PIPIO_JOB_STATUS_URL.format(job_id=job_id)
    start = time.time()
    last_data: Dict[str, Any] = {}
    
    progress_bar = st.progress(0)
    status_text = st.empty()

    while True:
        elapsed = time.time() - start
        progress = min(elapsed / MAX_POLL_SECONDS, 1.0)
        progress_bar.progress(progress)
        
        if elapsed > MAX_POLL_SECONDS:
            status_text.warning("⏰ Polling timeout reached")
            break

        try:
            r = requests.get(status_url, headers=_headers(api_key), timeout=30)
        except requests.RequestException as e:
            status_text.error(f"Network error: {e}")
            break

        if r.status_code != 200:
            status_text.error(f"Status endpoint error: {r.status_code}")
            try:
                last_data = r.json()
            except Exception:
                last_data = {"raw_text": r.text}
            break

        try:
            data = r.json()
        except Exception:
            data = {"raw_text": r.text}

        last_data = data
        status = str(
            data.get("status")
            or data.get("state")
            or data.get("jobStatus")
            or ""
        ).lower()
        
        status_text.info(f"Status: {status.upper()} | Elapsed: {int(elapsed)}s")

        if status in {"completed", "finished", "success", "done", "complete"}:
            progress_bar.progress(1.0)
            status_text.success("✅ Job completed!")
            break
        if status in {"failed", "error"}:
            status_text.error("❌ Job failed")
            break

        time.sleep(POLL_INTERVAL_SECONDS)
    
    progress_bar.empty()
    status_text.empty()
    return last_data


def extract_job_id(initial: Dict[str, Any]) -> Optional[str]:
    """Extract job ID from API response."""
    candidates = ["jobId", "id", "videoId", "taskId", "job_id"]
    
    for key in candidates:
        if key in initial and isinstance(initial[key], (str, int)):
            return str(initial[key])

    for field in ("data", "result", "response"):
        nested = initial.get(field)
        if isinstance(nested, dict):
            for key in candidates:
                if key in nested and isinstance(nested[key], (str, int)):
                    return str(nested[key])

    return None


def extract_video_url(payload: Dict[str, Any]) -> Optional[str]:
    """Extract video URL from API response."""
    candidates = ["url", "videoUrl", "downloadUrl", "mp4Url", "video_url", "output_url"]

    for key in candidates:
        val = payload.get(key)
        if isinstance(val, str) and val.startswith("http"):
            return val

    for field in ("data", "result", "output", "video"):
        nested = payload.get(field)
        if isinstance(nested, dict):
            for key in candidates:
                val = nested.get(key)
                if isinstance(val, str) and val.startswith("http"):
                    return val

    return None


def init_session_state():
    """Initialize session state variables."""
    if "pipio_jobs" not in st.session_state:
        st.session_state["pipio_jobs"]: List[Dict[str, Any]] = []
    if "total_videos" not in st.session_state:
        st.session_state["total_videos"] = 0
    if "successful_videos" not in st.session_state:
        st.session_state["successful_videos"] = 0
    if "failed_videos" not in st.session_state:
        st.session_state["failed_videos"] = 0
    if "favorites" not in st.session_state:
        st.session_state["favorites"] = []


def add_job_to_history(
    job_id: Optional[str],
    status: str,
    script_preview: str,
    video_url: Optional[str],
    actor_id: str = "",
    voice_id: str = "",
):
    """Add job to history with metadata."""
    jobs = st.session_state["pipio_jobs"]
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    job_data = {
        "job_id": job_id or "N/A",
        "status": status,
        "script": script_preview,
        "video_url": video_url,
        "timestamp": timestamp,
        "actor_id": actor_id,
        "voice_id": voice_id,
    }
    
    jobs.insert(0, job_data)
    
    # Update stats
    st.session_state["total_videos"] += 1
    if status.lower() in {"completed", "finished", "done", "success", "complete"}:
        st.session_state["successful_videos"] += 1
    elif status.lower() in {"failed", "error"}:
        st.session_state["failed_videos"] += 1
    
    # Cap history at 50
    if len(jobs) > 50:
        del jobs[50:]


def script_templates() -> Dict[str, str]:
    """Predefined script templates."""
    return {
        "Welcome / Intro": 
            "Welcome to our channel! In this short video, I'll walk you through what we do and how you can get started today. "
            "We're excited to have you here and can't wait to show you everything we have to offer.",
        
        "Product Explainer":
            "In this video, you'll learn what our product does, who it's for, and how it can save you time every week. "
            "Our innovative solution helps thousands of users streamline their workflow and boost productivity.",
        
        "Training Snippet":
            "In this training, we'll cover one core concept step-by-step so you can apply it immediately in your work. "
            "By the end of this session, you'll have practical knowledge you can use right away.",
        
        "Sales Pitch":
            "Are you tired of spending hours on tasks that could be automated? Our solution is here to help. "
            "Join thousands of satisfied customers who have transformed their business with our platform.",
        
        "Tutorial Introduction":
            "Hello and welcome to this tutorial! Today we're going to dive deep into the features that make this tool essential. "
            "Follow along as I show you step-by-step how to get the most out of every feature.",
        
        "Motivational Message":
            "Every great achievement starts with a single step. Today is your day to take that step forward. "
            "Believe in yourself, stay focused, and remember that success is built one day at a time.",
        
        "Company Announcement":
            "We're thrilled to announce some exciting news that will change the way you work with us. "
            "This update brings new features, improved performance, and better user experience for everyone.",
        
        "FAQ Response":
            "This is one of our most frequently asked questions, so let me break it down for you clearly. "
            "The answer is simpler than you might think, and I'll explain everything you need to know.",
    }


def job_status_badge(status: str) -> str:
    """Generate status badge with emoji."""
    s = status.lower()
    if s in {"completed", "finished", "done", "success", "complete"}:
        return "✅ COMPLETED"
    if s in {"queued", "pending", "submitted"}:
        return "🕒 QUEUED"
    if s in {"processing", "running", "in_progress"}:
        return "⚙️ PROCESSING"
    if s in {"failed", "error"}:
        return "❌ FAILED"
    return f"ℹ️ {status.upper() if status else 'UNKNOWN'}"


def export_history_json():
    """Export job history as JSON."""
    jobs = st.session_state.get("pipio_jobs", [])
    return json.dumps(jobs, indent=2)


# ----------------- Main UI -----------------

def main():
    init_session_state()
    apply_matrix_theme()
    
    st.set_page_config(
        page_title="PIPIO MATRIX STUDIO",
        page_icon="🎬",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    
    # Matrix-style title
    st.markdown('<h1 class="main-title">⚡ PIPIO MATRIX STUDIO ⚡</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p style="text-align: center; color: #008F11; font-size: 1.2em; margin-bottom: 30px;">'
        'NEURAL AVATAR GENERATION SYSTEM v2.0'
        '</p>',
        unsafe_allow_html=True
    )
    
    # Sidebar Configuration
    with st.sidebar:
        st.markdown("### 🔐 SYSTEM ACCESS")
        api_key = st.text_input(
            "API KEY",
            type="password",
            help="Enter your Pipio API key (Authorization: Key <API_KEY>)",
        )
        
        st.markdown("---")
        st.markdown("### ⚙️ SYSTEM CONFIGURATION")
        
        max_poll = st.slider("Max polling time (seconds)", 60, 600, MAX_POLL_SECONDS, 30)
        poll_interval = st.slider("Poll interval (seconds)", 2, 10, POLL_INTERVAL_SECONDS, 1)
        
        st.markdown("---")
        st.markdown("### 🎨 DISPLAY OPTIONS")
        show_raw = st.checkbox("Show raw JSON responses", value=False)
        show_stats = st.checkbox("Show statistics dashboard", value=True)
        dry_run = st.checkbox("Dry run mode (no API calls)", value=False)
        
        st.markdown("---")
        st.markdown("### 📊 SESSION STATS")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total", st.session_state.get("total_videos", 0))
        with col2:
            st.metric("Success", st.session_state.get("successful_videos", 0))
        
        st.markdown("---")
        st.markdown("### 💡 PRO TIPS")
        st.markdown(
            "• Keep scripts **15-45 seconds** for optimal results\n\n"
            "• Test with same actor/voice for consistency\n\n"
            "• Use templates as starting points\n\n"
            "• Check job history for reusable content"
        )
        
        if st.button("🗑️ Clear History"):
            st.session_state["pipio_jobs"] = []
            st.session_state["total_videos"] = 0
            st.session_state["successful_videos"] = 0
            st.session_state["failed_videos"] = 0
            st.rerun()
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🎬 GENERATE", "📜 HISTORY", "📊 ANALYTICS", "⚙️ ADVANCED"])
    
    # TAB 1: Generate Video
    with tab1:
        st.markdown("### STEP 1: AVATAR CONFIGURATION")
        
        col1, col2 = st.columns(2)
        with col1:
            actor_id = st.text_input(
                "🎭 Actor ID",
                placeholder="e.g., actor_xyz123",
                help="Unique identifier for the avatar actor"
            )
        with col2:
            voice_id = st.text_input(
                "🎤 Voice ID",
                placeholder="e.g., voice_abc456",
                help="Unique identifier for the voice profile"
            )
        
        st.markdown("### STEP 2: SCRIPT CREATION")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            template_choice = st.selectbox(
                "📝 Template",
                options=["Custom"] + list(script_templates().keys()),
                index=0,
            )
        with col2:
            use_template = st.checkbox("Apply", value=False, help="Load selected template")
        
        script_text = st.text_area(
            "Script Content",
            value="",
            height=250,
            placeholder="Enter your script here... (Tip: Keep it between 15-45 seconds for best results)",
            help="The text your avatar will speak"
        )
        
        if template_choice != "Custom" and use_template:
            script_text = script_templates()[template_choice]
            st.success(f"✅ Template '{template_choice}' loaded")
        
        # Character counter
        char_count = len(script_text)
        word_count = len(script_text.split())
        estimated_duration = word_count / 2.5  # Rough estimate: 150 words per minute
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Characters", char_count)
        with col2:
            st.metric("Words", word_count)
        with col3:
            st.metric("Est. Duration", f"{estimated_duration:.0f}s")
        
        st.markdown("### STEP 3: VIDEO SETTINGS")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            aspect_ratio = st.selectbox(
                "📐 Aspect Ratio",
                ["16:9", "9:16", "1:1", "4:3"],
                index=0,
                help="Video dimensions ratio"
            )
        with col2:
            resolution = st.selectbox(
                "🎥 Resolution",
                ["1080p", "720p", "480p"],
                index=0,
                help="Video quality"
            )
        with col3:
            fps = st.selectbox(
                "🎞️ Frame Rate",
                ["24", "30", "60"],
                index=1,
                help="Frames per second"
            )
        
        st.markdown("### STEP 4: ADVANCED OPTIONS")
        
        with st.expander("🎨 Visual Settings", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                bg_color = st.color_picker(
                    "Background Color",
                    "#000000",
                    help="Choose background color"
                )
                bg_blur = st.slider("Background Blur", 0, 100, 0, 5)
            with col2:
                brightness = st.slider("Brightness", 0, 200, 100, 5)
                contrast = st.slider("Contrast", 0, 200, 100, 5)
        
        with st.expander("🗣️ Audio Settings", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                speaking_rate = st.slider(
                    "Speaking Speed",
                    0.5, 2.0, 1.0, 0.05,
                    help="Adjust voice speed (1.0 = normal)"
                )
                pitch = st.slider("Voice Pitch", 0.5, 2.0, 1.0, 0.05)
            with col2:
                volume = st.slider("Volume", 0, 150, 100, 5)
                enable_captions = st.checkbox("Enable Captions", value=False)
        
        with st.expander("🎬 Production Settings", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                add_intro = st.checkbox("Add Intro Sequence", value=False)
                add_outro = st.checkbox("Add Outro Sequence", value=False)
            with col2:
                add_watermark = st.checkbox("Add Watermark", value=False)
                add_bgm = st.checkbox("Add Background Music", value=False)
        
        # Build extras dictionary
        extras: Dict[str, Any] = {}
        if bg_color != "#000000":
            extras["backgroundColor"] = bg_color
        if speaking_rate != 1.0:
            extras["speakingRate"] = speaking_rate
        if enable_captions:
            extras["captions"] = True
        if pitch != 1.0:
            extras["pitch"] = pitch
        if volume != 100:
            extras["volume"] = volume / 100
        if bg_blur > 0:
            extras["backgroundBlur"] = bg_blur
        if brightness != 100:
            extras["brightness"] = brightness / 100
        if contrast != 100:
            extras["contrast"] = contrast / 100
        
        st.markdown("### STEP 5: GENERATION")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            generate_btn = st.button("🚀 GENERATE VIDEO", type="primary", use_container_width=True)
        with col2:
            preview_btn = st.button("👁️ PREVIEW CONFIG", use_container_width=True)
        with col3:
            save_script_btn = st.button("💾 SAVE SCRIPT", use_container_width=True)
        with col4:
            reset_btn = st.button("🔄 RESET", use_container_width=True)
        
        if preview_btn:
            st.json({
                "actorId": actor_id,
                "voiceId": voice_id,
                "script": script_text[:100] + "..." if len(script_text) > 100 else script_text,
                "aspectRatio": aspect_ratio,
                "resolution": resolution,
                "fps": fps,
                **extras
            })
        
        if save_script_btn:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            script_filename = f"script_{timestamp}.txt"
            st.download_button(
                "Download Script",
                script_text,
                file_name=script_filename,
                mime="text/plain"
            )
        
        if reset_btn:
            st.rerun()
        
        # Generation logic
        status_container = st.container()
        video_container = st.container()
        
        if generate_btn:
            with status_container:
                if not api_key:
                    st.error("⚠️ API KEY REQUIRED - Enter your key in the sidebar")
                    st.stop()
                if not actor_id or not voice_id:
                    st.error("⚠️ ACTOR ID and VOICE ID are required")
                    st.stop()
                if not script_text.strip():
                    st.error("⚠️ SCRIPT cannot be empty")
                    st.stop()
                
                preview = (script_text.strip()[:120] + "...") if len(script_text) > 120 else script_text.strip()
                
                if dry_run:
                    st.info("🔧 DRY RUN MODE - No API calls will be made")
                    payload_preview = {
                        "actorId": actor_id,
                        "voiceId": voice_id,
                        "script": script_text.strip(),
                        "aspectRatio": aspect_ratio,
                        "resolution": resolution,
                        "fps": fps,
                        **extras,
                    }
                    st.json(payload_preview)
                    add_job_to_history(
                        job_id=None,
                        status="DRY RUN",
                        script_preview=preview,
                        video_url=None,
                        actor_id=actor_id,
                        voice_id=voice_id
                    )
                    st.stop()
                
                with st.spinner("📡 Connecting to Pipio Neural Network..."):
                    try:
                        resp = call_pipio_generate(
                            api_key=api_key,
                            actor_id=actor_id,
                            voice_id=voice_id,
                            script=script_text,
                            aspect_ratio=aspect_ratio,
                            resolution=resolution,
                            extras=extras or None,
                        )
                    except requests.RequestException as e:
                        st.error(f"🔴 NETWORK ERROR: {e}")
                        st.stop()
                
                if resp.status_code not in (200, 201, 202):
                    st.error(f"🔴 API ERROR: HTTP {resp.status_code}")
                    if show_raw:
                        with st.expander("Error Response", expanded=True):
                            try:
                                st.json(resp.json())
                            except Exception:
                                st.code(resp.text)
                    add_job_to_history(
                        job_id=None,
                        status=f"HTTP {resp.status_code}",
                        script_preview=preview,
                        video_url=None,
                        actor_id=actor_id,
                        voice_id=voice_id
                    )
                    st.stop()
                
                try:
                    initial_json = resp.json()
                except Exception:
                    initial_json = {"raw_text": resp.text}
                
                if show_raw:
                    with st.expander("Initial API Response", expanded=False):
                        st.json(initial_json)
                
                job_id = extract_job_id(initial_json)
                immediate_url = extract_video_url(initial_json)
                
                if immediate_url:
                    st.success("✅ VIDEO GENERATED SUCCESSFULLY")
                    with video_container:
                        st.video(immediate_url)
                        st.download_button(
                            "⬇️ Download Video",
                            data=requests.get(immediate_url).content,
                            file_name=f"pipio_video_{job_id or 'instant'}.mp4",
                            mime="video/mp4"
                        )
                    add_job_to_history(
                        job_id=job_id,
                        status="completed",
                        script_preview=preview,
                        video_url=immediate_url,
                        actor_id=actor_id,
                        voice_id=voice_id
                    )
                
                elif job_id:
                    st.info(f"⚙️ JOB CREATED: {job_id}")
                    st.markdown("---")
                    job_payload = poll_job_status(api_key, job_id)
                    
                    if show_raw:
                        with st.expander("Final Job Payload", expanded=False):
                            st.json(job_payload)
                    
                    final_status = str(
                        job_payload.get("status")
                        or job_payload.get("state")
                        or job_payload.get("jobStatus")
                        or "unknown"
                    )
                    video_url = extract_video_url(job_payload)
                    
                    if video_url:
                        st.success(f"✅ JOB {job_id} COMPLETED")
                        with video_container:
                            st.video(video_url)
                            try:
                                video_data = requests.get(video_url).content
                                st.download_button(
                                    "⬇️ Download Video",
                                    data=video_data,
                                    file_name=f"pipio_video_{job_id}.mp4",
                                    mime="video/mp4"
                                )
                            except:
                                st.warning("Download unavailable")
                    else:
                        st.warning("⚠️ Job completed but no video URL detected")
                    
                    add_job_to_history(
                        job_id=job_id,
                        status=final_status,
                        script_preview=preview,
                        video_url=video_url,
                        actor_id=actor_id,
                        voice_id=voice_id
                    )
                
                else:
                    st.warning("⚠️ Could not detect job ID or video URL")
                    st.info("Check the API response and adjust extraction functions")
                    add_job_to_history(
                        job_id=None,
                        status="UNKNOWN",
                        script_preview=preview,
                        video_url=None,
                        actor_id=actor_id,
                        voice_id=voice_id
                    )
    
    # TAB 2: History
    with tab2:
        st.markdown("### 📜 GENERATION HISTORY")
        
        jobs = st.session_state.get("pipio_jobs", [])
        
        if not jobs:
            st.info("💫 No generation history yet. Create your first video in the GENERATE tab!")
        else:
            # Filter options
            col1, col2, col3 = st.columns(3)
            with col1:
                filter_status = st.multiselect(
                    "Filter by Status",
                    ["completed", "failed", "processing", "queued", "unknown"],
                    default=[]
                )
            with col2:
                search_term = st.text_input("🔍 Search scripts", "")
            with col3:
                sort_order = st.selectbox("Sort by", ["Newest First", "Oldest First"])
            
            # Export button
            if st.button("📥 Export History as JSON"):
                json_data = export_history_json()
                st.download_button(
                    "Download JSON",
                    json_data,
                    file_name=f"pipio_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            
            st.markdown("---")
            
            # Filter jobs
            filtered_jobs = jobs
            if filter_status:
                filtered_jobs = [j for j in filtered_jobs if j.get("status", "").lower() in filter_status]
            if search_term:
                filtered_jobs = [j for j in filtered_jobs if search_term.lower() in j.get("script", "").lower()]
            if sort_order == "Oldest First":
                filtered_jobs = list(reversed(filtered_jobs))
            
            # Display jobs
            for idx, job in enumerate(filtered_jobs):
                with st.container():
                    st.markdown(f'<div class="job-card">', unsafe_allow_html=True)
                    
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.markdown(f"**Job ID:** `{job.get('job_id', 'N/A')}`")
                        st.markdown(f"**Status:** {job_status_badge(job.get('status', 'unknown'))}")
                    with col2:
                        st.markdown(f"**Timestamp:**")
                        st.caption(job.get('timestamp', 'N/A'))
                    with col3:
                        st.markdown(f"**Actor:** `{job.get('actor_id', 'N/A')[:15]}...`")
                        st.markdown(f"**Voice:** `{job.get('voice_id', 'N/A')[:15]}...`")
                    
                    with st.expander("📄 View Script", expanded=False):
                        st.text(job.get('script', 'N/A'))
                    
                    video_url = job.get('video_url')
                    if video_url:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if st.button(f"▶️ Play", key=f"play_{idx}"):
                                st.session_state[f"show_video_{idx}"] = True
                        with col2:
                            try:
                                video_data = requests.get(video_url).content
                                st.download_button(
                                    "⬇️ Download",
                                    data=video_data,
                                    file_name=f"pipio_{job.get('job_id', 'video')}.mp4",
                                    mime="video/mp4",
                                    key=f"download_{idx}"
                                )
                            except:
                                st.caption("Download unavailable")
                        with col3:
                            if st.button(f"⭐ Favorite", key=f"fav_{idx}"):
                                if job not in st.session_state.get("favorites", []):
                                    st.session_state.setdefault("favorites", []).append(job)
                                    st.success("Added to favorites!")
                        
                        if st.session_state.get(f"show_video_{idx}", False):
                            st.video(video_url)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown("---")
    
    # TAB 3: Analytics
    with tab3:
        st.markdown("### 📊 ANALYTICS DASHBOARD")
        
        if show_stats:
            jobs = st.session_state.get("pipio_jobs", [])
            total = st.session_state.get("total_videos", 0)
            successful = st.session_state.get("successful_videos", 0)
            failed = st.session_state.get("failed_videos", 0)
            
            # Stats cards
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown('<div class="stat-card">', unsafe_allow_html=True)
                st.metric("Total Videos", total)
                st.markdown('</div>', unsafe_allow_html=True)
            with col2:
                st.markdown('<div class="stat-card">', unsafe_allow_html=True)
                st.metric("Successful", successful, delta=f"{(successful/total*100) if total > 0 else 0:.1f}%")
                st.markdown('</div>', unsafe_allow_html=True)
            with col3:
                st.markdown('<div class="stat-card">', unsafe_allow_html=True)
                st.metric("Failed", failed, delta=f"{(failed/total*100) if total > 0 else 0:.1f}%", delta_color="inverse")
                st.markdown('</div>', unsafe_allow_html=True)
            with col4:
                st.markdown('<div class="stat-card">', unsafe_allow_html=True)
                success_rate = (successful / total * 100) if total > 0 else 0
                st.metric("Success Rate", f"{success_rate:.1f}%")
                st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Most used actors/voices
            if jobs:
                st.markdown("### 🎭 Most Used Configurations")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Top Actors**")
                    actor_counts = {}
                    for job in jobs:
                        actor = job.get('actor_id', 'Unknown')
                        actor_counts[actor] = actor_counts.get(actor, 0) + 1
                    
                    sorted_actors = sorted(actor_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                    for actor, count in sorted_actors:
                        st.markdown(f"• `{actor[:30]}...` - {count} videos")
                
                with col2:
                    st.markdown("**Top Voices**")
                    voice_counts = {}
                    for job in jobs:
                        voice = job.get('voice_id', 'Unknown')
                        voice_counts[voice] = voice_counts.get(voice, 0) + 1
                    
                    sorted_voices = sorted(voice_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                    for voice, count in sorted_voices:
                        st.markdown(f"• `{voice[:30]}...` - {count} videos")
                
                st.markdown("---")
                
                # Recent activity
                st.markdown("### ⏱️ Recent Activity")
                recent_jobs = jobs[:10]
                for job in recent_jobs:
                    status = job_status_badge(job.get('status', 'unknown'))
                    timestamp = job.get('timestamp', 'N/A')
                    job_id = job.get('job_id', 'N/A')
                    st.markdown(f"• **{timestamp}** - {status} - Job: `{job_id}`")
        else:
            st.info("Enable 'Show statistics dashboard' in the sidebar to view analytics")
    
    # TAB 4: Advanced
    with tab4:
        st.markdown("### ⚙️ ADVANCED CONFIGURATION")
        
        st.markdown("#### 🔧 API Endpoints")
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Generate URL", value=PIPIO_GENERATE_URL, disabled=True)
        with col2:
            st.text_input("Job Status URL", value=PIPIO_JOB_STATUS_URL, disabled=True)
        
        st.markdown("---")
        st.markdown("#### 📚 Documentation & Resources")
        
        st.markdown("""
        **Pipio API Resources:**
        - [Official Documentation](https://docs.pipio.ai)
        - [API Reference](https://docs.pipio.ai/api)
        - [Actor Library](https://pipio.ai/actors)
        - [Voice Library](https://pipio.ai/voices)
        
        **Quick Start Guide:**
        1. Obtain API key from Pipio dashboard
        2. Select an actor and voice from the library
        3. Write or select a script template
        4. Configure video settings
        5. Generate and download your video
        
        **Best Practices:**
        - Keep scripts concise (15-45 seconds)
        - Test different actor/voice combinations
        - Use high resolution for professional content
        - Enable captions for accessibility
        - Save successful configurations for reuse
        """)
        
        st.markdown("---")
        st.markdown("#### 🧪 Experimental Features")
        
        col1, col2 = st.columns(2)
        with col1:
            batch_mode = st.checkbox("Batch Generation Mode", value=False)
            if batch_mode:
                st.info("Generate multiple videos from a list of scripts")
        
        with col2:
            auto_retry = st.checkbox("Auto-retry on Failure", value=False)
            if auto_retry:
                retry_count = st.number_input("Max Retries", 1, 5, 3)
        
        st.markdown("---")
        st.markdown("#### 💾 Import/Export")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 Import Configuration"):
                st.info("Upload a JSON configuration file (feature in development)")
        
        with col2:
            if st.button("📤 Export Configuration"):
                config = {
                    "api_url": PIPIO_GENERATE_URL,
                    "max_poll_seconds": max_poll,
                    "poll_interval": poll_interval,
                    "total_videos": st.session_state.get("total_videos", 0),
                    "successful_videos": st.session_state.get("successful_videos", 0),
                }
                st.download_button(
                    "Download Config",
                    json.dumps(config, indent=2),
                    file_name="pipio_config.json",
                    mime="application/json"
                )


if __name__ == "__main__":
    main()
