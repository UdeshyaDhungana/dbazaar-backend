from dataclasses import field
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from djoser.serializers import UserSerializer as BaseUserSerializer

class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        fields = [
            'id',
            'username',
            'password',
            'email',
            'first_name',
            'last_name',
            'wallet_address',
            'public_key'
        ]
    

class UserSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        fields = [
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'wallet_address'
            'public_key'
        ]