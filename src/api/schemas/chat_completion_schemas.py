import uuid
from typing import List, Optional

from pydantic import BaseModel, field_validator, model_validator
from fastapi import HTTPException


class Reference(BaseModel):
    content: str
    url: Optional[str] = None


class ChatCompletionInputSchema(BaseModel):
    """
    Represents the input schema for chat completion.

    Attributes:
        chat_query (str): The current query in the chat.
        chat_history (List[str] | None): The history of the chat messages.
        chat_id (str | None): UUID of an existing chat in the database.
    """
    chat_query: str
    chat_history: Optional[List[str]] = None
    chat_id: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "chat_query": "How can you assist me?",
                    "chat_history": [],
                    "chat_id": "a4c77902-87cc-485f-9b2e-c969e1068225",
                }
            ]
        }
    }

    @field_validator('chat_query')
    def validate_chat_query_length(cls, chat_query):
        max_length = 2000
        if len(chat_query) > max_length:
            raise HTTPException(
                status_code=413,
                detail=f'chat_query length exceeds {max_length} characters'
            )
        return chat_query

    @field_validator('chat_history')
    def validate_chat_history_length(cls, chat_history):
        if chat_history is None:  # user might not provide chat_history
            return chat_history
        if len(chat_history) % 2 != 0:
            raise ValueError('chat_history length must be even')
        return chat_history

    @field_validator('chat_id')
    def validate_chat_id_is_uuid(cls, chat_id):
        if chat_id is None:
            return chat_id
        try:
            uuid.UUID(chat_id)
        except ValueError:
            raise ValueError("chat_id must be a valid UUID string.")
        return chat_id

    @model_validator(mode='before')
    def check_chat_id_or_chat_history(cls, values):
        """
        Ensures the user provides exactly one of chat_id or chat_history,
        but not both, and not neither.
        """
        chat_id = values.get('chat_id')
        chat_history = values.get('chat_history')

        if chat_id and chat_history is not None:
            raise ValueError(
                "You must provide only one of 'chat_id' or 'chat_history', not both."
            )
        if not chat_id and chat_history is None:
            raise ValueError(
                "You must provide one of 'chat_id' or 'chat_history'."
            )
        return values


class ChatCompletionOutputSchema(BaseModel):
    """
    Represents the output schema for chat completion.

    Attributes:
        text (str): The completed message based on the input chat query and history.
        input_documents (List[Document]): List of input documents provided for the completion.
    """
    message: str
    references: List[Reference]

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "Hello! 😊 I'm here to help you with information and support regarding Mitrix Technology. Here's what I can assist you with:\n\n- **Company Information:** Details about Mitrix Technology, our office locations, contact info, and more.\n- **Project Portfolio:** Insights into our projects, success stories, and use cases, including the LeadGuru project.\n- **Services:** Explanation of our services in software development, web/mobile app development, AI technologies, etc.\n- **Industries:** Information about the different industries we work with.\n- **Consultation:** Guidance on career opportunities or project development requests, with ball-park estimates if possible.\n- **Technology and Methodology:** Details on roles, tools, and technologies we use in software development.\n\nFeel free to ask any specific questions you might have! 🤗",
                    "references": [
                        {
                            "content": "Q: Can you develop AI chatbots and virtual assistants?\nA: Yes, we create AI-powered chatbots for customer support and automation.\nQ: How do you ensure the reliability of your software solutions?\nA: We conduct rigorous testing, code reviews, and performance monitoring.\nQ: What is your experience with cloud-native development?\nA: We build cloud-native apps optimized for AWS, Azure, and Google Cloud.\nQ: Can you optimize my software for high performance?\nA: Yes, we conduct performance audits and optimizations.\nQ: What databases do you work with?\nA: We use MySQL, PostgreSQL, MongoDB, Firebase, and more.\nQ: Can you develop AI chatbots and virtual assistants?\nA: Yes, we create AI-powered chatbots for customer support and automation.\nQ: What’s your experience with serverless computing?\nA: We build serverless applications using AWS Lambda, Azure Functions, and Google \nCloud Functions.",
                            "url": None
                        },
                        {
                            "content": "Please visit our page at (link)\nQ: What software consulting services do you provide?\nA: At Mitrix, we provide technology consulting and software assessment, software \ndevelopment consulting, and software architecture assessment and redesign. Please \nvisit our page at (link)\nQ: What mobile application development services do you provide?\nA: Our mobile development services include custom Android and iOS app \ndevelopment, automated QA and testing services, native and cross-platform app \ndevelopment, embedded Android & AOSP customizations, UI/UX design and \nprototyping services, and maintenance and support services. Please visit our page at \n(link)\nQ: What web development services do you provide?\nA: From concept ideation to deployment, we develop secure digital products that \nmaximize your business’ potential and attract more users, including websites, web \napplications, and server apps. Please visit our page at (link)\nQ: Do you provide post-launch support and maintenance?",
                            "url": None
                        },
                        {
                            "content": "Question \nAnswer\nQ: What industries do you work with?\nA: Mitrix collaborates with various industries, including healthcare, \neducation, finance, e-commerce, and startups. If your industry isn’t listed, \nlet us know - we’re always eager to explore new domains and \nchallenges. \nQ: Do you have experience working with healthcare providers?\nA: We have experience developing solutions such as digital health \npassports, patient management systems, and AI-driven diagnostics \nsoftware. Would you like me to connect you with one of our \nrepresentatives to discuss it further? Meanwhile, feel free to check out \nour healthcare presentation.\nLink to healthcare presentation\nQ: Do you have experience working with e-learning providers?\nA: We have experience creating intuitive learning automation platforms \nand tools for online learning. Would you like me to connect you with one \nof our representatives to discuss it further? Meanwhile, feel free to check \nout our edtech presentation.",
                            "url": None
                        },
                        {
                            "content": "to another AI-powered technology – AI copilots. Both leverage LLMs and generative AI tools to respond naturally to user requests and streamline complex tasks. However, copilots are more constrained compared to the advanced autonomy and capabilities of AI agents.AI copilots:can complete preconfigured tasks;developed to work alongside users;do not analyze or interpret context deeply;function as a tool for assisting with straightforward tasks.AI agents:can build their workflows;offer personalized solutions;learn from each interaction;adapt to a specific situation.In other words, AI agents elevate the capabilities of generative AI by going beyond mere assistance. Instead, they can collaborate with you or even act independently on your behalf.The benefits for a businessAI agents offer significant advantages for businesses and end users alike, including:Boosted productivity: By automating routine tasks, AI agents free up time for employees to focus on their creative and strategic",
                            "url": "https://mitrix.io/artificial-intelligence/ai-agents-the-cornerstone-of-digital-transformation-in-2025"
                        }
                    ]
                }
            ]
        }
    }
