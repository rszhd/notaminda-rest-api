from rest_framework import serializers
from ..models import Note
from django.contrib.auth.models import User

class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ['id', 'node', 'content', 'created_at']

class NoteCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ['node']

    def create(self, validated_data):
        node = validated_data['node']
        user = self.context['request'].user
        if node.mind_map.user != user:
            raise serializers.ValidationError("You can only create notes for your own mind maps.")
        return Note.objects.create(**validated_data)
    
class NoteUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ['node']

    def update(self, instance, validated_data):
        user = self.context['request'].user
        if instance.mind_map.user != user:
            raise serializers.ValidationError("You can only update notes in your own mind maps.")
        return super().update(instance, validated_data)