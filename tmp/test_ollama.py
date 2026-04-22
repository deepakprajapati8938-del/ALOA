import os
from dotenv import load_dotenv
from aloa.llm.providers import get_fallback_chain

load_dotenv('aloa/.env')

def test_ollama():
    print(f"OLLAMA_URL: {os.getenv('OLLAMA_URL')}")
    print(f"OLLAMA_MODEL: {os.getenv('OLLAMA_MODEL')}")
    
    chain = get_fallback_chain()
    if not chain:
        print("❌ No providers found!")
        return
    
    provider = chain[0]
    print(f"Testing provider: {type(provider).__name__} (Model: {provider.model_name})")
    
    prompt = "Say 'Ollama is Ready' if you can hear me."
    print("Sending prompt...")
    try:
        response = provider.generate(prompt)
        if response:
            print(f"✅ Response: {response}")
        else:
            print("❌ No response from provider.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_ollama()
