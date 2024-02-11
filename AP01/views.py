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

openai.api_key = settings.OPENAI_API_KEY


class ChatGPTView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = ChatPromptSerializer(data=request.data)
        if serializer.is_valid():
            text = serializer.validated_data.get('text', '')
            image = serializer.validated_data.get('image', None)
            audio = serializer.validated_data.get('audio', None)

            if audio:
                # Process the audio file
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
            image_b64 = self.convert_image_to_base64(image)
            prompt = {
                "prompt": {"image": image_b64, "text": text},
                "n": 1,
                "stop": None,
                "temperature": 0.7,
            }
        else:
            prompt = {"prompt": text, "n": 1, "stop": None, "temperature": 0.7}

        try:
            response = openai.ChatCompletion.create(model="gpt-4", **prompt)
            return {"response": response.choices[0].message.content}
        except Exception as e:
            return {"error": str(e)}

    def convert_image_to_base64(self, image_file):
        # Open the image file
        image = Image.open(image_file)
        # Convert the image to RGB format (if not already in this format)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        # Create a bytes buffer for the image
        buffered = BytesIO()
        # Save the image to the buffer
        image.save(buffered, format="JPEG")
        # Get the byte value of the image
        img_byte = buffered.getvalue()
        # Encode the byte value to base64
        img_base64 = base64.b64encode(img_byte)
        # Convert base64 bytes to string
        img_str = img_base64.decode('utf-8')
        return img_str

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
