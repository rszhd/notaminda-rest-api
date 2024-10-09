from rest_framework import serializers
import json


class JSONFieldSerializer(serializers.Field):
    def to_representation(self, value):
        if value is None:
            return None
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return value

    def to_internal_value(self, data):
        if data is None:
            return None
        if isinstance(data, str):
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                raise serializers.ValidationError("Invalid JSON data")
        return json.dumps(data)
