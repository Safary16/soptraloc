from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Company, Vehicle, MovementCode


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email')


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = [
            'id',
            'name',
            'code',
            'rut',
            'email',
            'phone',
            'address',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ('id', 'created_at', 'updated_at')


class VehicleSerializer(serializers.ModelSerializer):
    vehicle_type_display = serializers.CharField(source='get_vehicle_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Vehicle
        fields = [
            'vehicle_type_display',
            'status_display',
            'brand',
            'created_at',
            'created_by',
            'id',
            'is_active',
            'max_capacity',
            'model',
            'plate',
            'status',
            'updated_at',
            'updated_by',
            'vehicle_type',
            'year'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by', 'updated_by')


class MovementCodeSerializer(serializers.ModelSerializer):
    is_used = serializers.SerializerMethodField()

    class Meta:
        model = MovementCode
        fields = [
            'is_used',
            'code',
            'created_at',
            'created_by',
            'description',
            'id',
            'is_active',
            'movement_type',
            'updated_at',
            'updated_by',
            'used_at'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by', 'updated_by', 'used_at')
    
    def get_is_used(self, obj):
        return obj.used_at is not None