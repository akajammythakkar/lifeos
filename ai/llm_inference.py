import boto3
import json
from ai.prompts import claude_prompt
import os
import dotenv
from typing import List, Dict

dotenv.load_dotenv()

class ClaudeInference:
    def __init__(self, region_name='eu-north-1'):
        self.bedrock = boto3.client(
            service_name='bedrock-runtime',
            region_name=region_name
        )
        self.model_id = 'eu.anthropic.claude-3-7-sonnet-20250219-v1:0'
        self.inference_profile = 'arn:aws:bedrock:eu-north-1:024848454151:inference-profile/eu.anthropic.claude-3-7-sonnet-20250219-v1:0'
    
    def analyze_transcript(self, text_content: str) -> List[Dict]:
        """
        Send text content to Claude 3 Sonnet via AWS Bedrock for analysis
        Returns a list of action items
        """
        prompt = claude_prompt.format(transcript=text_content)
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "temperature": 0.5,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        })
        
        response = self.bedrock.invoke_model(
            body=body,
            modelId=self.model_id,
            accept='application/json',
            contentType='application/json'
        )
        
        response_body = json.loads(response.get('body').read())
        response_text = response_body.get('content', [{}])[0].get('text', '')
        
        try:
            # Try to parse the response as JSON
            action_items = json.loads(response_text)
            if not isinstance(action_items, list):
                action_items = [{"description": response_text}]
        except json.JSONDecodeError:
            # If parsing fails, create a single action item with the raw text
            action_items = [{"description": response_text}]
        
        # Ensure each action item has required fields
        for item in action_items:
            if not isinstance(item, dict):
                item = {"description": str(item)}
            item.setdefault("status", "pending")
            item.setdefault("priority", "medium")
        
        return action_items 