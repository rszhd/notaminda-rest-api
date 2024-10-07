import asyncio
import uuid
from typing import List, Dict
import logging
import json
import os

from django.core.exceptions import ValidationError
from pydantic import BaseModel
from openai import AsyncOpenAI

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
AI_MODEL = os.environ.get('AI_MODEL')

logger = logging.getLogger(__name__)

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

class AutoGenerateNodeChildren:
    @staticmethod
    async def generate_children(
        node,
        num_children: int = 3,
        positions: List[Dict] = None,
        ai_key: str = None,
        ai_model: str = None
    ) -> List[Dict]:
        ai_model = ai_model if ai_key else AI_MODEL
        ai_key = ai_key or OPENAI_API_KEY

        def combine_children_data(positions: List[Dict], subtopics: List[Dict]) -> List[Dict]:
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

        def prepare_node_data(positions: List[Dict]) -> tuple:
            nodes_structure = []
            nodes_position = []
            if positions:
                for item in positions:
                    nodes_structure.append({
                        'id': item['id'],
                        'title': item['title'],
                        'parent_node': item.get('parentNode')
                    })
                    nodes_position.append({k: v for k, v in item.items() if k != 'title'})
            return nodes_structure, nodes_position

        def create_subtopic_prompt(node, num_children: int, nodes_structure: List[Dict]) -> str:
            return f"""
            These are nodes structure for my mind map.
            {nodes_structure}
            I need your help to generate {num_children} subtopics for the {node.id} node
            """

        def create_position_prompt(node, num_children: int, nodes_position: List[Dict]) -> str:
            return f"""
            These are my mind map nodes and their position in a canvas. 
            ```
            {nodes_position}
            ```
            I need to add {num_children} more children nodes for node with id {node.id}.
            Suggest {num_children} x and y position for the new nodes. 
            Follow the same position pattern as my mind map & ensure it doesn't overlap with each other.
            """

        async def fetch_ai_responses(client: AsyncOpenAI, model: str, subtopic_prompt: str, position_prompt: str) -> tuple:
            tasks = [
                client.beta.chat.completions.parse(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": subtopic_prompt}
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
            return json.loads(responses[0].choices[0].message.content), json.loads(responses[1].choices[0].message.content)

        async with AsyncOpenAI(api_key=ai_key) as client:
            nodes_structure, nodes_position = prepare_node_data(positions)

            subtopic_prompt = create_subtopic_prompt(node, num_children, nodes_structure)
            position_prompt = create_position_prompt(node, num_children, nodes_position)

            try:
                subtopics, new_positions = await fetch_ai_responses(
                    client, ai_model, subtopic_prompt, position_prompt
                )
                return combine_children_data(new_positions['positions'], subtopics['subtopics'])
            except Exception as e:
                logger.error(f"Error generating children: {str(e)}")
                raise

    @classmethod
    def run(cls, node, num_children: int, positions: List[Dict], ai_key: str, ai_model: str) -> List[Dict]:
        return asyncio.run(cls.generate_children(node, num_children, positions, ai_key, ai_model))

