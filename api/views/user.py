from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from openai import OpenAI
import os

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    password = request.data.get('password')
    email = request.data.get('email')

    if not email or not password:
        return Response({'error': 'Please provide both email and password'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=email).exists():
        return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=email, password=password, email=email)
    return Response({'message': 'User created successfully'}, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response({'error': 'Please provide both email and password'}, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(username=email, password=password)

    if user is not None:
        refresh = RefreshToken.for_user(user)
        return Response({
            'token': str(refresh.access_token),
        }, status=status.HTTP_200_OK)
    else:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    
@api_view(['POST'])
def check_ai_api_key(request):
    api_key = request.data.get('key')
    client = OpenAI(api_key=api_key)

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": "Hello"
            }
        ]
    )

    response = completion.choices[0].message.content
    if response is not None:
        return Response({'message': 'User created successfully'}, status=status.HTTP_200_OK)
    else:
        return Response({'error': 'Invalid key'}, status=status.HTTP_400_BAD_REQUEST)