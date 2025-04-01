from flask import Flask, render_template, request, jsonify
import cohere

app = Flask(__name__)

# Cohere API setup
COHERE_API_KEY = "OC7WvIc3z7pwMRiQL3VpcRTmsqcHG1oAVgL7jPOA"
co = cohere.Client(COHERE_API_KEY)

# Store chat history per session (basic memory)
chat_history = {}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    doctor_name = data.get("doctor", "Doctor")
    user_message = data.get("message", "")

    # Store conversation history per doctor
    if doctor_name not in chat_history:
        chat_history[doctor_name] = []
    
    # Append user message to history
    chat_history[doctor_name].append(f"User: {user_message}")

    # Generate a chat-aware query
    chat_context = "\n".join(chat_history[doctor_name][-5:])  # Keep last 5 messages for context
    query = (
        f"You are {doctor_name}, a friendly and knowledgeable doctor. "
        f"Keep responses brief (1-2 sentences) and relevant to the conversation. "
        f"Refer to the chat history to maintain context. If needed, gently recommend professional help. "
        f"\n\n{chat_context}\n{doctor_name}:"
    )

    try:
        response = co.generate(
            model="command",
            prompt=query,
            max_tokens=50,  # Enforces short responses
            temperature=0.7,
            stop_sequences=["User:", f"{doctor_name}:"]
        )

        ai_response = response.generations[0].text.strip() if response.generations else "I'm not sure, could you clarify?"

    except Exception as e:
        print(f"Error with Cohere API: {str(e)}")
        ai_response = "Sorry, I had trouble understanding that."

    # Append AI response to history
    chat_history[doctor_name].append(f"{doctor_name}: {ai_response}")

    return jsonify({"response": ai_response})

if __name__ == '__main__':
    app.run(debug=True)
