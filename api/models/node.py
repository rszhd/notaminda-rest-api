import uuid
from django.db import models
from django.core.exceptions import ValidationError
from .mindmap import MindMap
from dotenv import load_dotenv
import os
from pydantic import BaseModel
from typing import List
import asyncio
from functools import lru_cache
from openai import AsyncOpenAI
import json
import aiohttp


load_dotenv()

@lru_cache(maxsize=1)
def get_openai_client():
    return AsyncOpenAI(api_key=os.environ.get('OPENAI_KEY'))

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
    return uuid.uuid4().hex[:50]

class Node(models.Model):
    id = models.CharField(max_length=50, primary_key=True, default=generate_unique_id, editable=False)
    title = models.CharField(max_length=200)
    note = models.TextField(default="", blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children', db_index=True)
    mind_map = models.ForeignKey(MindMap, on_delete=models.CASCADE, related_name='nodes', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    flow_data = models.JSONField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['id', 'parent', 'mind_map']),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        if self.parent and self.parent.id == self.id:
            raise ValidationError("A node cannot be its own parent.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @staticmethod
    def create_client(ai_key=None):
        if ai_key:
            return AsyncOpenAI(api_key=ai_key)
        return get_openai_client()
    
        # async with aiohttp.ClientSession() as session:
        #     tasks = [
        #         self.make_openai_call(session, prompt1),
        #         self.make_openai_call(session, prompt2)
        #     ]
        #     responses = await asyncio.gather(*tasks)
        # return responses

    async def generate_children(self, num_children=3, positions=None, ai_key=None, ai_model=None):
        async with aiohttp.ClientSession() as session:
            client = self.create_client(ai_key)
            model = ai_model if ai_key and ai_model else "gpt-4o-mini"

            nodes_structure = []
            nodes_position = []
            if positions:
                for item in positions:
                    new_structure = {
                        'id': item['id'],
                        'title': item['title'],
                        'parent_node': item.get('parentNode')
                    }
                    new_positions = {k: v for k, v in item.items() if k != 'title'}
                    nodes_position.append(new_positions)
                    nodes_structure.append(new_structure)

            prompt = f"""
            These are nodes structure for my mind map.
            {nodes_structure}
            I need your help to generate {num_children} subtopics for the {self.id} node
            """

            position_prompt = f"""
            These are my mind map nodes and their position in a canvas. 
            ```
            {nodes_position}
            ```
            I need to add {num_children} more children nodes for node with id {self.id}.
            Suggest {num_children} x and y position for the new nodes. 
            Follow the same position pattern as my mind map & ensure it doesn't overlap with each other.
            """
            tasks = [
                client.beta.chat.completions.parse(
                        model=model,
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant."},
                            {"role": "user", "content": prompt}
                        ],
                        response_format=SubtopicList,
                    ),
                client.beta.chat.completions.parse(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": position_prompt}
                    ],
                    response_format=PositionList,
                )
            ]

            responses = await asyncio.gather(*tasks)
            print(responses)
            subtopics = responses[0].choices[0].message.content
            new_positions = responses[1].choices[0].message.content
            subtopics_dict = json.loads(subtopics)
            new_positions_dict = json.loads(new_positions)

            new_nodes = self.combine_arrays(new_positions_dict['positions'], subtopics_dict['subtopics'])

            return new_nodes

    @staticmethod
    def combine_arrays(positions, subtopics):
        if len(positions) != len(subtopics):
            raise ValidationError("Input arrays must have the same length.")

        return [
            {
                'x': pos['x'],
                'y': pos['y'],
                'absolute_x': pos['absolute_x'],
                'absolute_y': pos['absolute_y'],
                'title': subtopic['title'],
                'id': uuid.uuid4()
            }
            for pos, subtopic in zip(positions, subtopics)
        ]
