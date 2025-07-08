import asyncio
import logging
import cv2
import numpy as np
from livekit import rtc
from livekit.agents import JobContext, WorkerOptions, cli
from dotenv import load_dotenv
load_dotenv()

# --- ADD THESE TWO LINES ---
# Enable debug logging for the underlying WebRTC library
logging.getLogger("aiortc").setLevel(logging.DEBUG)
logging.getLogger("livekit").setLevel(logging.DEBUG)

# This function remains correct
async def process_frames(video_stream: rtc.VideoStream, output_source: rtc.VideoSource):
    async for frame_event in video_stream:
        buffer = frame_event.frame
        bgra_frame = buffer.convert(rtc.VideoBufferType.BGRA)
        np_frame = np.frombuffer(bgra_frame.data, dtype=np.uint8).reshape(
            bgra_frame.height, bgra_frame.width, 4
        )
        cv2.rectangle(np_frame, (50, 50), (250, 250), (0, 255, 0, 255), 3)
        new_frame = rtc.VideoFrame.from_ndarray(np_frame, format="bgra")
        output_source.capture_frame(new_frame)


async def entrypoint(ctx: JobContext):
    logging.info("Vision Agent job started, waiting for a video track...")

    # --- THIS SECTION IS CORRECTED ---

    # This new async function contains the logic we need to run
    async def handle_track_subscription(track: rtc.Track):
        logging.info("User video stream subscribed, initializing agent's output track.")
        
        # Default to a common size if dimensions aren't immediately available
        width = track.width if track.width > 0 else 640
        height = track.height if track.height > 0 else 480
        
        output_source = rtc.VideoSource(width, height)
        agent_track = rtc.LocalVideoTrack.create_video_track("agent_processed_video", output_source)
        await ctx.room.local_participant.publish_track(agent_track)
        
        logging.info("Agent track published. Starting processing loop.")
        ctx.create_task(process_frames(rtc.VideoStream(track), output_source))

    # The event handler itself is now a standard 'def' function
    def on_track_subscribed(track: rtc.Track, publication: rtc.TrackPublication, participant: rtc.RemoteParticipant):
        if track.kind == rtc.TrackKind.KIND_VIDEO:
            # We launch our async logic as a new task
            ctx.create_task(handle_track_subscription(track))
    
    # Register the synchronous handler
    ctx.room.on("track_subscribed", on_track_subscribed)


def main():
    logging.info("Starting Vision Agent worker...")
    
    # --- THIS IS THE CORRECTED LINE ---
    # Add the agent_name to the WorkerOptions
    opts = WorkerOptions(
        entrypoint_fnc=entrypoint,
        agent_name="aura-vision-agent" # Give the agent a unique name
    )
    
    cli.run_app(opts)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler()])
    main()