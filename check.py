import google.generativeai as genai
import os

print("--- Checking your API key's available models ---")

try:
   
    GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']
    genai.configure(api_key=GOOGLE_API_KEY)
    print("API key found. Listing models...\n")

   
    found_model = False
    for m in genai.list_models():
   
        if 'generateContent' in m.supported_generation_methods:
            
            model_name_for_code = m.name.split('/')[-1]
            
            print(f"✅ Found usable model!")
            print(f"   Model name for your code: {model_name_for_code}")
            print(f"   (Full API name: {m.name})")
            print(f"   Description: {m.description}\n")
            found_model = True

    if not found_model:
        print("❌ No models with 'generateContent' method found for your API key.")
    else:
        print("\n--- ACTION REQUIRED ---")
        print("Look at the 'Model name for your code' from the list above.")
        print("model = genai.GenerativeModel('...')")


except KeyError:
    print("Error: GOOGLE_API_KEY not found.")
    print("Please set the environment variable before running this script.")
except Exception as e:
    print(f"An error occurred: {e}")