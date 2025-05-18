from flask import Flask, render_template, request, jsonify, session
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import random
import time
import smtplib
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from cohere import Client
from flask_session import Session
from huggingface_hub import InferenceClient
import numpy as np
from PIL import Image
from scipy.signal import butter, filtfilt, find_peaks
import io

# Initialize Flask app
app = Flask(__name__)

# Configurations for Flask session
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = '2029240f6d1128be89ddc32729463129'
Session(app)

# Set Cohere API key and initialize client
COHERE_API_KEY = "oaiXjisZYMP0ZrNLdEHKSPduxKpJSIKZLAzIJ2aZ"
co = Client(COHERE_API_KEY)

# Set up Huggingface API client
client = InferenceClient(
    provider="cohere",
    api_key=COHERE_API_KEY
)

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect('http://127.0.0.1:5000/login')  # Redirect to login if user is not in session
        return f(*args, **kwargs)  # Allow access to the decorated function if user is in session
    return decorated_function


# Bandpass filter for signal processing
def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    return butter(order, [low, high], btype='band')

def bandpass_filter(data, lowcut=0.75, highcut=2.5, fs=30, order=5):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    return filtfilt(b, a, data)

def moving_average(data, window_size=5):
    """Simple moving average filter."""
    return np.convolve(data, np.ones(window_size) / window_size, mode='valid')

# Routes
@app.route('/')
@login_required
def home():
    return render_template('index.html')

@app.route('/get_reports')
@login_required
def get_reports():
    reports = [
        "Report 1: Normal",
        "Report 2: Mild Dehydration",
        "Report 3: Elevated Heart Rate"
    ]
    return jsonify({"reports": reports})


@app.route('/submit-form', methods=['POST'])
@login_required
def submit_form():
    try:
        form_data = request.form.to_dict()

        # Compile the form data into an email-style summary
        summary = "\n".join([f"{k.replace('_', ' ').title()}: {v}" for k, v in form_data.items()])

        # Send email with summary
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

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)

        return "Form submitted successfully. Thank you!", 200
    except Exception as e:
        return f"Error submitting form: {str(e)}", 500

@app.route('/submit-patient', methods=['POST'])
@login_required
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

        return "Patient info submitted successfully.", 200
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/analyze-image', methods=['POST'])
@login_required
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
                            "text": "This is a medical image. First, give a label on what the issue (disease, allergy, etc.) this may be. Then describe any visible conditions or abnormalities you notice, respond like Medical Assistant with accuracy."
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

        return jsonify({"message": "Image analysis report sent successfully."}), 200
    except Exception as e:
        return jsonify({"error": f"Image analysis failed: {str(e)}"}), 500

@app.route('/analyze_ppg', methods=['POST'])
@login_required
def analyze_ppg():
    try:
        data = request.get_json()
        fps = data.get("fps", 30)  # Default to 30 FPS if not provided
        frames = data.get("frames", [])

        if not frames or len(frames) < 20:
            return jsonify({"error": "Not enough data frames provided"}), 400

        green_intensities = []
        red_intensities = []

        # Process each frame
        for frame in frames:
            try:
                # Decode the base64 image
                image_data = base64.b64decode(frame.split(",")[1])
                image = Image.open(io.BytesIO(image_data)).convert("RGB")
                pixels = np.array(image)

                # Extract green and red channel intensities
                green_avg = np.mean(pixels[:, :, 1])  # Green channel
                red_avg = np.mean(pixels[:, :, 2])    # Red channel

                green_intensities.append(green_avg)
                red_intensities.append(red_avg)
            except Exception as e:
                print(f"Error processing frame: {e}")
                continue

        # Ensure we have enough data
        if len(green_intensities) < 20:
            return jsonify({"error": "Not enough valid frames for analysis"}), 400

        # Heart Rate Calculation
        green_signal = np.array(green_intensities)
        green_signal -= np.mean(green_signal)  # Remove DC component
        filtered_signal = bandpass_filter(green_signal, lowcut=0.75, highcut=2.5, fs=fps, order=4)

        # Find peaks in the filtered signal
        peaks, _ = find_peaks(filtered_signal, distance=fps / 2)  # Minimum 0.5 seconds between peaks
        if len(peaks) > 1:
            ibi = np.diff(peaks) / fps  # Inter-beat intervals in seconds
            heart_rate = int(60 / np.mean(ibi))  # Convert to BPM
        else:
            heart_rate = None

        # Temperature Estimation
        if len(red_intensities) >= fps:
            smoothed_red = moving_average(red_intensities[-fps:], window_size=5)
            temp_index = np.mean(smoothed_red)
            temperature = round((34.0 + (temp_index - 100) * 0.05) * 9 / 5 + 32, 1)
        else:
            temperature = None

        

        # Generate and send the health report
        return generate_ppg_report(co, heart_rate, temperature)

    except Exception as e:
        return jsonify({"error": f"Error analyzing PPG: {str(e)}"}), 500


def generate_ppg_report(cohere, heart_rate, temperature):
    try:
        # Generate AI health report using Cohere API
        query = (
            f"You are a helpful doctor. Please generate a professional health report based on the following:\n"
            f"- Heart Rate: {heart_rate}\n"
            f"- Temperature: {temperature}\n"
            f"Provide insights and recommendations in a clear and helpful way."
        )

        response = cohere.generate(
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
- Heart Rate: {heart_rate}
- Temperature: {temperature}

AI Insights and Recommendations:
{ai_report}

Best regards,
DocAI
"""

        # Set up and send email
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)

        return jsonify({"message": "AI-generated report successfully sent to the doctor."})
    
    except cohere.error.CohereError as ce:
        return jsonify({"error": f"Cohere API error: {str(ce)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Failed to send report: {str(e)}"}), 500 

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)