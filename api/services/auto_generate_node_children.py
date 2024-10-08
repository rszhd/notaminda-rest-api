import uuid
from typing import List, Dict
import logging
import json

from django.core.exceptions import ValidationError
from pydantic import BaseModel
from openai import AsyncOpenAI

from ..utils.generate_node_positions import generate_node_positions

logger = logging.getLogger(__name__)


class Subtopic(BaseModel):
    title: str


class SubtopicList(BaseModel):
    subtopics: List[Subtopic]


class NodeChildrenGenerator:
    @staticmethod
    def _combine_children_data(
        positions: List[Dict], subtopics: List[Dict]
    ) -> List[Dict]:
        if len(positions) != len(subtopics):
            raise ValidationError("Input arrays must have the same length.")

        return [
            {
                "x": pos["position"]["x"],
                "y": pos["position"]["y"],
                "title": subtopic["title"],
                "id": uuid.uuid4(),
            }
            for pos, subtopic in zip(positions, subtopics)
        ]

    @staticmethod
    def _prepare_node_data(positions: List[Dict]) -> List[Dict]:
        return (
            [
                {
                    "id": item["id"],
                    "title": item["title"],
                    "parent_node": item.get("parentNode"),
                }
                for item in positions
            ]
            if positions
            else []
        )

    @staticmethod
    def _create_subtopic_prompt(node, nodes_structure: List[Dict]) -> str:
        return f"""
        I am making a mind map & these are the current nodes structure.
        ```
        {nodes_structure}
        ```
        I need your help to generate the next layer of children nodes for the '{node.id}' node with title '{node.title}'.
        Please keep the amount of children nodes between 3 - 10.
        """

    @classmethod
    async def generate(
        cls, ai_model, ai_key, node, positions: List[Dict] = None
    ) -> List[Dict]:
        async with AsyncOpenAI(api_key=ai_key) as client:
            nodes_structure = cls._prepare_node_data(positions)
            subtopic_prompt = cls._create_subtopic_prompt(node, nodes_structure)

            try:
                response = await client.beta.chat.completions.parse(
                    model=ai_model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": subtopic_prompt},
                    ],
                    response_format=SubtopicList,
                )
                subtopics = json.loads(response.choices[0].message.content)
                new_positions = generate_node_positions(
                    json.loads(node.flow_data), len(subtopics["subtopics"]), positions
                )
                return cls._combine_children_data(new_positions, subtopics["subtopics"])
            except Exception as e:
                logger.error(f"Error generating children: {str(e)}")
                raise
