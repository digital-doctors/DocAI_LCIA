from flask import Flask, render_template, request, jsonify
import random
import time
import cohere
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64
from cohere import ClientV2
from flask import session
from flask_session import Session


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

@app.route('/send_report', methods=['POST'])
def send_report():
    try:
        data = request.get_json()

        # Validate the input data
        if not all(key in data for key in ["heart_rate", "hydration", "temperature", "blood_pressure"]):
            return jsonify({"error": "Invalid input data"}), 400

        # Generate the AI health report using Cohere API
        query = (
            f"Generate a professional health report based on the following:\n"
            f"- Heart Rate: {data['heart_rate']}\n"
            f"- Hydration Status: {data['hydration']}\n"
            f"- Temperature: {data['temperature']}\n"
            f"- Blood Pressure: {data['blood_pressure']}\n\n"
            f"Provide insights and recommendations in a clear and helpful way."
        )

        response = co.generate(
            model="command-light",
            prompt=query,
            max_tokens=300,
            temperature=0.7
        )
        ai_report = response.generations[0].text.strip()

        # Email setup
        sender_email = "Nikmaproducts@gmail.com"
        sender_password = "rqri izcc ybnd conx"  # Your app password
        recipient_email = "nikhi.kanda@gmail.com"

        # Subject and email body with vitals and AI report
        subject = "AI-Generated Patient Health Report"
        body = f"""Dear Doctor,

Here is the AI-generated health report for the patient:

Vital Health Data:
- Heart Rate: {data['heart_rate']}
- Hydration Status: {data['hydration']}
- Temperature: {data['temperature']}
- Blood Pressure: {data['blood_pressure']}

AI Insights and Recommendations:
{ai_report}

Best regards,
DocAI
"""

        # Set up the email
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Send the email
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)

        print(f"Email sent successfully to {recipient_email}")
        return jsonify({"message": "AI-generated report successfully sent to the doctor."})

    except cohere.error.CohereError as ce:
        print(f"Cohere API error: {str(ce)}")
        return jsonify({"error": f"Cohere API error: {str(ce)}"}), 500
    except Exception as e:
        print(f"Failed to send report: {str(e)}")
        return jsonify({"error": f"Failed to send report: {str(e)}"}), 500

@app.route('/submit-form', methods=['POST'])
def submit_form():
    try:
        form_data = request.form.to_dict()

        # Compile the form data into an email-style summary
        summary = "\n".join([f"{k.replace('_', ' ').title()}: {v}" for k, v in form_data.items()])

        # Email setup
        sender_email = "Nikmaproducts@gmail.com"
        sender_password = "rqri izcc ybnd conx"
        recipient_email = "nikhi.kanda@gmail.com"

        subject = "Patient Health Questionnaire Submission"
        body = f"""Dear Doctor,

The patient has completed the pre-consultation health questionnaire. Here's the summary:

{summary}

Best regards,
DocAI
"""

        # Send the email
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)

        print("Health form submitted and emailed successfully.")
        return "Form submitted successfully. Thank you!", 200

    except Exception as e:
        print(f"Error submitting form: {str(e)}")
        return f"Error submitting form: {str(e)}", 500

@app.route('/submit-patient', methods=['POST'])
def submit_patient():
    try:
        patient_data = request.form.to_dict()
        patient_summary = "\n".join([f"{k.replace('_', ' ').title()}: {v}" for k, v in patient_data.items()])

        sender_email = "Nikmaproducts@gmail.com"
        sender_password = "rqri izcc ybnd conx"
        recipient_email = "nikhi.kanda@gmail.com"

        subject = "New Patient Information Submission"
        body = f"""Dear Doctor,

A new patient has submitted their personal information:

{patient_summary}

Best regards,
DocAI
"""

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)

        print("Patient information submitted and emailed successfully.")
        return "Patient info submitted successfully.", 200

    except Exception as e:
        print(f"Error submitting patient info: {str(e)}")
        return f"Error: {str(e)}", 500

from huggingface_hub import InferenceClient

client = InferenceClient(
    provider="cohere",
    api_key="oaiXjisZYMP0ZrNLdEHKSPduxKpJSIKZLAzIJ2aZ",
)

@app.route('/analyze-image', methods=['POST'])
def analyze_image():
    try:
        uploaded_files = request.files.getlist("images")
        if not uploaded_files:
            return jsonify({"error": "No images uploaded"}), 400

        allowed_extensions = {"png", "jpg", "jpeg"}
        all_image_reports = []

        for image_file in uploaded_files:
            filename = image_file.filename.lower()
            if '.' not in filename or filename.rsplit('.', 1)[1] not in allowed_extensions:
                continue  # Skip invalid files

            image_bytes = image_file.read()
            mime_type = f"image/{filename.rsplit('.', 1)[1]}"
            data_url = f"data:{mime_type};base64,{base64.b64encode(image_bytes).decode()}"

            # Send request with image and text prompt
            completion = client.chat.completions.create(
                model="CohereLabs/aya-vision-8b",
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "This is a medical image. First, give a label on what the issue (disease, allergy, etc.) this may be. Then Describe any visible conditions or abnormalities you notice, respond like Medical Assistant with accuracy."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": data_url
                            }
                        }
                    ]
                }],
                max_tokens=512
            )

            feedback = completion.choices[0].message.get("content", "").strip()
            report = f"Report for {image_file.filename}:\n\n{feedback}"
            all_image_reports.append(report)

        if not all_image_reports:
            return jsonify({"error": "No valid images were processed."}), 400

        final_report = "\n\n---\n\n".join(all_image_reports)

        # Email setup
        sender_email = "Nikmaproducts@gmail.com"
        sender_password = "rqri izcc ybnd conx"
        recipient_email = "nikhi.kanda@gmail.com"

        subject = "AI-Based Medical Image Analysis"
        body = f"""Dear Doctor,

The following AI-generated analysis reports are based on the uploaded patient images:

{final_report}

Best regards,  
DocAI
"""

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)

        print("Image analysis report emailed successfully.")
        return jsonify({"message": "Image analysis report sent successfully."}), 200

    except Exception as e:
        print(f"Unexpected error during image analysis: {str(e)}")
        return jsonify({"error": f"Image analysis failed: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5001)
