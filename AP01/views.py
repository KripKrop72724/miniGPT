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
        openai.api_key = settings.OPENAI_API_KEY
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
        messages = [{"role": "user", "content": text}]

        if image:
            image_b64 = self.convert_image_to_base64(image)
            # Assuming the model you're using supports image inputs, adjust as necessary.
            # Add the image as a separate message following the OpenAI format for images.
            messages.append({
                "role": "user",
                "content": {
                    "type": "image",
                    "data": f"data:image/jpeg;base64,{image_b64}"
                }
            })

        try:
            # Ensure you're using the correct model that supports text and image inputs
            response = openai.ChatCompletion.create(
                model="gpt-4-vision-preview",  # Replace with the actual model name
                messages=messages
            )
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
        print(img_base64)
        return img_base64

    def transcribe_audio(self, audio_file):
        try:
            response = openai.Audio.transcribe(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
            print(response)
            return {"transcript": response}
        except Exception as e:
            return {"error": str(e)}
