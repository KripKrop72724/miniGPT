from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
import openai
from django.conf import settings
from django.core.files.images import ImageFile

from AP01.models import Conversation, Prompt
from AP01.serializer import ChatPromptSerializer, ConversationSerializer, PromptSerializer, UserSerializer
import io
from PIL import Image
import base64
from django.contrib.auth import authenticate

# Set OpenAI API key
openai.api_key = settings.OPENAI_API_KEY


class ChatGPTView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = ChatPromptSerializer(data=request.data)
        if serializer.is_valid():
            conversation_id = serializer.validated_data.get('conversation_id')
            text = serializer.validated_data.get('text', '')
            image = serializer.validated_data.get('image', None)
            audio = serializer.validated_data.get('audio', None)

            try:
                conversation = Conversation.objects.get(id=conversation_id)
            except Conversation.DoesNotExist:
                return Response({"error": "Conversation does not exist."}, status=status.HTTP_404_NOT_FOUND)

            file_instance = None
            if audio:
                transcription = self.transcribe_audio(audio)
                file_instance = audio
                if transcription.get('error'):
                    return Response({"error": transcription['error']}, status=status.HTTP_400_BAD_REQUEST)
                text += " " + transcription.get('transcript', '')
            elif image:
                image_b64 = self.convert_image_to_base64(image)
                file_instance = ContentFile(base64.b64decode(image_b64), name='prompt_image.jpg')

            response_data = self.process_prompt(text, image)

            # Save prompt and response to the database, now including the file if present
            try:
                Prompt.objects.create(
                    conversation=conversation,
                    text=text,
                    response=response_data.get('response', ''),
                    file=file_instance  # Save the file here
                )
            except ValidationError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def process_prompt(self, text, image):
        if image:
            image_b64 = self.convert_image_to_base64(image)
            model = "gpt-4-vision-preview"
            messages = [
                {"role": "user", "content": [{"type": "text", "text": text}, {"type": "image_url", "image_url": {
                    "url": f"data:image/jpeg;base64,{image_b64}"}}]}
            ]
        else:
            model = "gpt-4"
            messages = [{"role": "user", "content": text}]

        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                max_tokens=4096
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
        return img_base64

    def transcribe_audio(self, audio_file):
        try:
            response = openai.Audio.transcribe(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
            return {"transcript": response}
        except Exception as e:
            return {"error": str(e)}


class ConversationViewSet(viewsets.ModelViewSet):
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer

    def create_prompt(self, request, pk=None):
        conversation = self.get_object()
        serializer = PromptSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(conversation=conversation)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SignupView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'User created successfully'}, status=201)
        return Response(serializer.errors, status=400)


class LoginView(APIView):
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user:
            return Response({'message': 'Login successful'}, status=200)
        return Response({'message': 'Invalid credentials'}, status=400)
