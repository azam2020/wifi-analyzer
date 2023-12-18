from flask import Flask, render_template, request
import subprocess

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan')
def scan():
    # Your Wi-Fi scanning logic here
    result = subprocess.check_output(['sudo', 'iwlist', 'wlo1', 'scan'])
    return render_template('scan_wifi.html', wifi_info=result.decode('utf-8'))

@app.route('/block', methods=['POST'])
def block():
    ssid_to_block = request.form['ssid_to_block']
    # Your Wi-Fi blocking logic here
    # ...

    return render_template('index.html', message=f'Wi-Fi signal {ssid_to_block} blocked successfully.')

@app.route('/unblock', methods=['POST'])
def unblock():
    ssid_to_unblock = request.form['ssid_to_unblock']
    # Your Wi-Fi unblocking logic here
    # ...

    return render_template('index.html', message=f'Wi-Fi signal {ssid_to_unblock} unblocked successfully.')

if __name__ == '__main__':
    app.run(debug=True, port=5001)
