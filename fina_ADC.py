import minimalmodbus
import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from BlynkLib import Blynk

# Blynk Template Name and Authentication Token
BLYNK_TEMPLATE_NAME = "Cassava value chain"
BLYNK_AUTH_TOKEN = "JQQkNXMGjdjQnTtWbV_654OuxzLsbyQy"

# Create the Blynk instance
blynk = Blynk(BLYNK_AUTH_TOKEN)

# Create the I2C bus
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)
chan = AnalogIn(ads, ADS.P1)

# Define the commands
COMMANDS = {
    'Temperature': {'address': 0x13, 'length': 2, 'name': 'field1'},
    'Moisture': {'address': 0x12, 'length': 2, 'name': 'field2'},
    'Conductivity': {'address': 0x15, 'length': 1, 'name': 'field3'},
    'pH': {'address': 0x06, 'length': 1, 'name': 'field4'},
    'Nitrogen': {'address': 0x1E, 'length': 1, 'name': 'field5'},
    'Phosphorus': {'address': 0x1F, 'length': 1, 'name': 'field6'},
    'Potassium': {'address': 0x20, 'length': 1, 'name': 'field7'}
}

# Serial port configuration
instrument = minimalmodbus.Instrument('/dev/ttyUSB1', 1)  # port name, slave address (1 in this example)
instrument.serial.baudrate = 9600
instrument.serial.bytesize = 8
instrument.serial.parity = minimalmodbus.serial.PARITY_NONE
instrument.serial.stopbits = 1
instrument.serial.timeout = 1  # seconds

def adc_to_voltage(value):
    return value / 32767 * 3.3

def read_sensor_data_adc(channel):
    try:
        value = channel.value
        voltage = adc_to_voltage(value)
        return voltage
    except Exception as e:
        print("Error reading ADC sensor data:", e)
        return None

def read_sensor_data(command):
    try:
        # Read registers from the sensor
        response = instrument.read_registers(command['address'], command['length'])
        # Interpret the response (assuming it's a 16-bit integer)
        value = minimalmodbus._twos_complement(response[0], 16)

        # Apply specific adjustments based on sensor type
        if command['name'] == 'Temperature':
            # Divide temperature values by 10
            value /= 10
        elif command['name'] == 'pH':
            # Divide pH value by 100
            value /= 10000

        # Ensure moisture value does not exceed 100
        if command['name'] == 'Moisture':
            value = min(value, 100)

        return value
    except Exception as e:
        print("Error reading sensor data:", e)
        return None

def send_to_blynk(data):
    try:
        for field, value in data.items():
            if field == 'GS_Sensor':
                blynk.virtual_write(8, value)  # Write to virtual pin 8 for GS_Sensor
            else:
                field_index = int(field[-1])  # Extract the field number from the field name
                blynk.virtual_write(field_index, value)  # Write to corresponding virtual pin
        print("Data sent to Blynk successfully.")
    except Exception as e:
        print("Error sending data to Blynk:", e)

def main():
    while True:
        data = {}

        # Read data from ADC sensor (GS sensor)
        adc_value = read_sensor_data_adc(chan)
        if adc_value is not None:
            data['GS_Sensor'] = adc_value
            print("GS Sensor:", adc_value)
        else:
            data['GS_Sensor'] = 'Error'
            print("GS Sensor: Error reading data")

        # Read data from other sensors
        for data_type, command in COMMANDS.items():
            value = read_sensor_data(command)
            if value is not None:
                if data_type == 'Temperature':
                    value /= 10  # Divide temperature values by 10
                elif data_type == 'pH':
                    value /= 100  # Divide pH values by 100
                elif data_type == 'Moisture':
                    value = min(value, 100)  # Ensure moisture value does not exceed 100
                data[data_type] = value
                print("{}: {}".format(data_type, value))
            else:
                data[data_type] = 'Error'
                print("{}: Error reading data".format(data_type))
       
        # Send data to Blynk
  
