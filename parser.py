# Creating and testing PydanticOutputParser from scratch and using it with a self made template. 
 
import json 
import re 
from typing import TypeVar, Generic, Any
from pydantic import BaseModel, ValidationError, Field
from openai import OpenAI

class PydanticOutputParser(): 
    """Generate JSON format instructions, parse JSON, and validate Output. """

    def __init__(self, pydantic_model: type[BaseModel]) : 
        self.pydantic_model = pydantic_model

    def get_format_instructions(self) -> str: 
        """Generate Schema Enforcements for the LLM prompt"""
        schema = self.pydantic_model.model_json_schema()

        return (
            "Return a valid JSON object that conforms to the "
            "following schema. Do not include Markdown or explanations. \n\n"
            f"Schema:\n{json.dumps(schema, indent=2, ensure_ascii=False)}"
        )

    def parse(self, text: str) -> BaseModel: 
        """
        Parse the LLM JSON string response into a Python and then validates it 
        against the pydantic model and creates it's pydantic model object.
        """
        
        text = text.strip()
        # Removing the JSON string wrapped in MarkDown code fences. 
        match = re.fullmatch(
            r"```(?:json)?\s*(.*?)\s*```",
            text, 
            flags=re.IGNORECASE | re.DOTALL,
        )

        if match:
            text = match.group(1)

        try: 
            result = json.loads(text)
        except json.JSONDecodeError as exc :
            raise ValueError(f"Invalid JSON output: {exc}") from exc 

        if not isinstance(result, dict): 
            raise ValueError("Expected a dictionary object")

        final_result = self.pydantic_model.model_validate(result)

        return final_result

model = OpenAI(
    api_key=oc_api_key,
    base_url="https://vyceai.com/v1",
)

def prompt_template(system, user, schema): 
    system_prompt = f"You are a {system} assistant"
    user_prompt = f"extract information from the text. \n{schema} \n Text: {user}"
    return system_prompt, user_prompt

class EmployeeInfo(BaseModel): 
    name: str = Field(description = "The employee's full name")
    role: str = Field(description= "Job title or department")
    skills: str = Field(description="List of core technical skills")

parser = PydanticOutputParser(pydantic_model=EmployeeInfo)

system_prompt, user_prompt = prompt_template(
    system="Very helpful",
    user="Alex is a Senior Dev Ops engineer who specializes in Docker, Kubernetes, and AWS.",
    schema= parser.get_format_instructions()
)

response = model.chat.completions.create(
    model="glm-5.3-flash",
    messages=[
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": user_prompt
        }
    ]
)

result = response.choices[0].message.content

final = parser.parse(result)

print(final)