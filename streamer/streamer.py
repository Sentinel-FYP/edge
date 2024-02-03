from aiortc.contrib.media import MediaPlayer
from aiortc import RTCPeerConnection, RTCSessionDescription
import os


class VideoStreamer:
    def __init__(self, media_path, is_rtsp=False):
        self.media_path = media_path
        self.is_rtsp = is_rtsp
        self.pc: RTCPeerConnection = None

    def create_local_tracks(self, decode=True):
        player = MediaPlayer(self.media_path, decode=decode)
        return player.audio, player.video

    async def handle_offer(self, data):
        print("offer received", data)
        offer = RTCSessionDescription(sdp=data["sdp"], type=data["type"])
        self.pc = RTCPeerConnection()

        @self.pc.on("connectionstatechange")
        async def on_connectionstatechange():
            print("Connection state is %s" % self.pc.connectionState)
            if self.pc.connectionState == "failed":
                await self.pc.close()

        # open media source
        audio, video = self.create_local_tracks()

        if audio:
            audio_sender = self.pc.addTrack(audio)
        if video:
            video_sender = self.pc.addTrack(video)

        await self.pc.setRemoteDescription(offer)

        answer = await self.pc.createAnswer()
        await self.pc.setLocalDescription(answer)

        return {
            "sdp": self.pc.localDescription.sdp,
            "type": self.pc.localDescription.type,
            "deviceId": os.getenv("DEVICE_ID"),
        }

    async def close(self):
        await self.pc.close()
