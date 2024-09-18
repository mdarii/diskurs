import logging
from abc import abstractmethod, ABC
from typing import Optional, Self

from entities import Conversation, ChatMessage, PromptArgument, GenericPrompt
from interfaces import ConversationDispatcher, LLMClient, Agent, ConversationParticipant
from prompt import Prompt

logger = logging.getLogger(__name__)

# TODO: consider passing a child class of AgentConfig to the create method, for specific agent types
# TODO: consider having agent config class in agent module


class BaseAgent(ABC, Agent, ConversationParticipant):
    def __init__(
        self,
        name: str,
        prompt: GenericPrompt,
        llm_client: LLMClient,
        topics: Optional[list[str]] = None,
        dispatcher: Optional[ConversationDispatcher] = None,
        max_trials: int = 5,
    ):
        self.dispatcher = dispatcher
        self.prompt = prompt
        self.name = name
        self.topics = topics
        self.max_trials = max_trials
        self._topics = []
        self.llm_client = llm_client

    @classmethod
    @abstractmethod
    def create(cls, name: str, prompt: Prompt, llm_client: LLMClient, **kwargs) -> Self:
        pass

    @property
    def topics(self) -> list[str]:
        return self._topics

    @topics.setter
    def topics(self, value):
        self._topics = value

    @abstractmethod
    def invoke(self, conversation: Conversation | str) -> Conversation:
        """
        Runs the agent on a conversation, performing reasoning steps until the user prompt is final,
        meaning all the conditions, as specified in the prompt's is_final function, are met.
        If the conversation is a string i.e. starting a new conversation, the agent will prepare
        the conversation by setting the user prompt argument's content to this string.

        :param conversation: The conversation object to run the agent on. If a string is provided, the agent will
            start a new conversation with the string as the user query's content.
        :return: the updated conversation object after the agent has finished reasoning. Contains
            the chat history, with all the system and user messages, as well as the final answer.
        """
        pass

    def register_dispatcher(self, dispatcher: ConversationDispatcher) -> None:
        self.dispatcher = dispatcher

    @abstractmethod
    def process_conversation(self, conversation: Conversation) -> None:
        """
        Receives a conversation from the dispatcher, i.e. message bus, processes it and finally publishes
        a deep copy of the resulting conversation back to the dispatcher.

        :param conversation: The conversation object to process.
        """
        pass

    def prepare_conversation(
        self,
        conversation: Conversation | str,
        system_prompt_argument: PromptArgument,
        user_prompt_argument: PromptArgument,
    ) -> Conversation:
        """
        Ensures the conversation is in a valid state by creating a new set of prompts
        and prompt_variables for system and user, as well creating a fresh copy of the conversation.

        :param conversation: A conversation object, possible passed from another agent
            or a string to start a new conversation.
        :param system_prompt_argument: The system prompt argument to use for the system prompt.
        :param user_prompt_argument: The user prompt argument to use for the user prompt.
        :return: A deep copy of the conversation, in a valid state for this agent
        """
        if isinstance(conversation, str):
            user_prompt_argument.content = conversation

        system_prompt = self.prompt.render_system_template(self.name, prompt_args=system_prompt_argument)
        user_prompt = self.prompt.render_user_template(name=self.name, prompt_args=user_prompt_argument)

        if isinstance(conversation, str):
            return Conversation(
                system_prompt_argument=system_prompt_argument,
                user_prompt_argument=user_prompt_argument,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
        return conversation.update(
            chat=conversation.chat,
            system_prompt_argument=system_prompt_argument,
            user_prompt_argument=user_prompt_argument,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

    def generate_validated_response(self, conversation: Conversation) -> Conversation:
        for max_trials in range(self.max_trials):

            response = self.llm_client.generate(conversation, getattr(self, "tools", None))
            parsed_response = self.prompt.parse_prompt(response.last_message.content)

            if isinstance(parsed_response, PromptArgument):
                self.max_trials = 0
                return response.update(
                    user_prompt_argument=parsed_response,
                    user_prompt=self.prompt.render_user_template(name=self.name, prompt_args=parsed_response),
                )
            elif isinstance(parsed_response, ChatMessage):
                conversation = response.update(user_prompt=parsed_response)
            else:
                raise ValueError(f"Failed to parse response from LLM model: {parsed_response}")
