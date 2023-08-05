from configparser import ConfigParser
from mysql.connector import MySQLConnection, Error 
from collections import OrderedDict 
import datetime 
import pkg_resources

#Reads database parameters from .ini file
def read_db_config(filename='config.ini', section='mariadb'):
    DATA_PATH = pkg_resources.resource_filename('modules', filename)
    parser = ConfigParser()
    parser.read(DATA_PATH)
    db = {}
    if parser.has_section(section):
        items = parser.items(section)
        for item in items:
            db[item[0]] = item[1]
    else:
        raise Exception('{0} not found in the {1} file'.format(section, filename))
    return db
 
#Returns all rows from a cursor as a list of dicts
def dictFetchAll(cursor):
    desc = cursor.description
    return [OrderedDict(zip([col[0] for col in desc], row)) 
            for row in cursor.fetchall()]
    
#Database write operation
def write_operation(query):
    out = False
    try:
        db_config = read_db_config()
        conn = MySQLConnection(**db_config)
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
	out = True
    except Error as error:
        out = False
        print(str(error) + " at " + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    finally:
        if 'cursor' in locals():
            cursor.close()            
        if 'conn' in locals():
            conn.close()
        
    return out

def createUploadStatus(a_table, a_device_id, a_datetime):
    if a_device_id == None:
        query = """INSERT into upload_status (table_name, created, updated, last_uploaded_datetime) 
                VALUES ('%s', NOW(), NOW(), '%s')""" %(a_table, a_datetime)
    else:
        query = """INSERT into upload_status (table_name, device_id, created, updated, last_uploaded_datetime) 
                VALUES ('%s', '%s', NOW(), NOW(), '%s')""" %(a_table, a_device_id, a_datetime)
    return write_operation(query)

def updateUploadStatus(a_table, a_device_id, a_datetime):
    if a_device_id == None:
        query = "UPDATE upload_status SET last_uploaded_datetime = '%s' WHERE table_name ='%s'" %(a_datetime, a_table)
    else:
        query = "UPDATE upload_status SET last_uploaded_datetime = '%s' WHERE table_name ='%s' and device_id = '%s'" %(a_datetime, a_table, a_device_id)
    return write_operation(query)

def createEGaugeRecord(a_table, a_timestamp, a_device_id, a_data):
    query = "INSERT INTO %s (device_id, timestamp, data) VALUES ('%s','%s','%s')"%(a_table, a_device_id, a_timestamp, a_data)
    return write_operation(query)

#Database read operation
def read_operation(query):
    try:
        db_config = read_db_config()
        conn = MySQLConnection(**db_config)
        cursor = conn.cursor()
        cursor.execute(query)
        data = {"success": True, "data": dictFetchAll(cursor)}
    except Error as error:
        print(str(error) + " at " + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        data = {"success": False}
    finally:
        if 'cursor' in locals():
            cursor.close()            
        if 'conn' in locals():
            conn.close()
    return data

def readUploadStatus(a_table, a_device_id):
    if a_device_id == None:
        query = """SELECT * FROM upload_status WHERE table_name = '%s'""" %(a_table)
    else:
        query = """SELECT * FROM upload_status WHERE table_name = '%s' and device_id='%s'""" %(a_table, a_device_id)
        #print(query)
    out = read_operation(query)
    return out

def readEntrysBetweenDates(a_table, a_device_id, a_from_date, a_to_date):
    if a_device_id == None:
        query = """SELECT * FROM %s WHERE timestamp BETWEEN '%s' AND '%s'"""%(a_table, a_from_date, a_to_date)
    else:
        query = """SELECT * FROM %s WHERE device_id = '%s' AND timestamp BETWEEN '%s' AND '%s'"""%(a_table, a_device_id, a_from_date, a_to_date)
    #print(query)
    return read_operation(query)

def readNEntrysFromDate(a_table, a_device_id, a_from_date, a_n):
    if a_device_id == None:
        query = """SELECT * FROM %s WHERE timestamp >= '%s' ORDER BY timestamp ASC LIMIT %d"""%(a_table, a_from_date, a_n)
    else:
        query = """SELECT * FROM %s WHERE device_id = '%s' AND timestamp >= '%s' ORDER BY timestamp ASC LIMIT %d"""%(a_table, a_device_id, a_from_date, a_n)
    return read_operation(query)

def read_first_entry(a_table, a_device_id):
    if a_device_id == None:
        query = "SELECT * FROM %s order by id limit 1" %(a_table)
    else:
        query = "SELECT * FROM %s WHERE device_id = '%s' order by id limit 1" %(a_table, a_device_id)
    return read_operation(query)

def read_last_upload_datetime(a_device_id):
    query = "SELECT MIN(last_uploaded_datetime) AS last_uploaded_datetime FROM upload_status WHERE device_id = '%s'"%(a_device_id)
    print(query)
    return read_operation(query)

def last_entry_from_date(a_table, a_from_date, a_to_date, a_device_id):
    query = "SELECT * FROM %s WHERE timestamp BETWEEN '%s' AND '%s' and device_id = '%s' order by id DESC limit 1" %(a_table, a_from_date, a_to_date, a_device_id) 
    return read_operation(query)  

def delete_entries(a_table, a_first_id, a_last_id, a_device_id):
    query = "DELETE FROM %s WHERE id BETWEEN '%s' AND '%s' and device_id='%s'" %(a_table,a_first_id,a_last_id, a_device_id)
    print(query)
    #return False
    return write_operation(query)  
