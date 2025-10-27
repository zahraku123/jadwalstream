from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import pandas as pd
import os
import json
from datetime import datetime
import pytz
import pandas as pd
import os
import json
from datetime import datetime
import pytz
from google_auth_oauthlib.flow import InstalledAppFlow
import schedule
import subprocess
import threading
import time

# Constants
EXCEL_FILE = 'live_stream_data.xlsx'
TIMEZONE = 'Asia/Jakarta'
SCOPES = ['https://www.googleapis.com/auth/youtube']
SCHEDULER_STATUS_FILE = 'scheduler_status.json'

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # untuk flash messages
TIMEZONE = 'Asia/Jakarta'
SCOPES = ['https://www.googleapis.com/auth/youtube']
SCHEDULER_STATUS_FILE = 'scheduler_status.json'

def save_scheduler_status(status):
    try:
        with open(SCHEDULER_STATUS_FILE, 'w') as f:
            json.dump({
                'last_run': status.get('last_run', ''),
                'next_check': status.get('next_check', ''),
                'last_status': status.get('last_status', ''),
                'active': status.get('active', False)
            }, f)
    except Exception as e:
        print(f"Error saving scheduler status: {e}")

def get_scheduler_status():
    try:
        with open(SCHEDULER_STATUS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {
            'last_run': '',
            'next_check': '',
            'last_status': 'Never run',
            'active': False
        }

def get_stream_name(stream_id):
    """Convert stream ID to stream name using the mapping from live.py"""
    if not stream_id:
        return ''

    # Try live.py reverse mapping first (fast when available)
    try:
        from live import REVERSE_STREAM_MAPPING
        if stream_id in REVERSE_STREAM_MAPPING:
            return REVERSE_STREAM_MAPPING[stream_id]
        # if not found, don't return yet — fall back to saved mappings
    except Exception:
        pass

    # Fallback: try to read our saved stream_mapping.json and find a title
    try:
        mapping = get_stream_mapping()
        for token, streams in mapping.items():
            # streams expected: {streamId: {title: ..., ...}}
            for sid, meta in (streams or {}).items():
                if sid == stream_id:
                    # meta might be a dict with a title
                    if isinstance(meta, dict):
                        return meta.get('title') or meta.get('name') or stream_id
                    # otherwise meta might be a string name
                    return str(meta)
    except Exception:
        pass

    # Last resort: return the provided value unchanged
    return stream_id

def load_schedule_times():
    try:
        with open('schedule_config.json', 'r') as f:
            config = json.load(f)
            return config.get('schedule_times', ["00:35", "00:37", "00:39"])
    except:
        return ["00:35", "00:37", "00:39"]

def save_schedule_times(times):
    with open('schedule_config.json', 'w') as f:
        json.dump({'schedule_times': times}, f)

def get_stream_mapping():
    try:
        with open('stream_mapping.json', 'r') as f:
            return json.load(f)
    except:
        return {}

@app.route('/edit_schedule/<int:index>', methods=['GET'])
def edit_schedule(index):
    try:
        # Read the Excel file
        df = pd.read_excel(EXCEL_FILE)
        schedule = df.iloc[index].to_dict()
        
        # Handle the datetime conversion
        try:
            # Try to parse the datetime from the Excel value
            dt = pd.to_datetime(schedule['scheduledStartTime'])
            # Format it for the datetime-local input
            schedule['scheduledStartTime'] = dt.strftime('%Y-%m-%dT%H:%M')
        except:
            # If parsing fails, try to use the value as-is if it's properly formatted
            current_value = str(schedule.get('scheduledStartTime', ''))
            if 'T' in current_value:  # Check if it's already in the correct format
                schedule['scheduledStartTime'] = current_value
            else:
                schedule['scheduledStartTime'] = ''  # Set empty if invalid
        
        tokens = [f for f in os.listdir() if f.endswith('.json') and f != 'client_secret.json']
        stream_mapping = get_stream_mapping()
        return render_template('edit_schedule.html', schedule=schedule, index=index, 
                             tokens=tokens, stream_mapping=stream_mapping)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('schedules'))

@app.route('/update_schedule/<int:index>', methods=['POST'])
def update_schedule(index):
    try:
        data = request.form.to_dict()
        df = pd.read_excel(EXCEL_FILE)
        
        # Resolve stream name and log for debugging
        submitted_stream = data.get('streamNameExisting', '')
        resolved_stream = get_stream_name(submitted_stream)
        app.logger.debug(f"update_schedule: submitted stream='{submitted_stream}' resolved='{resolved_stream}'")

        # Update the row
        df.loc[index, 'title'] = data['title']
        df.loc[index, 'description'] = data['description']
        df.loc[index, 'scheduledStartTime'] = data['scheduledStartTime']
        df.loc[index, 'privacyStatus'] = data.get('privacyStatus', 'unlisted')
        df.loc[index, 'autoStart'] = data.get('autoStart') == 'on'
        df.loc[index, 'autoStop'] = data.get('autoStop') == 'on'
        df.loc[index, 'madeForKids'] = data.get('madeForKids') == 'on'
        df.loc[index, 'tokenFile'] = data['tokenFile']
        df.loc[index, 'useExistingStream'] = data.get('useExistingStream') == 'on'
        df.loc[index, 'streamNameExisting'] = resolved_stream
        df.loc[index, 'thumbnailFile'] = data.get('thumbnailFile', '')
        
        # Save the changes
        df.to_excel(EXCEL_FILE, index=False)
        flash('Schedule updated successfully!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('schedules'))

@app.route('/delete_schedule/<int:index>', methods=['POST'])
def delete_schedule(index):
    try:
        df = pd.read_excel(EXCEL_FILE)
        df = df.drop(index)
        df.to_excel(EXCEL_FILE, index=False)
        flash('Schedule deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('schedules'))

@app.route('/stream_keys')
def stream_keys():
    # Get available tokens
    tokens = [f for f in os.listdir() if f.endswith('.json') and f != 'client_secret.json']
    # Get current stream mapping
    stream_mapping = get_stream_mapping()
    return render_template('stream_keys.html', tokens=tokens, stream_mapping=stream_mapping)


@app.route('/manage_streams')
def manage_streams():
    from kunci import load_stream_mapping
    stream_mapping = load_stream_mapping()
    return render_template('manage_streams.html', stream_mapping=stream_mapping)


@app.route('/delete_stream_mapping', methods=['POST'])
def delete_stream_mapping():
    token_file = request.form.get('token_file')
    stream_id = request.form.get('stream_id')
    try:
        mapping = get_stream_mapping()
        if token_file in mapping and stream_id in mapping[token_file]:
            del mapping[token_file][stream_id]
            # if token has no more streams, keep empty dict or remove key
            if not mapping[token_file]:
                mapping.pop(token_file, None)
            with open('stream_mapping.json', 'w') as f:
                json.dump(mapping, f, indent=4)
            flash('Stream mapping deleted.', 'success')
        else:
            flash('Stream mapping not found.', 'warning')
    except Exception as e:
        flash(f'Error: {e}', 'error')
    return redirect(url_for('manage_streams'))


@app.route('/delete_token_mapping', methods=['POST'])
def delete_token_mapping():
    token_file = request.form.get('token_file')
    try:
        mapping = get_stream_mapping()
        if token_file in mapping:
            mapping.pop(token_file, None)
            with open('stream_mapping.json', 'w') as f:
                json.dump(mapping, f, indent=4)
            flash('Token mappings deleted.', 'success')
        else:
            flash('Token not found in mappings.', 'warning')
    except Exception as e:
        flash(f'Error: {e}', 'error')
    return redirect(url_for('manage_streams'))


@app.route('/export_stream_mapping', methods=['POST'])
def export_stream_mapping():
    try:
        mapping = get_stream_mapping()
        data = json.dumps(mapping, indent=4)
        return (data, 200, {
            'Content-Type': 'application/json',
            'Content-Disposition': 'attachment; filename="stream_mapping.json"'
        })
    except Exception as e:
        flash(f'Error exporting mapping: {e}', 'error')
        return redirect(url_for('manage_streams'))

@app.route('/fetch_stream_keys', methods=['POST'])
def fetch_stream_keys():
    from kunci import get_stream_keys, save_stream_mapping
    token_file = request.form.get('token_file')
    if not token_file:
        flash('Please select a token file', 'error')
        return redirect(url_for('stream_keys'))
    
    try:
        # Get stream keys from YouTube
        stream_keys = get_stream_keys(token_file)
        if stream_keys:
            # Save to stream_mapping.json under the token filename (merge existing)
            if save_stream_mapping(stream_keys, token_file):
                flash('Stream keys fetched and saved successfully!', 'success')
            else:
                flash('Error saving stream keys', 'error')
        else:
            flash('No stream keys found', 'warning')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('stream_keys'))

@app.route('/')
def home():
    # Get schedules data
    try:
        df = pd.read_excel(EXCEL_FILE)
        schedules = df.to_dict('records')
    except:
        schedules = []
    
    # Get tokens
    tokens = [f for f in os.listdir() if f.endswith('.json') and f != 'client_secret.json']
    
    return render_template('index.html', schedules=schedules, tokens=tokens)

@app.route('/schedules')
def schedules():
    try:
        df = pd.read_excel(EXCEL_FILE)
        schedules = df.to_dict('records')
    except:
        schedules = []
    stream_mapping = get_stream_mapping()
    # Get list of available tokens
    tokens = [f for f in os.listdir() if f.endswith('.json') and f != 'client_secret.json']
    return render_template('schedules.html', schedules=schedules, stream_mapping=stream_mapping, tokens=tokens)

@app.route('/add_schedule', methods=['POST'])
def add_schedule():
    try:
        data = request.form.to_dict()
        df = pd.read_excel(EXCEL_FILE) if os.path.exists(EXCEL_FILE) else pd.DataFrame()
        
        # Resolve stream name and log for debugging
        submitted_stream = data.get('streamNameExisting', '')
        resolved_stream = get_stream_name(submitted_stream)
        app.logger.debug(f"add_schedule: submitted stream='{submitted_stream}' resolved='{resolved_stream}'")

        new_row = {
            'title': data['title'],
            'description': data['description'],
            'scheduledStartTime': data['scheduledStartTime'],
            'privacyStatus': data.get('privacyStatus', 'unlisted'),
            'autoStart': data.get('autoStart') == 'on',
            'autoStop': data.get('autoStop') == 'on',
            'madeForKids': data.get('madeForKids') == 'on',
            'tokenFile': data['tokenFile'],
            'useExistingStream': data.get('useExistingStream') == 'on',
            'streamNameExisting': resolved_stream,
            'thumbnailFile': data.get('thumbnailFile', ''),
            'success': False,
            'streamId': '',
            'broadcastLink': '',
            'streamIdExisting': ''
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_excel(EXCEL_FILE, index=False)
        flash('Schedule added successfully!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('schedules'))

@app.route('/tokens')
def tokens():
    tokens = [f for f in os.listdir() if f.endswith('.json') and f != 'client_secret.json']
    return render_template('tokens.html', tokens=tokens)

@app.route('/create_token', methods=['POST'])
def create_token():
    try:
        token_name = request.form.get('token_name', 'token.json')
        if not token_name.endswith('.json'):
            token_name += '.json'
        
        flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
        creds = flow.run_local_server(port=0)
        
        with open(token_name, 'w') as f:
            f.write(creds.to_json())
        
        flash(f'Token {token_name} berhasil dibuat!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('tokens'))

@app.route('/delete_token', methods=['POST'])
def delete_token():
    try:
        token_name = request.form.get('token_name')
        if not token_name:
            flash('Token name is required', 'error')
            return redirect(url_for('tokens'))
        
        if not token_name.endswith('.json'):
            token_name += '.json'
        
        # Check if it's a valid token file
        if token_name == 'client_secret.json':
            flash('Cannot delete client_secret.json', 'error')
            return redirect(url_for('tokens'))
        
        # Try to delete the token file
        if os.path.exists(token_name):
            os.remove(token_name)
            
            # Also remove any associated stream mappings
            try:
                mapping = get_stream_mapping()
                if token_name in mapping:
                    del mapping[token_name]
                    with open('stream_mapping.json', 'w') as f:
                        json.dump(mapping, f, indent=4)
            except:
                pass  # Ignore errors with stream mapping cleanup
                
            flash(f'Token {token_name} has been deleted', 'success')
        else:
            flash(f'Token {token_name} not found', 'warning')
            
    except Exception as e:
        flash(f'Error deleting token: {str(e)}', 'error')
    
    return redirect(url_for('tokens'))

def check_and_run_schedules():
    """Check if any schedules should be run now"""
    import live
    current_time = datetime.now(pytz.timezone(TIMEZONE))
    times = load_schedule_times()
    current_time_str = current_time.strftime('%H:%M')
    
    if current_time_str in times:
        try:
            live.main()  # Run the scheduler
            status = {
                'last_run': current_time.strftime('%Y-%m-%d %H:%M:%S'),
                'next_check': (current_time + pd.Timedelta(minutes=1)).strftime('%Y-%m-%d %H:%M:%S'),
                'last_status': 'Success',
                'active': True
            }
        except Exception as e:
            status = {
                'last_run': current_time.strftime('%Y-%m-%d %H:%M:%S'),
                'next_check': (current_time + pd.Timedelta(minutes=1)).strftime('%Y-%m-%d %H:%M:%S'),
                'last_status': f'Error: {str(e)}',
                'active': True
            }
    else:
        status = get_scheduler_status()
        status['next_check'] = (current_time + pd.Timedelta(minutes=1)).strftime('%Y-%m-%d %H:%M:%S')
        status['active'] = True
    
    save_scheduler_status(status)
    return status

def start_scheduler_thread():
    def run_scheduler():
        while True:
            check_and_run_schedules()
            time.sleep(60)  # Wait for 1 minute
    
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

@app.route('/auto_schedule')
def auto_schedule():
    schedule_times = load_schedule_times()
    scheduler_status = get_scheduler_status()
    return render_template('auto_schedule.html', 
                         schedule_times=schedule_times,
                         scheduler_status=scheduler_status)

@app.route('/update_schedule_times', methods=['POST'])
def update_schedule_times():
    times = request.form.getlist('times[]')
    save_schedule_times(times)
    flash('Jadwal auto-scheduling berhasil diupdate!', 'success')
    return redirect(url_for('auto_schedule'))

@app.route('/run_scheduler', methods=['POST'])
def run_scheduler():
    try:
        import live
        live.main()  # Run scheduler directly
        
        # Update status
        current_time = datetime.now(pytz.timezone(TIMEZONE))
        status = {
            'last_run': current_time.strftime('%Y-%m-%d %H:%M:%S'),
            'next_check': (current_time + pd.Timedelta(minutes=1)).strftime('%Y-%m-%d %H:%M:%S'),
            'last_status': 'Success (Manual Run)',
            'active': True
        }
        save_scheduler_status(status)
        
        flash('Scheduler berhasil dijalankan!', 'success')
    except Exception as e:
        status = {
            'last_run': datetime.now(pytz.timezone(TIMEZONE)).strftime('%Y-%m-%d %H:%M:%S'),
            'last_status': f'Error: {str(e)}',
            'active': True
        }
        save_scheduler_status(status)
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('auto_schedule'))

if __name__ == '__main__':
    # Enable Flask's debugger and detailed error pages
    app.debug = True
    
    # Enable more verbose logging
    import logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Initialize scheduler: when using the reloader, only start the thread
    # in the reloader child process to avoid starting it twice.
    # WERKZEUG_RUN_MAIN is set to 'true' in the child process when the
    # auto-reloader is enabled.
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
        start_scheduler_thread()

    # Start Flask with debug mode enabled
    app.run(debug=True, use_reloader=True, host='0.0.0.0')
