import time
from typing import Optional, Dict, Any, List

import requests
import streamlit as st

# ----------------- Basic Config -----------------

PIPIO_GENERATE_URL = "https://generate.pipio.ai/single-clip"
# Adjust once you confirm the exact job status URL in Pipio docs:
PIPIO_JOB_STATUS_URL = "https://generate.pipio.ai/jobs/{job_id}"

MAX_POLL_SECONDS = 180
POLL_INTERVAL_SECONDS = 5


# ----------------- Helpers -----------------

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
    """
    Hit `GET /jobs/{job_id}` until completion or timeout.
    Exact schema may differ; inspect JSON in the UI and tweak mapping as needed.[web:31][web:34]
    """
    status_url = PIPIO_JOB_STATUS_URL.format(job_id=job_id)
    start = time.time()
    last_data: Dict[str, Any] = {}

    while True:
        if time.time() - start > MAX_POLL_SECONDS:
            st.warning("⏰ Timed out while waiting for job to complete.")
            break

        try:
            r = requests.get(status_url, headers=_headers(api_key), timeout=30)
        except requests.RequestException as e:
            st.error(f"Error while polling job status: {e}")
            break

        if r.status_code != 200:
            st.error(f"Status endpoint error: {r.status_code}")
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

        if status in {"completed", "finished", "success", "done", "complete"}:
            break
        if status in {"failed", "error"}:
            st.error("Job reported a failure state.")
            break

        time.sleep(POLL_INTERVAL_SECONDS)

    return last_data


def extract_job_id(initial: Dict[str, Any]) -> Optional[str]:
    """
    Guess where Pipio puts the job ID in the initial /single-clip response.
    Adjust once you see a real payload.[web:31][web:34]
    """
    candidates = ["jobId", "id", "videoId", "taskId"]
    for key in candidates:
        if key in initial and isinstance(initial[key], (str, int)):
            return str(initial[key])

    # Nested
    for field in ("data", "result"):
        nested = initial.get(field)
        if isinstance(nested, dict):
            for key in candidates:
                if key in nested and isinstance(nested[key], (str, int)):
                    return str(nested[key])

    return None


def extract_video_url(payload: Dict[str, Any]) -> Optional[str]:
    """
    Try common fields for a URL; supports nested structures.
    """
    candidates = ["url", "videoUrl", "downloadUrl", "mp4Url"]

    for key in candidates:
        val = payload.get(key)
        if isinstance(val, str) and val.startswith("http"):
            return val

    for field in ("data", "result", "output"):
        nested = payload.get(field)
        if isinstance(nested, dict):
            for key in candidates:
                val = nested.get(key)
                if isinstance(val, str) and val.startswith("http"):
                    return val

    return None


def init_session_state():
    if "pipio_jobs" not in st.session_state:
        st.session_state["pipio_jobs"]: List[Dict[str, Any]] = []


def add_job_to_history(
    job_id: Optional[str],
    status: str,
    script_preview: str,
    video_url: Optional[str],
):
    jobs = st.session_state["pipio_jobs"]
    jobs.insert(
        0,
        {
            "job_id": job_id,
            "status": status,
            "script": script_preview,
            "video_url": video_url,
        },
    )
    # cap history
    if len(jobs) > 20:
        del jobs[20:]


def script_templates() -> Dict[str, str]:
    return {
        "Welcome / Intro":
            "Welcome to our channel! In this short video, I'll walk you through what we do and how you can get started today.",
        "Product explainer":
            "In this video, you'll learn what our product does, who it's for, and how it can save you time every week.",
        "Training snippet":
            "In this training, we'll cover one core concept step‑by‑step so you can apply it immediately in your work.",
    }


def job_status_badge(status: str) -> str:
    s = status.lower()
    if s in {"completed", "finished", "done", "success", "complete"}:
        return "✅ Completed"
    if s in {"queued", "pending", "submitted"}:
        return "🕒 Queued"
    if s in {"processing", "running", "in_progress"}:
        return "⚙️ Processing"
    if s in {"failed", "error"}:
        return "❌ Failed"
    return f"ℹ️ {status or 'Unknown'}"


# ----------------- UI -----------------

init_session_state()

st.set_page_config(
    page_title="Pipio Avatar Studio",
    page_icon="🎬",
    layout="wide",
)

st.title("🎬 Pipio Avatar Studio (Streamlit)")
st.caption(
    "Turn scripts into avatar videos via Pipio's API, with live job polling and a small job history.[cite:15]"
)

# Sidebar: API + global options
st.sidebar.header("API Settings")
api_key = st.sidebar.text_input(
    "PIPIO API Key",
    type="password",
    help="You can find this in your Pipio dashboard; used as `Authorization: Key <API_KEY>`.[web:30]",
)

st.sidebar.markdown("---")
st.sidebar.subheader("General Tips")
st.sidebar.markdown(
    "- Start with short scripts (15–30 seconds) while testing.\n"
    "- Reuse the same actor/voice combo to compare different scripts easily.[web:7][web:25]"
)

st.sidebar.markdown("---")
st.sidebar.subheader("Debug")
show_raw = st.sidebar.checkbox("Show raw JSON responses", value=True)
dry_run = st.sidebar.checkbox("Dry run (do not call API)", value=False)

# Main columns: left for generation, right for history
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("1. Script & Avatar")

    cols_ids = st.columns(2)
    with cols_ids[0]:
        actor_id = st.text_input(
            "Actor ID",
            placeholder="Paste actorId from Pipio",
        )
    with cols_ids[1]:
        voice_id = st.text_input(
            "Voice ID",
            placeholder="Paste voiceId from Pipio",
        )

    temp_col1, temp_col2 = st.columns([2, 1])
    with temp_col1:
        template_name = st.selectbox(
            "Script helper",
            options=["Custom"] + list(script_templates().keys()),
            index=0,
        )
    with temp_col2:
        auto_overwrite = st.checkbox("Apply template", value=False)

    default_script = (
        "Welcome to Pipio API. Let's create amazing avatar videos together with just a few lines of text."
    )
    script_value = st.text_area(
        "Script",
        value=default_script,
        height=200,
    )

    if template_name != "Custom" and auto_overwrite:
        script_value = script_templates()[template_name]
        st.info(f"Script template applied: {template_name}")

    st.subheader("2. Visual / Advanced Options")

    vis_col1, vis_col2 = st.columns(2)
    with vis_col1:
        aspect_ratio = st.selectbox("Aspect ratio", ["16:9", "9:16", "1:1"], index=0)
    with vis_col2:
        resolution = st.selectbox("Resolution", ["1080p", "720p"], index=0)

    extras: Dict[str, Any] = {}
    with st.expander("More options (optional)"):
        bg_color = st.text_input(
            "Background color (hex or keyword)",
            placeholder="#000000, #FFFFFF, transparent, etc.",
        )
        captions = st.checkbox("Enable captions (if supported)", value=False)
        speaking_rate = st.slider(
            "Speaking speed (if supported)",
            0.5,
            1.5,
            1.0,
            0.05,
        )

        if bg_color:
            extras["backgroundColor"] = bg_color
        if captions:
            extras["captions"] = True
        if speaking_rate != 1.0:
            extras["speakingRate"] = speaking_rate

    st.subheader("3. Generate & Preview")

    action_cols = st.columns([1, 1])
    with action_cols[0]:
        generate_btn = st.button("🚀 Generate Video", type="primary")
    with action_cols[1]:
        reset_btn = st.button("Reset form")

    if reset_btn:
        st.experimental_rerun()

    status_box = st.empty()
    video_holder = st.empty()

    if generate_btn:
        if not api_key:
            status_box.error("Please enter your Pipio API key in the sidebar.")
            st.stop()
        if not actor_id or not voice_id:
            status_box.error("Actor ID and Voice ID are required.")
            st.stop()
        if not script_value.strip():
            status_box.error("Script cannot be empty.")
            st.stop()

        preview = (script_value.strip()[:120] + "...") if len(script_value) > 120 else script_value.strip()

        if dry_run:
            status_box.info("Dry run enabled – payload only, no API calls.")
            payload_preview = {
                "actorId": actor_id,
                "voiceId": voice_id,
                "script": script_value.strip(),
                "aspectRatio": aspect_ratio,
                "resolution": resolution,
                **extras,
            }
            st.json(payload_preview)
            add_job_to_history(job_id=None, status="DRY RUN", script_preview=preview, video_url=None)
            st.stop()

        status_box.info("Submitting generate request to Pipio...")
        try:
            resp = call_pipio_generate(
                api_key=api_key,
                actor_id=actor_id,
                voice_id=voice_id,
                script=script_value,
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                extras=extras or None,
            )
        except requests.RequestException as e:
            status_box.error(f"Network error while calling Pipio: {e}")
            st.stop()

        if resp.status_code not in (200, 201, 202):
            status_box.error(f"Pipio returned an error: {resp.status_code}")
            if show_raw:
                with st.expander("Initial error response", expanded=True):
                    try:
                        st.json(resp.json())
                    except Exception:
                        st.code(resp.text, language="json")
            add_job_to_history(job_id=None, status=f"HTTP {resp.status_code}", script_preview=preview, video_url=None)
            st.stop()

        try:
            initial_json = resp.json()
        except Exception:
            initial_json = {"raw_text": resp.text}

        if show_raw:
            with st.expander("Initial /single-clip response", expanded=False):
                st.json(initial_json)

        job_id = extract_job_id(initial_json)
        immediate_url = extract_video_url(initial_json)

        # If API returns a finished URL immediately
        if immediate_url:
            status_box.success("Video URL returned immediately.")
            video_holder.video(immediate_url)
            add_job_to_history(job_id=job_id, status="completed", script_preview=preview, video_url=immediate_url)

        # If API is async with a jobId
        elif job_id:
            status_box.info(f"Job created (ID: {job_id}). Polling for status...")
            with st.spinner("Waiting for Pipio to finish rendering..."):
                job_payload = poll_job_status(api_key, job_id)

            if show_raw:
                with st.expander("Final job payload", expanded=False):
                    st.json(job_payload)

            final_status = str(
                job_payload.get("status")
                or job_payload.get("state")
                or job_payload.get("jobStatus")
                or "unknown"
            )
            video_url = extract_video_url(job_payload)

            if video_url:
                status_box.success(f"Job {job_id} completed – playing video.")
                video_holder.video(video_url)
            else:
                status_box.warning(
                    "Job finished but no video URL was detected.\n"
                    "Check the final payload and update `extract_video_url()` to match the actual schema."
                )

            add_job_to_history(
                job_id=job_id,
                status=final_status,
                script_preview=preview,
                video_url=video_url,
            )

        # Neither immediate URL nor job ID – user must inspect payload
        else:
            status_box.warning(
                "Could not detect a job ID or video URL in the initial response. "
                "Inspect the payload and adjust `extract_job_id()` / `extract_video_url()`."
            )
            add_job_to_history(job_id=None, status="UNKNOWN", script_preview=preview, video_url=None)

with col_right:
    st.subheader("Recent jobs this session")

    jobs = st.session_state["pipio_jobs"]
    if not jobs:
        st.info("No jobs yet. Generate a video to populate this history.")
    else:
        for j in jobs:
            job_id = j.get("job_id") or "N/A"
            status = j.get("status") or "unknown"
            video_url = j.get("video_url")
            script_preview = j.get("script") or ""

            with st.container(border=True):
                st.markdown(f"**Job:** `{job_id}`")
                st.markdown(job_status_badge(status))
                st.caption(script_preview)

                if video_url:
                    if st.button("Play", key=f"play_{job_id}_{video_url}"):
                        st.session_state["selected_video_url"] = video_url
                else:
                    st.caption("No video URL captured yet.")

        # If user clicked any "Play" button, show it below
        sel_url = st.session_state.get("selected_video_url")
        if sel_url:
            st.markdown("---")
            st.markdown("**Selected video from history**")
            st.video(sel_url)
