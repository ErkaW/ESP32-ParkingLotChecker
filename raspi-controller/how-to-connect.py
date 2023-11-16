from flask import Flask, render_template
import requests

app = Flask(__name__)

@app.route('/')
def index():
    # Replace 'raspberry_pi_ip' with the actual IP address of your Raspberry Pi
    raspberry_pi_url = 'http://raspberry_pi_ip:5000/'
    
    # Make an HTTP GET request to the Raspberry Pi server
    response = requests.get(raspberry_pi_url)
    
    # Extract and display the response content
    status = response.text
    return f'Status from Raspberry Pi: {status}'

if __name__ == '__main__':
    app.run(debug=True)
