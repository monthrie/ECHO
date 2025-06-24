import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from second_brain.runthexp.anon.anon_PII import EntityAnonymizer, Config

# Configure for OpenRouter
Config.USE_OPENROUTER = True
Config.OPENROUTER_MODEL = 'mistralai/mistral-small-3.1-24b-instruct'
Config.LLM_MODEL = 'mistralai/mistral-small-3.1-24b-instruct'  # Use same model for both

# Create anonymizer
anonymizer = EntityAnonymizer()

# Complex test text
test_text = """Last week, I had a meeting with my team at Google's Mountain View headquarters. 
My manager Sarah introduced me to two new colleagues: Alex from the London office and Priya who recently transferred from Microsoft. 
We discussed our upcoming project with our client, Acme Corp, where we'll be working with their CTO, Dr. James Wilson. 
After the meeting, I had lunch with my friend Mike, who works at Apple, and we talked about his recent trip to Tokyo where he met with our mutual friend Emma, who now works at Sony. 
Later that day, I called my sister Lisa to tell her about my new project, and she mentioned that her husband Tom, who works at Amazon, might be interested in collaborating. 
The next morning, I had a video call with our team in Bangalore, including Rajesh and Meera, who are leading the technical implementation. 
We're planning to visit their office next month to finalize the project details."""

# First show the anonymization
print("Step 1: Anonymization")
print("Original Text:")
print(test_text)
result = anonymizer.anonymize_text(test_text)
print("\nAnonymized Text:")
print(result["anonymized_text"])
print("\nEntity Mapping:")
for original, alias in result["entity_mapping"].items():
    print(f"{original} -> {alias}")

# Now demonstrate LLM query
print("\nStep 2: LLM Query")
test_query = "What can you tell me about the relationships between Mike, Emma, and Lisa?"
print("\nTest Query:", test_query)
llm_response = anonymizer.query_llm(test_query)
print("\nLLM Response:")
print(llm_response)

# Demonstrate chat with context
print("\nStep 3: Chat with Context")
messages = [
    {"role": "user", "content": "Who are all the people that work at Google?"},
    {"role": "assistant", "content": "Based on the information provided, Sarah, Alex, and Priya work at Google's Mountain View headquarters."},
    {"role": "user", "content": "And what about Mike and Emma, where do they work?"}
]
print("\nChat Messages:")
for msg in messages:
    print(f"{msg['role'].upper()}: {msg['content']}")
chat_response = anonymizer.chat_with_context(messages)
print("\nChat Response:")
print(chat_response) 