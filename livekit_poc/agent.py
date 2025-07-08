import asyncio
import logging
import json
import cv2
import numpy as np
from typing import Dict
from dataclasses import dataclass, field
from dotenv import load_dotenv

from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.llm import function_tool
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import groq
from livekit.rtc import VideoFrame, ArgbFrame, VideoStream, Track, TrackPublication, RemoteParticipant, DataPacket, DataPacketKind

load_dotenv()

# --- Shared Session State ---
@dataclass
class AuraContext:
    # We can add more state here later
    is_processing_video: bool = False

# --- LangChain & Tools ---
@tool
def get_procedure(component_name: str) -> str:
    """Fetches the operational procedure for a given hardware component."""
    logging.info(f"--- TOOL CALLED: get_procedure(component_name='{component_name}') ---")
    if "PSU-07B" in component_name:
        return "Procedure for PSU-07B: 1. Disconnect power. 2. Unscrew retaining bolts."
    return f"No procedure found for {component_name}."

# --- Video Processing Logic ---
async def process_video_stream(stream: VideoStream, source: rtc.VideoSource):
    async for frame_event in stream:
        buffer = frame_event.frame
        # Use the reliable .convert() method
        bgra_frame = buffer.convert(rtc.VideoBufferType.BGRA)
        np_frame = np.frombuffer(bgra_frame.data, dtype=np.uint8).reshape(
            bgra_frame.height, bgra_frame.width, 4
        )
        # Convert to grayscale and back to BGR (which is BGRA in this case)
        img_gray = cv2.cvtColor(np_frame, cv2.COLOR_BGRA2GRAY)
        img_color = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2BGR)

        # Recreate the frame for publishing
        new_frame_data = cv2.cvtColor(img_color, cv2.COLOR_BGR2BGRA)
        new_frame = VideoFrame(width=bgra_frame.width, height=bgra_frame.height,
                               buffer=ArgbFrame.from_ndarray(new_frame_data))
        source.capture_frame(new_frame)

# --- Agent Entrypoint ---
async def entrypoint(ctx: JobContext):
    logging.info("AURA Agent connected, initializing...")
    ctx.agent.voice.say("AURA is online and ready.", tts=groq.TTS()) # Greet the user

    # Setup the LangChain agent executor
    agent_executor = AgentExecutor(...) # Your LangChain setup here

    # This agent will publish its own video track for the augmented stream
    output_video = rtc.VideoSource()
    track = rtc.LocalVideoTrack.create_video_track("agent_video", output_video)
    await ctx.room.local_participant.publish_track(track)

    @ctx.room.on("track_subscribed")
    def on_track_subscribed(track: Track, pub: TrackPublication, part: RemoteParticipant):
        if track.kind == rtc.TrackKind.KIND_VIDEO:
            logging.info("User video stream subscribed, starting processing.")
            ctx.create_task(process_video_stream(VideoStream(track), output_video))

    @ctx.room.on("data_received")
    def on_data_received(data: bytes, participant, **kwargs):
        # Your data handling logic for LangChain commands here
        pass

def main():
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main()