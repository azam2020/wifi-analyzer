from flask import Flask, render_template, request
import subprocess
app = Flask(__name__)

grouped_blocks = {}

@app.route('/')
def index():
	return render_template('index.html')

def read_file():
	with open("blocked_signal.txt", 'r') as file:
		return [line.strip() for line in file.readlines()]
def write_file(ssid):
	with open("blocked_signal.txt", 'w') as file:
		file.write('\n'.join(ssid))

@app.route('/block_function',methods=['POST'])
def block_function():
	grouped_networks = filter_blocked_wifi(scan())
	input_ssid = request.form['input_ssid']
	if input_ssid in grouped_networks:
		total_blocked_ssid = read_file() 
		total_blocked_ssid.append(input_ssid) 
		write_file(total_blocked_ssid)
		del grouped_blocks[input_ssid]
		return render_template('index.html', message=f'Wifi signal {input_ssid} has been blocked successfully.')
	else:
		return render_template('index.html',message=f'Wifi signal {input_ssid} is not found')



@app.route('/unblock_function',methods=['POST'])
def unblock_function():
	total_blocked_ssid = read_file()
	input_ssid = request.form['input_ssid']
	if input_ssid in total_blocked_ssid:
		total_blocked_ssid.remove(input_ssid)
		write_file(total_blocked_ssid) 
		filter_blocked_wifi(scan())
		return render_template('index.html',message = f'Wifi signal {input_ssid} has been unblocked successfully')
	else:
		return render_template('index.html',message = f'Wifi signal {input_ssid} is not found in the blocked wifi list')

@app.route('/blocked_wifi')
def display_blocked_wifi():
	total_blocked_wifi = read_file()
	if len(total_blocked_wifi)!=0:
		return render_template('blocked_wifi.html',blocked_list = total_blocked_wifi)
	else:
		return render_template('index.html',message = "Nothing to display -> blocked wifi list is empty")

@app.route('/reset')
def reset():
	subprocess.check_output(['rm', 'blocked_signal.txt'])
	subprocess.check_output(['touch','blocked_signal.txt'])
	return render_template('index.html',message = "All blocked wifi signlas have been successfully unblocked.")

def scan():
	scan_result = subprocess.check_output(['sudo','iwlist','wlan0','scan'])
	scan_result = scan_result.decode('utf-8')
	return scan_result

@app.route('/more',methods=['POST'])
def more():
	input_ssid = request.form['input_ssid']
	if input_ssid in grouped_blocks:
		return render_template('more_info.html',details = grouped_blocks[input_ssid]['blocks'])
	else:
		return render_template('index.html',message = f"Wifi signal {input_ssid} is not found, please check if it is present in the available wifi list or not")
 

@app.route('/scan_wifi')
def scan_wifi():
	scan_result = scan() 
	filter_result = filter_blocked_wifi(scan_result)
	return render_template('scan_wifi.html',wifi_info=filter_result)

def filter_blocked_wifi(scan_result):
	wifi_blocks = scan_result.split('Cell') 
	total_blocked_ssid = read_file() 
	filtered_blocks = [] 
	for block in wifi_blocks: 
		if not any(ssid in block for ssid in total_blocked_ssid):
			filtered_blocks.append(block)

	grouped_networks = {}
 
	for block in filtered_blocks:
		ssid = extract_data(block, 'ESSID:') 
		signal_strength = extract_data(block, 'Signal level=') 
		frequency = extract_data(block, 'Frequency:') 
		encryption = extract_data(block, 'Encryption key:') 
		key = ssid
 
		if key not in grouped_networks:
			grouped_networks[key] = {'Signal Strength' : [], 'Frequency' : [], 'Encryption key' : [] } 
		grouped_networks[key]['Signal Strength'].append(signal_strength) 
		grouped_networks[key]['Frequency'].append(frequency) 
		grouped_networks[key]['Encryption key'].append(encryption)

		if key not in grouped_blocks:
        		grouped_blocks[key] = {'blocks' : []}
		grouped_blocks[key]['blocks'].append(block)
	del grouped_networks[None]
	return grouped_networks


def extract_data(block, var):
	start_index = block.find(var)
	if start_index != - 1:
		start_index += len(var)
		end_index = block.find('\n', start_index)
		if end_index != - 1:
			return block[start_index:end_index].strip('"')


if __name__=='__main__':
	app.run(host='0.0.0.0',port=5000,debug=True)

