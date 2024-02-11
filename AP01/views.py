from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import openai
from django.conf import settings
from django.core.files.images import ImageFile
from AP01.serializer import ChatPromptSerializer
import io
from PIL import Image
import base64

# Set OpenAI API key
openai.api_key = settings.OPENAI_API_KEY


class ChatGPTView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = ChatPromptSerializer(data=request.data)
        if serializer.is_valid():
            text = serializer.validated_data.get('text', '')
            image = serializer.validated_data.get('image', None)
            audio = serializer.validated_data.get('audio', None)

            if audio:
                transcription = self.transcribe_audio(audio)
                if transcription.get('error'):
                    return Response({"error": transcription['error']}, status=status.HTTP_400_BAD_REQUEST)
                text += " " + transcription.get('transcript', '')

            response_data = self.process_prompt(text, image)
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def process_prompt(self, text, image):
        if image:
            # Convert image to base64 and prepare the payload for an image prompt
            image_b64 = self.convert_image_to_base64(image)
            model = "gpt-4-vision-preview"
            messages = [
                # {"role": "user", "content": text},
                {"role": "user", "content": [{"type": "text", "text": text}, {"type": "image_url", "image_url": {
                    "url": f"data:image/jpeg;base64,{image_b64}"}}]}
            ]
        else:
            # If no image is provided, use a text-based prompt
            model = "gpt-4"
            messages = [{"role": "user", "content": text}]

        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                max_tokens=4096
            )
            print(response)
            return {"response": response['choices'][0]['message']['content']}
        except Exception as e:
            return {"error": str(e)}

    def convert_image_to_base64(self, image_file):
        image = Image.open(image_file)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        img_byte = buffered.getvalue()
        img_base64 = base64.b64encode(img_byte).decode('utf-8')
        return img_base64

    def transcribe_audio(self, audio_file):
        try:
            response = openai.Audio.transcribe(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
            return {"transcript": response['data']['text']}
        except Exception as e:
            return {"error": str(e)}
