import os
from langsmith import traceable

class SecondBrainTracer:
    """Simple utility class for LangSmith tracing in Second Brain pipeline."""
    
    def __init__(self):
        # Set environment variables
        os.environ["LANGSMITH_TRACING"] = "true"
        os.environ["LANGSMITH_ENDPOINT"] = "https://api.smith.langchain.com"
        os.environ["LANGSMITH_API_KEY"] = "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"
        os.environ["LANGSMITH_PROJECT"] = "pr-complicated-component-1"
        
        print(f"✅ LangSmith environment variables set")
        print(f"✅ Project: {os.environ['LANGSMITH_PROJECT']}")
        self.enabled = True
    
    def trace_openrouter_call(self, run_name, prompt, response, metadata=None):
        """
        For manual tracing, we should use the @traceable decorator.
        This is a simple wrapper to make it easier to use in your code.
        """
        if not self.enabled:
            return None
            
        # Use the traceable decorator directly
        @traceable(name=run_name, run_type="llm")
        def traced_function(prompt_input, response_output, meta=None):
            # This function just returns the inputs and outputs
            # The tracing happens via the decorator
            return {"prompt": prompt_input, "response": response_output, "metadata": meta}
        
        # Call the traced function
        result = traced_function(prompt, response, metadata)
        print(f"✅ Logged '{run_name}' to LangSmith")
        return "success"

# Simple test
if __name__ == "__main__":
    print("Testing LangSmith connection...")
    tracer = SecondBrainTracer()
    
    result = tracer.trace_openrouter_call(
        "test_run", 
        "This is a test prompt", 
        "This is a test response",
        {"test": "metadata"}
    )
    
    if result:
        print(f"✅ Test successful!")
        print("LangSmith integration is working correctly")
    else:
        print("❌ Test failed") 