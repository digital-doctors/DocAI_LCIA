from flask import Flask, render_template, request, jsonify
import random
import time
import cohere


app = Flask(__name__)

# Replace with your actual Cohere API key
COHERE_API_KEY = "oaiXjisZYMP0ZrNLdEHKSPduxKpJSIKZLAzIJ2aZ"
co = cohere.Client(COHERE_API_KEY)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/get_reports')
def get_reports():
    reports = [
        "Report 1: Normal",
        "Report 2: Mild Dehydration",
        "Report 3: Elevated Heart Rate"
    ]
    return jsonify({"reports": reports})


@app.route('/analyze', methods=['GET'])
def analyze():
    try:
        time.sleep(3)  # Simulating a health analysis process

        # Generate random health data
        health_data = {
            "heart_rate": f"{random.randint(65, 100)} BPM",
            "hydration": random.choice(["Normal", "Mild Dehydration", "Severe Dehydration"]),
            "temperature": f"{round(random.uniform(97.0, 99.5), 1)} °F",
            "blood_pressure": f"{random.randint(110, 135)}/{random.randint(70, 90)} mmHg"
        }
        return jsonify(health_data)
    
    except Exception as e:
        return jsonify({"error": f"Failed to analyze health data: {str(e)}"}), 500


@app.route('/report', methods=['POST'])
def report():
    try:
        data = request.get_json()

        # Validate input data
        if not all(key in data for key in ["heart_rate", "hydration", "temperature", "blood_pressure"]):
            return jsonify({"error": "Invalid input data"}), 400

        # Generate a query for the Cohere API
        query = (
            f"Generate a professional health report based on the following:\n"
            f"- Heart Rate: {data['heart_rate']}\n"
            f"- Hydration Status: {data['hydration']}\n"
            f"- Temperature: {data['temperature']}\n"
            f"- Blood Pressure: {data['blood_pressure']}\n\n"
            f"Provide insights and recommendations in a clear and helpful way."
        )

        # Call Cohere API to generate the report
        response = co.generate(
            model="command-light",
            prompt=query,
            max_tokens=300,
            temperature=0.7
        )
        ai_report = response.generations[0].text.strip()
        return jsonify({"report": ai_report})
    except cohere.error.CohereError as ce:
        return jsonify({"error": f"Cohere API error: {str(ce)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Failed to generate health report: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5001)
