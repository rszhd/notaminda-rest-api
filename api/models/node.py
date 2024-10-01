import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import JSONField
from .mindmap import MindMap
from openai import OpenAI
from dotenv import load_dotenv
import os
from pydantic import BaseModel
from typing import List, Dict

load_dotenv()

class Subtopic(BaseModel):
    title: str

class SubtopicList(BaseModel):
    subtopics: List[Subtopic]

class Position(BaseModel):
    x: float
    y: float
    absolute_x: float
    absolute_y: float

class PositionList(BaseModel):
    positions: List[Position]

def generate_unique_id():
    return uuid.uuid4().hex[:20]

def combine_arrays(positions: List[Position], subtopics: List[Subtopic]) -> List[dict]:
    if len(positions) != len(subtopics):
        raise ValidationError("Input arrays must have the same length.")

    combined_array = []

    for position, subtopic in zip(positions, subtopics):
        combined_item = {
            'x': position.x,
            'y': position.y,
            'absolute_x': position.absolute_x,
            'absolute_y': position.absolute_y,
            'title': subtopic.title,
            'id': uuid.uuid4().hex[:20]
        }
        combined_array.append(combined_item)

    return combined_array

class Node(models.Model):
    id = models.CharField(max_length=50, primary_key=True, default=generate_unique_id, editable=False)
    title = models.CharField(max_length=200)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    mind_map = models.ForeignKey(MindMap, on_delete=models.CASCADE, related_name='nodes')
    created_at = models.DateTimeField(auto_now_add=True)
    flow_data = JSONField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['id']),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        if self.parent and self.parent.id == self.id:
            raise ValidationError("A node cannot be its own parent.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def generate_children(self, num_children=3, positions=""):
        open_ai = OpenAI(api_key=os.environ.get('OPENAI_KEY'))

        nodes_structure = []
        nodes_position = []
        for item in positions:
            new_structure = {}
            new_structure['id'] = item['id']
            new_structure['title'] = item['title'] 
            new_structure['parent_node'] = item.get('parentNode', None)
            new_positions = item.copy()
            del new_positions['title']
            nodes_position.append(new_positions)
            nodes_structure.append(new_structure)

        prompt = f"""
        These are nodes structure for my mind map.
        {nodes_structure}
        I need your helps to generate {num_children} subtopics for the {self.id} node
        """
        response = open_ai.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            response_format=SubtopicList,
        )

        position_prompt = f"""
        These are my mind map nodes and their position in a canvas. 
        ```
        {nodes_position}
        ```
        I need to add {num_children} more children nodes for node with id {self.id}.
        Suggest 3 x and y position for the new nodes. 
        Follow the same position pattern as my mind map & ensure it doesnt overlapping each others.
        """
        position_response = open_ai.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": position_prompt}
            ],
            response_format=PositionList,
        )

        new_nodes_positions = position_response.choices[0].message.parsed.positions
        subtopics = response.choices[0].message.parsed.subtopics
        new_nodes = combine_arrays(new_nodes_positions, subtopics)

        return new_nodes