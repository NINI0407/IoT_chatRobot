# 安裝所需套件
# pip install google-genai pyaudio asyncio

import asyncio
import pyaudio
from google import genai
from google.genai.types import LiveConnectConfig, SpeechConfig, VoiceConfig, PrebuiltVoiceConfig

# ✍️ 配置常數
PROJECT_ID = "YOUR_PROJECT_ID"
LOCATION = "us-central1"
MODEL = "gemini-2.0-flash-live-preview-04-09"
INPUT_RATE = 16000
OUTPUT_RATE = 24000
CHUNK = 4096
FORMAT = pyaudio.paInt16
CHANNELS = 1

# 初始化 Gemini 客戶端
client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

# 設置串流配置：接收聲音並使用 Puck 聲音回應
config = LiveConnectConfig(
    response_modalities=["AUDIO"],
    speech_config=SpeechConfig(
        voice_config=VoiceConfig(
            prebuilt_voice_config=PrebuiltVoiceConfig(voice_name="Puck")
        )
    ),
    input_audio_transcription={},
    output_audio_transcription={}
)

async def main():
    p = pyaudio.PyAudio()
    # 打開麥克風流
    mic_stream = p.open(format=FORMAT, channels=CHANNELS,
                        rate=INPUT_RATE, input=True, frames_per_buffer=CHUNK)
    # 打開揚聲器輸出流
    speaker_stream = p.open(format=FORMAT, channels=CHANNELS,
                            rate=OUTPUT_RATE, output=True, frames_per_buffer=CHUNK)

    async with client.aio.live.connect(model=MODEL, config=config) as session:
        print("🎙️ Session started. You can speak now.")

        async def send():
            while True:
                data = mic_stream.read(CHUNK)
                await session.send(input={"data": data, "mime_type": "audio/pcm"})
                await asyncio.sleep(0)

        async def recv():
            async for msg in session.receive():
                if msg.server_content.input_transcription:
                    t = msg.server_content.input_transcription.text
                    print(f"[You said]: {t}")
                if msg.server_content.output_audio_transcription:
                    print(f"[Gemini thinks]: {msg.server_content.output_audio_transcription.text}")
                if msg.server_content.model_turn:
                    for part in msg.server_content.model_turn.parts:
                        data = part.inline_data.data
                        speaker_stream.write(data)

        await asyncio.gather(send(), recv())

if __name__ == "__main__":
    asyncio.run(main())
