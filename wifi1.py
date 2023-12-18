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
	ssid_to_block = request.form['ssid_to_block']
	if ssid_to_block in grouped_networks:
		total_blocked_ssid = read_file() 
		total_blocked_ssid.append(ssid_to_block) 
		write_file(total_blocked_ssid)
		del grouped_blocks[ssid_to_block]
		return render_template('index.html', message=f'wifi signal {ssid_to_block} has been successfully blocked')
	else:
		return render_template('index.html',f'wifi signal {ssid_to_block} is not found')



@app.route('/unblock_function',methods=['POST'])
def unblock_function():
	total_blocked_ssid = read_file()
	ssid_to_unblock = request.form['ssid_to_unblock']
	if ssid_to_unblock in total_blocked_ssid:
		total_blocked_ssid.remove(ssid_to_unblock)
		write_file(total_blocked_ssid) 
		filter_blocked_wifi(scan())
		return render_template('index.html',message = f'wifi signal {ssid_to_unblock} is unblocked')
	else:
		return render_template('index.html',message = f'wifi signal {ssid_to_unblock} is not found in the blocked wifi list')

@app.route('/blocked_wifi')
def display_blocked_wifi():
	total_blocked_wifi = read_file()
	if len(total_blocked_wifi)!=0:
		return render_template('blocked_wifi.html',blocked_list = total_blocked_wifi)
	else:
		return render_template('index.html',message = "Nothing to display -> blocked list is empty")

@app.route('/reset')
def reset():
	subprocess.check_output(['rm', 'blocked_signal.txt'])
	subprocess.check_output(['touch','blocked_signal.txt'])
	return render_template('index.html',message = "All blocked wifi signals are deleted")

def scan():
	scan_result = subprocess.check_output(['sudo','iwlist','wlo1','scan'])
	scan_result = scan_result.decode('utf-8')
	return scan_result

@app.route('/more',methods=['POST'])
def more():
	ssid = request.form['ssid_for_more_info']
	if ssid in grouped_blocks:
		return render_template('more_info.html',details = grouped_blocks[ssid]['blocks'])
	else:
		return render_template('index.html',message = "SSID not found, please check if it is present in the available wifi or not")
 

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
	app.run(debug=True,port=5001)

"""
while (True):
	option = input('''
                    Enter 's' to scan all the available wifi signals: 
                    Enter 'b' to block a wifi signal:
                    Enter 'u' to unblock a wifi signal:
                    Enter 'l' to list down all the blocked wifi signals:
                    Enter 'm' to know more about a wifi signal:
		    Enter 'r' to remove all blocked wifi signals:
                    Enter 'q' to stop the program:\n		''')
	print("-------------------------------------------------------------------------------------------------------")

	if option == "s":
		print("scanning available wifi signals.....")
		scan_result = scan_wifi()
		filter_result = filter_blocked_wifi(scan_result)
		display_result(filter_result)

	elif option == "b":
		x = input("Enter ssid which you want to block: ") 
		block_function(x)

	elif option == 'u':
		ssid = input("Enter ssid which you want to unblock: ") 
		unblock_function(ssid)

	elif option == 'l':
		display_blocked_wifi()

	elif option == "m":
		ssid = input("Enter ssid whose details you want: ") 
		if ssid in grouped_blocks:
			block = grouped_blocks[ssid]['blocks'] 
			for x in block:
				print(x)
		else:
			print(f"wifi signal {ssid} is not found, check if it is present in the available wifi list or not") 
		print("--------------------------------------------------------------------------------------------------")

	elif option=='r':
		reset()

	elif option == "q":
		break

	else:

		print("Invalid input, choose from the given options.") 
		print("-----------------------------------------------------------------------------------------------------------")

"""
