from rest_framework import serializers

from AP01.models import Prompt, Conversation, User


class ChatPromptSerializer(serializers.Serializer):
    text = serializers.CharField(required=False, allow_blank=True)
    image = serializers.ImageField(required=False)
    audio = serializers.FileField(required=False)
    conversation_id = serializers.IntegerField(required=True,
                                               help_text="The ID of the conversation this prompt belongs to.")

    def validate_conversation_id(self, value):
        """
        Check if the conversation exists.
        """
        from .models import Conversation
        try:
            Conversation.objects.get(pk=value)
        except Conversation.DoesNotExist:
            raise serializers.ValidationError("Conversation with this ID does not exist.")
        return value


class PromptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prompt
        fields = ['id', 'text', 'response', 'created_at', 'file']


class ConversationSerializer(serializers.ModelSerializer):
    prompts = PromptSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'name', 'prompts', 'created_at']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create(**validated_data)
        return user