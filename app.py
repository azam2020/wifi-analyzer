from flask import Flask, render_template, request
import subprocess
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import os
import re

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

def scan():
	scan_result = subprocess.check_output(['sudo','iwlist','wlan0','scan'])
	scan_result = scan_result.decode('utf-8')
	return scan_result


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
@app.route('/plot')
def plot_function():
	grouped_networks = filter_blocked_wifi(scan())
	x = []
	y = []
	for ssid in grouped_networks:
		x.append(ssid)
		y.append(grouped_networks[ssid]['Signal Strength'][0])
	plt.figure(figsize=(10,6))
	plt.bar(x,y,color='blue')
	font1 = {'family':'serif','color':'darkred','size':15}
	font2 = {'family':'serif','color':'green','size':20}
	#plt.title('Plot',fontdict=font2)
	plt.xlabel('SSID Name',fontdict=font1)
	plt.ylabel('Signal Strength(dbm)',fontdict=font1)
	
	plt.xticks(rotation=30,ha='right')
	plt.tight_layout()
	path = os.path.join('static','plot.png')
	plt.savefig(path)
	plt.close()
	return render_template('plot.html',img=path)

@app.route('/connected_wifi')
def connected_wifi():
	result = subprocess.check_output(['iwgetid'])
	result = result.decode('utf-8').strip()
	index = result.find('SSID:')
	if index!=-1:
		ssid = result[index+6:].strip('"')
		return render_template('index.html', message = f"System is connected to {ssid} click on more to get more info.")
	else:
		return render_template('index.html', message = f"System is not connected to any wifi.")

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

@app.route('/more',methods=['POST'])
def more():
	input_ssid = request.form['input_ssid']
	if input_ssid in grouped_blocks:
		return render_template('more_info.html',details = grouped_blocks[input_ssid]['blocks'])
	else:
		return render_template('index.html',message = f"Wifi signal {input_ssid} is not found, please check if it is present in the available wifi list or not")
 

@app.route('/connect')
def connect():
	return render_template('connect.html')

@app.route('/connect_to_given_input',methods=['POST'])
def connect_to_given_input():
	input_ssid = request.form['input_ssid']
	pwd = request.form['pwd']
	grouped_networks = filter_blocked_wifi(scan())
	if input_ssid not in grouped_networks:
		return render_template('connect.html',message=f"WiFi signal {input_ssid} not found")
	else:
		result = subprocess.run(['sudo','nmcli','device','wifi','connect',input_ssid,'password',pwd])
		if result.returncode==0:
			return render_template('connect.html',message=f"Devices connected to {input_ssid}")
		else:
			return render_template('connect.html',message=f"Unable to connect {input_ssid}")

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

@app.route('/ping')
def ping():
	return render_template('ping.html')

@app.route('/ping_to_input_ip',methods=['POST'])
def ping_to_input_ip():
	ip = request.form['input_ip']
	c=0
	try:
		result = subprocess.check_output(['ping','-c', '9', ip],universal_newlines=True)
	except subprocess.CalledProcessError as e:
		c = e.returncode
	if c!=0:
		return render_template('ping.html',message=f"Ping request could not find host {ip}. Please check the name and try again.")
	else:
		#result = result.decode('utf-8')
		time = re.findall(r"time=[0-9][0-9]?[0-9]?", result)
		received = re.findall(r"[0-9] received",result)
		l = []
		for x in time:
			t = x[5:]
			t = int(t)
			l.append(t)
		
		min_time = min(l)
		max_time = max(l)
		avg_time = int(sum(l)/len(l))
		s_packet = 9
		r_packet = int(received[0][0:1])
		l_packet = s_packet-r_packet
		l_percent = (l_packet/9)*100
		x_axis = [1,2,3,4,5,6,7,8,9]
		d = {'Target host':ip, 'Average ping':avg_time,'Minimum ping':min_time,'Maximum ping':max_time,'Packet loss':l_percent}
		plt.plot(l,color='blue',marker='o')
		#plt.xticks([])
		font1 = {'family':'serif','color':'darkred','size':15}
		plt.xlabel('Ping Number',fontdict = font1)
		plt.ylabel('Ping Time (ms)', fontdict=font1)
		plt.grid(axis='y',)
		path = os.path.join('static','ping.png')
		plt.savefig(path)
		plt.close()
		return render_template('ping_to_inputip.html',info=d)
	

@app.route('/speed_test')
def speed_test():
	result = subprocess.check_output(['sudo','speedtest-cli','--share'])
	result = result.decode('utf-8')
	m = re.search(r'http[s]?://[^\s]+',result)
	if m:
		link = m.group(0)
	else:
		link = None
	return render_template('speed.html',link=link)

@app.route('/documentation')
def documentation():
	return render_template('documentation.html')

if __name__=='__main__':
	app.run(host='0.0.0.0',debug=True)
