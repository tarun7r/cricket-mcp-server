import os
import asyncio
import threading
import gradio as gr
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver
from dotenv import load_dotenv
load_dotenv()

# Set your Gemini API key
google_api_key = os.getenv("GOOGLE_API_KEY")

class AgentManager:
    """
    Manages the asyncio event loop and the CricketAgent instance in a separate thread.
    """
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._start_loop, daemon=True)
        self.agent = CricketAgent()
        self._agent_initialized = threading.Event()
        self.thread.start()

    def _start_loop(self):
        """Starts the asyncio event loop."""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def _run_coro_sync(self, coro):
        """Runs a coroutine in the event loop and waits for the result."""
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        return future.result()

    def initialize_agent(self):
        """Initializes the agent if not already done."""
        if not self._agent_initialized.is_set():
            self._run_coro_sync(self.agent.initialize())
            self._agent_initialized.set()

    def ask_question(self, question, chat_history):
        """Asks a question to the agent."""
        self.initialize_agent() # Ensure agent is initialized
        return self._run_coro_sync(self.agent.ask_question(question, chat_history))

    def clear_memory(self):
        """Clears the agent's memory."""
        if self._agent_initialized.is_set():
            self.agent.clear_memory()

class CricketAgent:
    def __init__(self):
        self.client = None
        self.agent = None
        self.initialized = False
        self.memory = InMemorySaver()
        self.thread_id = "cricket_chat_session"
    
    async def initialize(self):
        """Initialize the MCP client and agent"""
        if self.initialized:
            return
            
        self.client = MultiServerMCPClient(
            {
                "cricket": {
                    "command": "python",
                    "args": ["cricket_server.py"],
                    "transport": "stdio",
                }
            }
        )
        tools = await self.client.get_tools()
        
        # Create the Gemini model
        model = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=google_api_key
        )
        
        # Create agent with memory
        self.agent = create_react_agent(
            model, 
            tools, 
            checkpointer=self.memory
        )
        self.initialized = True
    
    async def ask_question(self, question, chat_history):
        """Ask a question to the cricket agent with chat history"""
        try:
            if not self.initialized:
                await self.initialize()
            
            # Build the conversation history
            messages = []
            
            # Add chat history (keeping last 5 exchanges = 10 messages)
            for human_msg, ai_msg in chat_history[-5:]:
                if human_msg:
                    messages.append({"role": "user", "content": human_msg})
                if ai_msg:
                    messages.append({"role": "assistant", "content": ai_msg})
            
            # Add the current question
            messages.append({"role": "user", "content": question})
            
            # Invoke the agent with memory
            config = {"configurable": {"thread_id": self.thread_id}}
            response = await self.agent.ainvoke(
                {"messages": messages},
                config=config
            )
            
            # Extract the final answer
            final_message = response["messages"][-1]
            return final_message.content
        except Exception as e:
            return f"Error: {str(e)}"
    
    def clear_memory(self):
        """Clear the conversation memory"""
        self.memory = InMemorySaver()
        if self.agent:
            self.agent.checkpointer = self.memory

# Global agent manager
agent_manager = AgentManager()

def process_cricket_query(message, chat_history):
    """Process cricket query and return response with chat history"""
    if not message.strip():
        return "", chat_history
    
    try:
        # Use the agent manager to handle the async call
        response = agent_manager.ask_question(message, chat_history)
        
        # Add the new exchange to chat history
        chat_history.append((message, response))
        
        return "", chat_history
    except Exception as e:
        error_response = f"An error occurred: {str(e)}"
        chat_history.append((message, error_response))
        return "", chat_history

def clear_chat():
    """Clear chat history and agent memory"""
    agent_manager.clear_memory()
    return [], ""

# Create the Gradio interface
def create_interface():
    with gr.Blocks(
        theme=gr.themes.Soft(),
        title="🏏 Cricket Statistics Assistant",
    ) as demo:
        
        # Header
        gr.HTML("""
            <div class="cricket-header">
                <h1>🏏 Cricket Statistics Assistant</h1>
                <p style=\"font-size: 18px; margin-top: 10px;\">
                    Your AI-powered cricket companion!
                </p>
            </div>
        """)
        
        with gr.Row():
            with gr.Column(scale=3):
                # Chat interface
                chatbot = gr.Chatbot(
                    label="Cricket Chat Assistant",
                    height=500,
                    show_label=True,
                    container=True,
                    show_copy_button=True
                )
                
                with gr.Row():
                    msg_input = gr.Textbox(
                        label="Your cricket question",
                        placeholder="Ask about player stats, live scores, schedules...",
                        lines=2,
                        scale=5,
                        container=False
                    )
                    with gr.Column(scale=1, min_width=120):
                        send_btn = gr.Button("Send 🏏", variant="primary", size="lg")
                        clear_btn = gr.Button("Clear Chat 🗑️", variant="secondary")
                
            with gr.Column(scale=2):
                # Examples and features
                gr.HTML("""
                    <div class="feature-box">
                        <h3>🎯 What can I help with?</h3>
                        <ul>
                            <li>Player statistics & records</li>
                            <li>Batting & bowling averages</li>
                            <li>Career highlights</li>
                            <li>Live match updates</li>
                            <li>Live commentary (paste a match URL)</li>
                            <li>Upcoming schedules</li>
                            <li>Format comparisons</li>
                            <li>Historical cricket data</li>
                            <li>Latest cricket news</li>
                            <li>ICC rankings (batting, bowling, all-rounders, teams)</li>
                            <li>Match scorecards & detailed analysis</li>
                            <li>General web search for cricket info</li>
                        </ul>
                    </div>
                """)
                
        
        # Example questions
        with gr.Row():
            with gr.Column():
                gr.Examples(
                    examples=[
                        "Compare Virat Kohli and Steve Smith's Test careers",
                        "Tell me about Jasprit Bumrah's bowling statistics",
                        "How many hundreds does Virat Kohli have in Test, ODI, and T20 cricket?",
                        "Get current live cricket matches",
                        "What's the upcoming international cricket schedule?",
                        "Get the latest cricket news",
                        "Who are the top 10 ODI batsmen?",
                        "Show me the ICC Test bowling rankings",
                        "What are the T20 team rankings?",
                        "Get detailed scorecard for a recent match",
                        "Search web for latest update on Rohit Sharma injury",
                        "Search for live commentary of Zimbabwe vs New Zealand 2nd Test"
                    ],
                    inputs=msg_input,
                    label="💡 Try these example questions (notice how some refer to previous context):"
                )
        
        # Event handlers
        msg_input.submit(
            process_cricket_query,
            [msg_input, chatbot],
            [msg_input, chatbot],
        )
        
        send_btn.click(
            process_cricket_query,
            [msg_input, chatbot],
            [msg_input, chatbot],
        )
        
        clear_btn.click(
            fn=clear_chat,
            inputs=None,
            outputs=[chatbot, msg_input],
            queue=False
        )
        
    return demo

if __name__ == "__main__":
    print("🏏 Starting Cricket Statistics Assistant with Memory...")
    print("📊 Initializing cricket data sources and conversation memory...")
    
    # Create and launch the interface
    demo = create_interface()
    
    print("🚀 Launching chat interface with memory...")
    print("🌐 Open your browser to start chatting about cricket!")
    print("💬 The assistant will remember your last 5 exchanges for better context!")
    
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        show_api=False,
        share=False,
        inbrowser=True
    )
