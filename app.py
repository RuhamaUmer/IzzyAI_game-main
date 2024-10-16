
from flask import Flask, request, jsonify, send_from_directory, render_template, session, url_for
import  psycopg2
import pyaudio
import wave
from werkzeug.utils import secure_filename  
import os
import speech_recognition as sr
from flask_cors import CORS
import speech_recognition as sr
from pydub import AudioSegment


app = Flask(__name__)
# Generates a random key
app.secret_key = os.urandom(24)  

# Enable CORS for all routes and origins
CORS(app)  

# # Database connection parameters
# DB_HOST = "localhost"
# DB_NAME = "izzyai"
# DB_USER = "postgres"
# DB_PASS = "12345"




# # Database connection
# def get_db_connection():
#     conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
#     return conn

# conn = get_db_connection()

# conn = get_db_connection()
AUDIO_DIR = 'audio'
if not os.path.exists(AUDIO_DIR):
    os.makedirs(AUDIO_DIR)

def record_audio(filename, duration, channels=1, rate=44100, chunk=1024):
    # Initialize PyAudio
    audio = pyaudio.PyAudio()

    # Open a new stream to record audio
    stream = audio.open(format=pyaudio.paInt16,
                        channels=channels,
                        rate=rate,
                        input=True,
                        frames_per_buffer=chunk)

    print(f"Recording for {duration} seconds...")

    frames = []

    # Record audio for the specified duration
    for _ in range(0, int(rate / chunk * duration)):
        data = stream.read(chunk)
        frames.append(data)

    print("Recording finished.")

    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Save the recorded data as a WAV file
    filepath = os.path.join(AUDIO_DIR, filename)
    with wave.open(filepath, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(rate)
        wf.writeframes(b''.join(frames))

    print(f"Audio saved to {filepath}")

@app.route('/record', methods=['POST'])
def record():
    try:
        data = request.json
        duration = data.get('duration', 5)
        filename = data.get('filename', 'output.wav')

        # Record audio and overwrite if exists
        record_audio(filename, duration=duration)

        return jsonify({'status': 'success', 'message': f'Audio saved to {filename}'}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Ensure that the get_audio function as described above is implemented.



@app.route('/audio/<path:filename>', methods=['GET'])
def get_audio(filename):
    response = send_from_directory(AUDIO_DIR, filename)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'  # HTTP 1.1.
    response.headers['Pragma'] = 'no-cache'  # HTTP 1.0.
    response.headers['Expires'] = '0'  # Proxies.
    return response

UPLOAD_FOLDER =r'static\audio'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/save_audio', methods=['POST'])
def save_audio():
    if 'audio_data' not in request.files:
        return jsonify(message="No audio file provided."), 400
    
    audio_file = request.files['audio_data']
    filename = secure_filename(audio_file.filename)
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    try:
        # Save the audio file
        audio_file.save(save_path)
        print(f"Audio saved successfully at {save_path}")
        
      
        return jsonify(message="Audio saved"), 200

    except Exception as e:
        print(f"An error occurred while saving or transcribing the audio: {e}")
        return jsonify(message=f"Failed to save or transcribe audio: {str(e)}"), 500


def transcribe_audio(audio_file_path):
    recognizer = sr.Recognizer()
    try:
        # Load and transcribe the audio file
        with sr.AudioFile(audio_file_path) as source:
            audio_data = recognizer.record(source)
        
        # Try to recognize the text from the audio
        text = recognizer.recognize_google(audio_data)
        return text
    
    except sr.UnknownValueError:
        # Handle case where the audio is not clear or transcribable
        print("Google Speech Recognition could not understand the audio.")
        return None
    
    except sr.RequestError as e:
        # Handle errors in the API request to Google Speech Recognition
        print(f"Could not request results from Google Speech Recognition service; {e}")
        return None            

# def convert_to_pcm_wav(input_file, output_file):
#     try:
#         (
#             ffmpeg
#             .input(input_file)
#             .output(output_file, format='wav', acodec='pcm_s16le', ac=1, ar='16000')
#             .run(quiet=True, overwrite_output=True)
#         )
#         print(f"Converted {input_file} to {output_file}")
#         return True
#     except Exception as e:
#         print(f"Error converting file: {e}")
#         return False

# @app.route('/match_audio_text', methods=['POST'])
# def match_audio_text():
#     print(request.form)
#     print(request.files)
#     # Get the text and audio file path from the request
#     input_text = request.form.get('text')
#     audio_file_path = request.files.get('audio_path')

#     if not audio_file_path:
#         return jsonify({"error": "No audio file path provided"}), 400

#     if not os.path.exists(audio_file_path):
#         return jsonify({"error": "Audio file path does not exist"}), 400

#     # Transcribe the audio file
#     transcribed_text = transcribe_audio(audio_file_path)

#     if transcribed_text is None:
#         return jsonify({"error": "Could not transcribe audio"}), 500

#     # Compare the transcribed text with the input text
#     if input_text.lower() in transcribed_text.lower():
#         return jsonify({"match": True, "transcribed_text": transcribed_text}), 200
#     else:
#         return jsonify({"match": False, "transcribed_text": transcribed_text}), 200



def convert_to_wav(audio_path):
    try:
        audio = AudioSegment.from_file(audio_path)
        wav_path = os.path.splitext(audio_path)[0] + '.wav'
        audio.export(wav_path, format='wav')
        print(f"Converted to WAV: {wav_path}")
        return wav_path
    except Exception as e:
        print(f"Error converting {audio_path} to WAV: {e}")
        return None
    

@app.route('/match_audio_text', methods=['POST'])
def match_audio_text():
    # Get the text and audio file path from the request
    input_text = request.form.get('text')
    audio_file_path = request.form.get('audio_path')

    if not audio_file_path:
        return jsonify({"error": "No audio file path provided"}), 400

    if not os.path.exists(audio_file_path):
        return jsonify({"error": "Audio file path does not exist"}), 400

    converted_path = convert_to_wav(audio_file_path)

    # Transcribe the audio file
    transcribed_text = transcribe_audio(converted_path)
    print('transcribed_text', transcribed_text)

    if transcribed_text is None:
        return jsonify({"error": "Could not transcribe audio"}), 500

    # Compare the transcribed text with the input text
    if input_text.lower() in transcribed_text.lower():
        return jsonify({"match": True, "transcribed_text": transcribed_text}), 200
    else:
        return jsonify({"match": False, "transcribed_text": transcribed_text}), 200



@app.route('/get_session_data')
def get_session_data():
    user_id = session.get('UserID')
    disorder_id = session.get('DisorderID')
    if user_id and disorder_id:
        return jsonify({'UserID': user_id, 'DisorderID': disorder_id})
    return jsonify({'error': 'No session data available'}), 404


@app.route('/start_blow_game/<int:user_id>/<int:disorder_id>', methods=['GET'])
def start_blow_game(user_id, disorder_id):
    # Store the user_id and disorder_id_list in the session
    session['UserID'] = user_id
    session['DisorderID'] = disorder_id
    print("userid", user_id)
    # Render a game template
    return render_template('loudness_blow_game.html', user_id=user_id, disorder_id=disorder_id,
                           balloon_easy=url_for('static', filename='images/balloon.jpg'),
                           balloon_medium=url_for('static', filename='images/ball.jpg'),
                           balloon_hard=url_for('static', filename='images/box.jpeg'))



################################
# Game 2 - Sounds Game
################################

@app.route('/start_sounds_game/<int:user_id>/<int:disorder_id>', methods=['GET'])
def start_sounds_game(user_id, disorder_id):
    # Store the user_id and disorder_id_list in the session
    session['UserID'] = user_id
    session['DisorderID'] = disorder_id
    print("userid", user_id)
    print('disorder_id', disorder_id)
    # Render a game template
    return render_template('game2_levels.html', user_id=user_id, disorder_id=disorder_id)

@app.route('/game2_easy_level', methods=['GET'])
def game2_easy_level():
    # Render a game template
    return render_template('game2_easy_level.html')

@app.route('/game2_medium_level', methods=['GET'])
def game2_medium_level():
    # Render a game template
    return render_template('game2_medium_level.html')

@app.route('/game2_difficult_level', methods=['GET'])
def game2_difficult_level():
    # Render a game template
    return render_template('game2_difficult_level.html')

@app.route('/exit_game2_levels', methods=['GET'])
def exit_game2_levels():
    # Render a game template
    return render_template('game2_levels.html')


# routes for Animal Game LEVEL 1
@app.route('/game2_in', methods=['GET'])
def game2_in():
    # Render a game template
    return render_template('game2_in.html')

@app.route('/game2_out', methods=['GET'])
def game2_out():
    # Render a game template
    return render_template('game2_out.html')

@app.route('/game2_up', methods=['GET'])
def game2_up():
    # Render a game template
    return render_template('game2_up.html')

@app.route('/game2_on', methods=['GET'])
def game2_on():
    # Render a game template
    return render_template('game2_on.html')

@app.route('/game2_ball', methods=['GET'])
def game2_ball():
    # Render a game template
    return render_template('game2_ball.html')

@app.route('/game2_bulb', methods=['GET'])
def game2_bulb():
    # Render a game template
    return render_template('game2_bulb.html')

@app.route('/game2_boat', methods=['GET'])
def game2_boat():
    # Render a game template
    return render_template('game2_boat.html')

@app.route('/game2_pen', methods=['GET'])
def game2_pen():
    # Render a game template
    return render_template('game2_pen.html')

@app.route('/game2_pin', methods=['GET'])
def game2_pin():
    # Render a game template
    return render_template('game2_pin.html')

@app.route('/game2_pot', methods=['GET'])
def game2_pot():
    # Render a game template
    return render_template('game2_pot.html')

@app.route('/game2_moon', methods=['GET'])
def game2_moon():
    # Render a game template
    return render_template('game2_moon.html')

@app.route('/game2_mat', methods=['GET'])
def game2_mat():
    # Render a game template
    return render_template('game2_mat.html')

@app.route('/game2_mango', methods=['GET'])
def game2_mango():
    # Render a game template
    return render_template('game2_mango.html')


@app.route('/game2_net', methods=['GET'])
def game2_net():
    # Render a game template
    return render_template('game2_net.html')

@app.route('/game2_nail', methods=['GET'])
def game2_nail():
    # Render a game template
    return render_template('game2_nail.html')

@app.route('/game2_nine', methods=['GET'])
def game2_nine():
    # Render a game template
    return render_template('game2_nine.html')


# routes for Sounds Game LEVEL 2

@app.route('/game2_ball_out', methods=['GET'])
def game2_ball_out():
    # Render a game template
    return render_template('game2_ball_out.html')

@app.route('/game2_boat_in', methods=['GET'])
def game2_boat_in():
    # Render a game template
    return render_template('game2_boat_in.html')

@app.route('/game2_bulb_on', methods=['GET'])
def game2_bulb_on():
    # Render a game template
    return render_template('game2_bulb_on.html')

@app.route('/game2_pen_in', methods=['GET'])
def game2_pen_in():
    # Render a game template
    return render_template('game2_pen_in.html')

@app.route('/game2_pin_out', methods=['GET'])
def game2_pin_out():
    # Render a game template
    return render_template('game2_pin_out.html')

@app.route('/game2_pot_on', methods=['GET'])
def game2_pot_on():
    # Render a game template
    return render_template('game2_pot_on.html')

@app.route('/game2_moon_up', methods=['GET'])
def game2_moon_up():
    # Render a game template
    return render_template('game2_moon_up.html')

@app.route('/game2_mat_open', methods=['GET'])
def game2_mat_open():
    # Render a game template
    return render_template('game2_mat_open.html')

@app.route('/game2_mango_out', methods=['GET'])
def game2_mango_out():
    # Render a game template
    return render_template('game2_mango_out.html')

@app.route('/game2_net_up', methods=['GET'])
def game2_net_up():
    # Render a game template
    return render_template('game2_net_up.html')

@app.route('/game2_nail_out', methods=['GET'])
def game2_nail_out():
    # Render a game template
    return render_template('game2_nail_out.html')

@app.route('/game2_nine_up', methods=['GET'])
def game2_nine_up():
    # Render a game template
    return render_template('game2_nine_up.html')

# routes for Sounds Game LEVEL 3

@app.route('/game2_sentence1', methods=['GET'])
def game2_sentence1():
    # Render a game template
    return render_template('game2_sentence1.html')

@app.route('/game2_sentence2', methods=['GET'])
def game2_sentence2():
    # Render a game template
    return render_template('game2_sentence2.html')

@app.route('/game2_sentence3', methods=['GET'])
def game2_sentence3():
    # Render a game template
    return render_template('game2_sentence3.html')

@app.route('/game2_sentence4', methods=['GET'])
def game2_sentence4():
    # Render a game template
    return render_template('game2_sentence4.html')

@app.route('/game2_sentence5', methods=['GET'])
def game2_sentence5():
    # Render a game template
    return render_template('game2_sentence5.html')

@app.route('/game2_sentence6', methods=['GET'])
def game2_sentence6():
    # Render a game template
    return render_template('game2_sentence6.html')

@app.route('/game2_sentence7', methods=['GET'])
def game2_sentence7():
    # Render a game template
    return render_template('game2_sentence7.html')

@app.route('/game2_sentence8', methods=['GET'])
def game2_sentence8():
    # Render a game template
    return render_template('game2_sentence8.html')

@app.route('/game2_sentence9', methods=['GET'])
def game2_sentence9():
    # Render a game template
    return render_template('game2_sentence9.html')

@app.route('/game2_sentence10', methods=['GET'])
def game2_sentence10():
    # Render a game template
    return render_template('game2_sentence10.html')

@app.route('/game2_sentence11', methods=['GET'])
def game2_sentence11():
    # Render a game template
    return render_template('game2_sentence11.html')

@app.route('/game2_sentence12', methods=['GET'])
def game2_sentence12():
    # Render a game template
    return render_template('game2_sentence12.html')


########################## Game 2 Testing Levels #################
@app.route('/testing_game2_levels', methods=['GET'])
def testing_game2_levels():
    # Render a game template
    return render_template('./testing/testing_game2_levels.html')

@app.route('/game2_testing_easy_level', methods=['GET'])
def game2_testing_easy_level():
    # Render a game template
    return render_template('./testing/game2_testing_easy_level.html')

@app.route('/game2_testing_medium_level', methods=['GET'])
def game2_testing_medium_level():
    # Render a game template
    return render_template('./testing/game2_testing_medium_level.html')

@app.route('/game2_testing_difficult_level', methods=['GET'])
def game2_testing_difficult_level():
    # Render a game template
    return render_template('./testing/game2_testing_difficult_level.html')


@app.route('/exit_game2_testing', methods=['GET'])
def exit_game2_testing():
    # Render a game template
    return render_template('/testing/testing_game2_levels.html')

########################## Game 2 Testing Easy Level

@app.route('/game2_testing_in', methods=['GET'])
def game2_testing_in():
    # Render a game template
    return render_template('/testing/game2_testing_in.html')

@app.route('/game2_testing_out', methods=['GET'])
def game2_testing_out():
    # Render a game template
    return render_template('/testing/game2_testing_out.html')

@app.route('/game2_testing_up', methods=['GET'])
def game2_testing_up():
    # Render a game template
    return render_template('/testing/game2_testing_up.html')

@app.route('/game2_testing_on', methods=['GET'])
def game2_testing_on():
    # Render a game template
    return render_template('/testing/game2_testing_on.html')

@app.route('/game2_testing_ball', methods=['GET'])
def game2_testing_ball():
    # Render a game template
    return render_template('/testing/game2_testing_ball.html')

@app.route('/game2_testing_bulb', methods=['GET'])
def game2_testing_bulb():
    # Render a game template
    return render_template('/testing/game2_testing_bulb.html')

@app.route('/game2_testing_boat', methods=['GET'])
def game2_testing_boat():
    # Render a game template
    return render_template('/testing/game2_testing_boat.html')

@app.route('/game2_testing_pen', methods=['GET'])
def game2_testing_pen():
    # Render a game template
    return render_template('/testing/game2_testing_pen.html')

@app.route('/game2_testing_pin', methods=['GET'])
def game2_testing_pin():
    # Render a game template
    return render_template('/testing/game2_testing_pin.html')

@app.route('/game2_testing_pot', methods=['GET'])
def game2_testing_pot():
    # Render a game template
    return render_template('/testing/game2_testing_pot.html')

@app.route('/game2_testing_moon', methods=['GET'])
def game2_testing_moon():
    # Render a game template
    return render_template('/testing/game2_testing_moon.html')

@app.route('/game2_testing_mat', methods=['GET'])
def game2_testing_mat():
    # Render a game template
    return render_template('/testing/game2_testing_mat.html')

@app.route('/game2_testing_mango', methods=['GET'])
def game2_testing_mango():
    # Render a game template
    return render_template('/testing/game2_testing_mango.html')


@app.route('/game2_testing_net', methods=['GET'])
def game2_testing_net():
    # Render a game template
    return render_template('/testing/game2_testing_net.html')

@app.route('/game2_testing_nail', methods=['GET'])
def game2_testing_nail():
    # Render a game template
    return render_template('/testing/game2_testing_nail.html')

@app.route('/game2_testing_nine', methods=['GET'])
def game2_testing_nine():
    # Render a game template
    return render_template('/testing/game2_testing_nine.html')


########################## Game 2 Testing Medium Level
@app.route('/game2_testing_ball_out', methods=['GET'])
def game2_testing_ball_out():
    # Render a game template
    return render_template('/testing/game2_testing_ball_out.html')

@app.route('/game2_testing_boat_in', methods=['GET'])
def game2_testing_boat_in():
    # Render a game template
    return render_template('/testing/game2_testing_boat_in.html')

@app.route('/game2_testing_bulb_on', methods=['GET'])
def game2_testing_bulb_on():
    # Render a game template
    return render_template('/testing/game2_testing_bulb_on.html')

@app.route('/game2_testing_pen_in', methods=['GET'])
def game2_testing_pen_in():
    # Render a game template
    return render_template('/testing/game2_testing_pen_in.html')

@app.route('/game2_testing_pin_out', methods=['GET'])
def game2_testing_pin_out():
    # Render a game template
    return render_template('/testing/game2_testing_pin_out.html')

@app.route('/game2_testing_pot_on', methods=['GET'])
def game2_testing_pot_on():
    # Render a game template
    return render_template('/testing/game2_testing_pot_on.html')

@app.route('/game2_testing_moon_up', methods=['GET'])
def game2_testing_moon_up():
    # Render a game template
    return render_template('/testing/game2_testing_moon_up.html')

@app.route('/game2_testing_mat_open', methods=['GET'])
def game2_testing_mat_open():
    # Render a game template
    return render_template('/testing/game2_testing_mat_open.html')

@app.route('/game2_testing_mango_out', methods=['GET'])
def game2_testing_mango_out():
    # Render a game template
    return render_template('/testing/game2_testing_mango_out.html')

@app.route('/game2_testing_net_up', methods=['GET'])
def game2_testing_net_up():
    # Render a game template
    return render_template('/testing/game2_testing_net_up.html')

@app.route('/game2_testing_nail_out', methods=['GET'])
def game2_testing_nail_out():
    # Render a game template
    return render_template('/testing/game2_testing_nail_out.html')

@app.route('/game2_testing_nine_up', methods=['GET'])
def game2_testing_nine_up():
    # Render a game template
    return render_template('/testing/game2_testing_nine_up.html')

########################## Game 2 Testing Difficult Level
@app.route('/game2_testing_sentence1', methods=['GET'])
def game2_testing_sentence1():
    # Render a game template
    return render_template('/testing/game2_testing_sentence1.html')

@app.route('/game2_testing_sentence2', methods=['GET'])
def game2_testing_sentence2():
    # Render a game template
    return render_template('/testing/game2_testing_sentence2.html')

@app.route('/game2_testing_sentence3', methods=['GET'])
def game2_testing_sentence3():
    # Render a game template
    return render_template('/testing/game2_testing_sentence3.html')

@app.route('/game2_testing_sentence4', methods=['GET'])
def game2_testing_sentence4():
    # Render a game template
    return render_template('/testing/game2_testing_sentence4.html')

@app.route('/game2_testing_sentence5', methods=['GET'])
def game2_testing_sentence5():
    # Render a game template
    return render_template('/testing/game2_testing_sentence5.html')

@app.route('/game2_testing_sentence6', methods=['GET'])
def game2_testing_sentence6():
    # Render a game template
    return render_template('/testing/game2_testing_sentence6.html')

@app.route('/game2_testing_sentence7', methods=['GET'])
def game2_testing_sentence7():
    # Render a game template
    return render_template('/testing/game2_testing_sentence7.html')

@app.route('/game2_testing_sentence8', methods=['GET'])
def game2_testing_sentence8():
    # Render a game template
    return render_template('/testing/game2_testing_sentence8.html')

@app.route('/game2_testing_sentence9', methods=['GET'])
def game2_testing_sentence9():
    # Render a game template
    return render_template('/testing/game2_testing_sentence9.html')

@app.route('/game2_testing_sentence10', methods=['GET'])
def game2_testing_sentence10():
    # Render a game template
    return render_template('/testing/game2_testing_sentence10.html')

@app.route('/game2_testing_sentence11', methods=['GET'])
def game2_testing_sentence11():
    # Render a game template
    return render_template('/testing/game2_testing_sentence11.html')

@app.route('/game2_testing_sentence12', methods=['GET'])
def game2_testing_sentence12():
    # Render a game template
    return render_template('/testing/game2_testing_sentence12.html')

################################
# Game 3 - Animal Game
################################

@app.route('/start_animal_game/<int:user_id>/<int:disorder_id>', methods=['GET'])
def start_animal_game(user_id, disorder_id):
    # Store the user_id and disorder_id_list in the session
    session['UserID'] = user_id
    session['DisorderID'] = disorder_id
    print("userid", user_id)
    print('disorder_id', disorder_id)
    # Render a game template
    return render_template('levels.html', user_id=user_id, disorder_id=disorder_id)

@app.route('/animal_level_1', methods=['GET'])
def animal_level_1():
    # Render a game template
    return render_template('level1.html')

@app.route('/animal_level_2', methods=['GET'])
def animal_level_2():
    # Render a game template
    return render_template('level2.html')

@app.route('/animal_level_3', methods=['GET'])
def animal_level_3():
    # Render a game template
    return render_template('level3.html')

@app.route('/testing_animal_levels', methods=['GET'])
def testing_animal_levels():
    # Render a game template
    return render_template('./testing/testing_game3_levels.html')

@app.route('/exit_animal_levels', methods=['GET'])
def exit_animal_levels():
    # Render a game template
    return render_template('levels.html')

@app.route('/finish_animal_level1', methods=['GET'])
def finish_animal_level1():
    # Render a game template
    return render_template('level1.html')

@app.route('/finish_animal_level2', methods=['GET'])
def finish_animal_level2():
    # Render a game template
    return render_template('level2.html')

@app.route('/finish_animal_level3', methods=['GET'])
def finish_animal_level3():
    # Render a game template
    return render_template('level3.html')

@app.route('/finish_animal_testing_level1', methods=['GET'])
def finish_animal_testing_level1():
    # Render a game template
    return render_template('./testing/testing_game3_level1.html')

@app.route('/finish_animal_testing_level2', methods=['GET'])
def finish_animal_testing_level2():
    # Render a game template
    return render_template('./testing/testing_game3_level2.html')

@app.route('/finish_animal_testing_level3', methods=['GET'])
def finish_animal_testing_level3():
    # Render a game template
    return render_template('./testing/testing_game3_level3.html')


# routes for Animal Game LEVEL 1
@app.route('/cat', methods=['GET'])
def cat():
    # Render a game template
    return render_template('cat.html')

@app.route('/dog', methods=['GET'])
def dog():
    # Render a game template
    return render_template('dog.html')

@app.route('/chicken', methods=['GET'])
def chicken():
    # Render a game template
    return render_template('chicken.html')

@app.route('/cow', methods=['GET'])
def cow():
    # Render a game template
    return render_template('cow.html')

@app.route('/horse', methods=['GET'])
def horse():
    # Render a game template
    return render_template('horse.html')

@app.route('/sheep', methods=['GET'])
def sheep():
    # Render a game template
    return render_template('sheep.html')

@app.route('/lion', methods=['GET'])
def lion():
    # Render a game template
    return render_template('lion.html')

@app.route('/monkey', methods=['GET'])
def monkey():
    # Render a game template
    return render_template('monkey.html')

@app.route('/elephant', methods=['GET'])
def elephant():
    # Render a game template
    return render_template('elephant.html')


# routes for Animal Game LEVEL 2

@app.route('/cat_level2', methods=['GET'])
def cat_level2():
    # Render a game template
    return render_template('cat_level2.html')

@app.route('/dog_level2', methods=['GET'])
def dog_level2():
    # Render a game template
    return render_template('dog_level2.html')

@app.route('/chicken_level2', methods=['GET'])
def chicken_level2():
    # Render a game template
    return render_template('chicken_level2.html')

@app.route('/cow_level2', methods=['GET'])
def cow_level2():
    # Render a game template
    return render_template('cow_level2.html')

@app.route('/horse_level2', methods=['GET'])
def horse_level2():
    # Render a game template
    return render_template('horse_level2.html')

@app.route('/sheep_level2', methods=['GET'])
def sheep_level2():
    # Render a game template
    return render_template('sheep_level2.html')

@app.route('/lion_level2', methods=['GET'])
def lion_level2():
    # Render a game template
    return render_template('lion_level2.html')

@app.route('/monkey_level2', methods=['GET'])
def monkey_level2():
    # Render a game template
    return render_template('monkey_level2.html')

@app.route('/elephant_level2', methods=['GET'])
def elephant_level2():
    # Render a game template
    return render_template('elephant_level2.html')

# routes for Animal Game LEVEL 3

@app.route('/cat_level3', methods=['GET'])
def cat_level3():
    # Render a game template
    return render_template('cat_level3.html')

@app.route('/dog_level3', methods=['GET'])
def dog_level3():
    # Render a game template
    return render_template('dog_level3.html')

@app.route('/chicken_level3', methods=['GET'])
def chicken_level3():
    # Render a game template
    return render_template('chicken_level3.html')

@app.route('/cow_level3', methods=['GET'])
def cow_level3():
    # Render a game template
    return render_template('cow_level3.html')

@app.route('/horse_level3', methods=['GET'])
def horse_level3():
    # Render a game template
    return render_template('horse_level3.html')

@app.route('/sheep_level3', methods=['GET'])
def sheep_level3():
    # Render a game template
    return render_template('sheep_level3.html')

@app.route('/lion_level3', methods=['GET'])
def lion_level3():
    # Render a game template
    return render_template('lion_level3.html')

@app.route('/monkey_level3', methods=['GET'])
def monkey_level3():
    # Render a game template
    return render_template('monkey_level3.html')

@app.route('/elephant_level3', methods=['GET'])
def elephant_level3():
    # Render a game template
    return render_template('elephant_level3.html')


# Routes for Animal Game Testing Level 1
@app.route('/testing_game3_level1', methods=['GET'])
def testing_game3_level1():
    # Render a game template
    return render_template('./testing/testing_game3_level1.html')

@app.route('/cat_testing_level1', methods=['GET'])
def cat_testing_level1():
    # Render a game template
    return render_template('./testing/cat_testing_level1.html')

@app.route('/dog_testing_level1', methods=['GET'])
def dog_testing_level1():
    # Render a game template
    return render_template('./testing/dog_testing_level1.html')

@app.route('/chicken_testing_level1', methods=['GET'])
def chicken_testing_level1():
    # Render a game template
    return render_template('./testing/chicken_testing_level1.html')

@app.route('/cow_testing_level1', methods=['GET'])
def cow_testing_level1():
    # Render a game template
    return render_template('./testing/cow_testing_level1.html')

@app.route('/horse_testing_level1', methods=['GET'])
def horse_testing_level1():
    # Render a game template
    return render_template('./testing/horse_testing_level1.html')

@app.route('/sheep_testing_level1', methods=['GET'])
def sheep_testing_level1():
    # Render a game template
    return render_template('./testing/sheep_testing_level1.html')

@app.route('/lion_testing_level1', methods=['GET'])
def lion_testing_level1():
    # Render a game template
    return render_template('./testing/lion_testing_level1.html')

@app.route('/monkey_testing_level1', methods=['GET'])
def monkey_testing_level1():
    # Render a game template
    return render_template('./testing/monkey_testing_level1.html')

@app.route('/elephant_testing_level1', methods=['GET'])
def elephant_testing_level1():
    # Render a game template
    return render_template('./testing/elephant_testing_level1.html')

# Routes for Animal Game Testing Level 2

@app.route('/testing_game3_level2', methods=['GET'])
def testing_game3_level2():
    # Render a game template
    return render_template('./testing/testing_game3_level2.html')

@app.route('/cat_testing_level2', methods=['GET'])
def cat_testing_level2():
    # Render a game template
    return render_template('./testing/cat_testing_level2.html')

@app.route('/dog_testing_level2', methods=['GET'])
def dog_testing_level2():
    # Render a game template
    return render_template('./testing/dog_testing_level2.html')

@app.route('/chicken_testing_level2', methods=['GET'])
def chicken_testing_level2():
    # Render a game template
    return render_template('./testing/chicken_testing_level2.html')

@app.route('/cow_testing_level2', methods=['GET'])
def cow_testing_level2():
    # Render a game template
    return render_template('./testing/cow_testing_level2.html')

@app.route('/horse_testing_level2', methods=['GET'])
def horse_testing_level2():
    # Render a game template
    return render_template('./testing/horse_testing_level2.html')

@app.route('/sheep_testing_level2', methods=['GET'])
def sheep_testing_level2():
    # Render a game template
    return render_template('./testing/sheep_testing_level2.html')

@app.route('/lion_testing_level2', methods=['GET'])
def lion_testing_level2():
    # Render a game template
    return render_template('./testing/lion_testing_level2.html')

@app.route('/monkey_testing_level2', methods=['GET'])
def monkey_testing_level2():
    # Render a game template
    return render_template('./testing/monkey_testing_level2.html')

@app.route('/elephant_testing_level2', methods=['GET'])
def elephant_testing_level2():
    # Render a game template
    return render_template('./testing/elephant_testing_level2.html')


# Routes for Animal Game Testing Level 3

@app.route('/testing_game3_level3', methods=['GET'])
def testing_game3_level3():
    # Render a game template
    return render_template('./testing/testing_game3_level3.html')


@app.route('/cat_testing_level3', methods=['GET'])
def cat_testing_level3():
    # Render a game template
    return render_template('./testing/cat_testing_level3.html')

@app.route('/dog_testing_level3', methods=['GET'])
def dog_testing_level3():
    # Render a game template
    return render_template('./testing/dog_testing_level3.html')

@app.route('/chicken_testing_level3', methods=['GET'])
def chicken_testing_level3():
    # Render a game template
    return render_template('./testing/chicken_testing_level3.html')

@app.route('/cow_testing_level3', methods=['GET'])
def cow_testing_level3():
    # Render a game template
    return render_template('./testing/cow_testing_level3.html')

@app.route('/horse_testing_level3', methods=['GET'])
def horse_testing_level3():
    # Render a game template
    return render_template('./testing/horse_testing_level3.html')

@app.route('/sheep_testing_level3', methods=['GET'])
def sheep_testing_level3():
    # Render a game template
    return render_template('./testing/sheep_testing_level3.html')

@app.route('/lion_testing_level3', methods=['GET'])
def lion_testing_level3():
    # Render a game template
    return render_template('./testing/lion_testing_level3.html')

@app.route('/monkey_testing_level3', methods=['GET'])
def monkey_testing_level3():
    # Render a game template
    return render_template('./testing/monkey_testing_level3.html')

@app.route('/elephant_testing_level3', methods=['GET'])
def elephant_testing_level3():
    # Render a game template
    return render_template('./testing/elephant_testing_level3.html')

################################
# Game 4 - Transport Game
################################


@app.route('/start_transport_game/<int:user_id>/<int:disorder_id>', methods=['GET'])
def start_transport_game(user_id,disorder_id):
    # Store the user_id and disorder_id_list in the session
    session['UserID'] = user_id
    session['DisorderID'] = disorder_id
    print("userid", user_id)
    print('disorder_id', disorder_id)
    # Render a game template
    return render_template('transp_game_levels.html', user_id=user_id, disorder_id=disorder_id)

@app.route('/transp_level1', methods=['GET'])
def transp_level1():
    # Render a game template
    return render_template('transp_level1.html')

@app.route('/transp_level2', methods=['GET'])
def transp_level2():
    # Render a game template
    return render_template('transp_level2.html')

@app.route('/transp_level3', methods=['GET'])
def transp_level3():
    # Render a game template
    return render_template('transp_level3.html')

@app.route('/testing_game4_levels', methods=['GET'])
def testing_game4_levels():
    # Render a game template
    return render_template('./testing/testing_game4_levels.html')

@app.route('/exit_transport', methods=['GET'])
def exit_transport():
    # Render a game template
    return render_template('transp_game_levels.html')

@app.route('/finish_transport_level1', methods=['GET'])
def finish_transport_level1():
    # Render a game template
    return render_template('transp_level1.html')

@app.route('/finish_transport_level2', methods=['GET'])
def finish_transport_level2():
    # Render a game template
    return render_template('transp_level2.html')

@app.route('/finish_transport_level3', methods=['GET'])
def finish_transport_level3():
    # Render a game template
    return render_template('transp_level3.html')

@app.route('/finish_transport_testing_level1', methods=['GET'])
def finish_transport_testing_level1():
    # Render a game template
    return render_template('./testing/testing_game4_level1.html')

@app.route('/finish_transport_testing_level2', methods=['GET'])
def finish_transport_testing_level2():
    # Render a game template
    return render_template('./testing/testing_game4_level2.html')

@app.route('/finish_transport_testing_level3', methods=['GET'])
def finish_transport_testing_level3():
    # Render a game template
    return render_template('./testing/testing_game4_level3.html')


# routes for transport Game LEVEL 1
@app.route('/car', methods=['GET'])
def car():
    # Render a game template
    return render_template('car.html')

@app.route('/bus', methods=['GET'])
def bus():
    # Render a game template
    return render_template('bus.html')

@app.route('/bicycle', methods=['GET'])
def bicycle():
    # Render a game template
    return render_template('bicycle.html')

@app.route('/helicopter', methods=['GET'])
def helicopter():
    # Render a game template
    return render_template('helicopter.html')

@app.route('/aeroplane', methods=['GET'])
def aeroplane():
    # Render a game template
    return render_template('aeroplane.html')

@app.route('/jet', methods=['GET'])
def jet():
    # Render a game template
    return render_template('jet.html')

@app.route('/boat', methods=['GET'])
def boat():
    # Render a game template
    return render_template('boat.html')

@app.route('/ship', methods=['GET'])
def ship():
    # Render a game template
    return render_template('ship.html')

@app.route('/cruise', methods=['GET'])
def cruise():
    # Render a game template
    return render_template('cruise.html')


# routes for Transport Game LEVEL 2

@app.route('/car_level2', methods=['GET'])
def car_level2():
    # Render a game template
    return render_template('car_level2.html')

@app.route('/bus_level2', methods=['GET'])
def bus_level2():
    # Render a game template
    return render_template('bus_level2.html')

@app.route('/bicycle_level2', methods=['GET'])
def bicycle_level2():
    # Render a game template
    return render_template('bicycle_level2.html')

@app.route('/helicopter_level2', methods=['GET'])
def helicopter_level2():
    # Render a game template
    return render_template('helicopter_level2.html')

@app.route('/aeroplane_level2', methods=['GET'])
def aeroplane_level2():
    # Render a game template
    return render_template('aeroplane_level2.html')

@app.route('/jet_level2', methods=['GET'])
def jet_level2():
    # Render a game template
    return render_template('jet_level2.html')

@app.route('/boat_level2', methods=['GET'])
def boat_level2():
    # Render a game template
    return render_template('boat_level2.html')

@app.route('/ship_level2', methods=['GET'])
def ship_level2():
    # Render a game template
    return render_template('ship_level2.html')

@app.route('/cruise_level2', methods=['GET'])
def cruise_level2():
    # Render a game template
    return render_template('cruise_level2.html')

# routes for Animal Game LEVEL 3
@app.route('/car_level3', methods=['GET'])
def car_level3():
    # Render a game template
    return render_template('car_level3.html')

@app.route('/bus_level3', methods=['GET'])
def bus_level3():
    # Render a game template
    return render_template('bus_level3.html')

@app.route('/bicycle_level3', methods=['GET'])
def bicycle_level3():
    # Render a game template
    return render_template('bicycle_level3.html')

@app.route('/helicopter_level3', methods=['GET'])
def helicopter_level3():
    # Render a game template
    return render_template('helicopter_level3.html')

@app.route('/aeroplane_level3', methods=['GET'])
def aeroplane_level3():
    # Render a game template
    return render_template('aeroplane_level3.html')

@app.route('/jet_level3', methods=['GET'])
def jet_level3():
    # Render a game template
    return render_template('jet_level3.html')

@app.route('/boat_level3', methods=['GET'])
def boat_level3():
    # Render a game template
    return render_template('boat_level3.html')

@app.route('/ship_level3', methods=['GET'])
def ship_level3():
    # Render a game template
    return render_template('ship_level3.html')

@app.route('/cruise_level3', methods=['GET'])
def cruise_level3():
    # Render a game template
    return render_template('cruise_level3.html')



# Routes for Trasnport Game Testing Level 1
@app.route('/testing_game4_level1', methods=['GET'])
def testing_game4_level1():
    # Render a game template
    return render_template('./testing/testing_game4_level1.html')

@app.route('/car_testing_level1', methods=['GET'])
def car_testing_level1():
    # Render a game template
    return render_template('./testing/car_testing_level1.html')

@app.route('/bus_testing_level1', methods=['GET'])
def bus_testing_level1():
    # Render a game template
    return render_template('./testing/bus_testing_level1.html')

@app.route('/bicycle_testing_level1', methods=['GET'])
def bicycle_testing_level1():
    # Render a game template
    return render_template('./testing/bicycle_testing_level1.html')

@app.route('/helicopter_testing_level1', methods=['GET'])
def helicopter_testing_level1():
    # Render a game template
    return render_template('./testing/helicopter_testing_level1.html')

@app.route('/aeroplane_testing_level1', methods=['GET'])
def aeroplane_testing_level1():
    # Render a game template
    return render_template('./testing/aeroplane_testing_level1.html')

@app.route('/jet_testing_level1', methods=['GET'])
def jet_testing_level1():
    # Render a game template
    return render_template('./testing/jet_testing_level1.html')

@app.route('/boat_testing_level1', methods=['GET'])
def boat_testing_level1():
    # Render a game template
    return render_template('./testing/boat_testing_level1.html')

@app.route('/ship_testing_level1', methods=['GET'])
def ship_testing_level1():
    # Render a game template
    return render_template('./testing/ship_testing_level1.html')

@app.route('/cruise_testing_level1', methods=['GET'])
def cruise_testing_level1():
    # Render a game template
    return render_template('./testing/cruise_testing_level1.html')

# Routes for Transport Game Testing Level 2

@app.route('/testing_game4_level2', methods=['GET'])
def testing_game4_level2():
    # Render a game template
    return render_template('./testing/testing_game4_level2.html')

@app.route('/car_testing_level2', methods=['GET'])
def car_testing_level2():
    # Render a game template
    return render_template('./testing/car_testing_level2.html')

@app.route('/bus_testing_level2', methods=['GET'])
def bus_testing_level2():
    # Render a game template
    return render_template('./testing/bus_testing_level2.html')

@app.route('/bicycle_testing_level2', methods=['GET'])
def bicycle_testing_level2():
    # Render a game template
    return render_template('./testing/bicycle_testing_level2.html')

@app.route('/helicopter_testing_level2', methods=['GET'])
def helicopter_testing_level2():
    # Render a game template
    return render_template('./testing/helicopter_testing_level2.html')

@app.route('/aeroplane_testing_level2', methods=['GET'])
def aeroplane_testing_level2():
    # Render a game template
    return render_template('./testing/aeroplane_testing_level2.html')

@app.route('/jet_testing_level2', methods=['GET'])
def jet_testing_level2():
    # Render a game template
    return render_template('./testing/jet_testing_level2.html')

@app.route('/boat_testing_level2', methods=['GET'])
def boat_testing_level2():
    # Render a game template
    return render_template('./testing/boat_testing_level2.html')

@app.route('/ship_testing_level2', methods=['GET'])
def ship_testing_level2():
    # Render a game template
    return render_template('./testing/ship_testing_level2.html')

@app.route('/cruise_testing_level2', methods=['GET'])
def cruise_testing_level2():
    # Render a game template
    return render_template('./testing/cruise_testing_level2.html')

# Routes for Transport Game Testing Level 3

@app.route('/testing_game4_level3', methods=['GET'])
def testing_game4_level3():
    # Render a game template
    return render_template('./testing/testing_game4_level3.html')


@app.route('/car_testing_level3', methods=['GET'])
def car_testing_level3():
    # Render a game template
    return render_template('./testing/car_testing_level3.html')

@app.route('/bus_testing_level3', methods=['GET'])
def bus_testing_level3():
    # Render a game template
    return render_template('./testing/bus_testing_level3.html')

@app.route('/bicycle_testing_level3', methods=['GET'])
def bicycle_testing_level3():
    # Render a game template
    return render_template('./testing/bicycle_testing_level3.html')

@app.route('/helicopter_testing_level3', methods=['GET'])
def helicopter_testing_level3():
    # Render a game template
    return render_template('./testing/helicopter_testing_level3.html')

@app.route('/aeroplane_testing_level3', methods=['GET'])
def aeroplane_testing_level3():
    # Render a game template
    return render_template('./testing/aeroplane_testing_level3.html')

@app.route('/jet_testing_level3', methods=['GET'])
def jet_testing_level3():
    # Render a game template
    return render_template('./testing/jet_testing_level3.html')

@app.route('/boat_testing_level3', methods=['GET'])
def boat_testing_level3():
    # Render a game template
    return render_template('./testing/boat_testing_level3.html')

@app.route('/ship_testing_level3', methods=['GET'])
def ship_testing_level3():
    # Render a game template
    return render_template('./testing/ship_testing_level3.html')

@app.route('/cruise_testing_level3', methods=['GET'])
def cruise_testing_level3():
    # Render a game template
    return render_template('./testing/cruise_testing_level3.html')

################################
# Game 5 - Food Game
################################

@app.route('/start_food_game/<int:user_id>/<int:disorder_id>', methods=['GET'])
def food_game_levels(user_id,disorder_id ):
    # Store the user_id and disorder_id_list in the session
    session['UserID'] = user_id
    session['DisorderID'] = disorder_id
    print("userid", user_id)
    print('disorder_id', disorder_id)
    # Render a game template
    return render_template('food_game_levels.html', user_id=user_id, disorder_id=disorder_id)


@app.route('/food_level1', methods=['GET'])
def food_level1():
    # Render a game template
    return render_template('food_level1.html')

@app.route('/food_level2', methods=['GET'])
def food_level2():
    # Render a game template
    return render_template('food_level2.html')

@app.route('/food_level3', methods=['GET'])
def food_level3():
    # Render a game template
    return render_template('food_level3.html')

@app.route('/testing_game5_levels', methods=['GET'])
def testing_game5_levels():
    # Render a game template
    return render_template('./testing/testing_game5_levels.html')


@app.route('/exit_food_levels', methods=['GET'])
def exit_food_levels():
    # Render a game template
    return render_template('food_game_levels.html')


# @app.route('/finish_food_level1', methods=['GET'])
# def finish_food_level1():
#     # Render a game template
#     return render_template('food_level1.html')

@app.route('/finish_food_level2', methods=['GET'])
def finish_food_level2():
    # Render a game template
    return render_template('food_level2.html')

@app.route('/finish_food_level3', methods=['GET'])
def finish_food_level3():
    # Render a game template
    return render_template('food_level3.html')

@app.route('/finish_food_testing_level2', methods=['GET'])
def finish_food_testing_level2():
    # Render a game template
    return render_template('./testing/testing_game5_level2.html')

@app.route('/finish_food_testing_level3', methods=['GET'])
def finish_food_testing_level3():
    # Render a game template
    return render_template('./testing/testing_game5_level3.html')


# routes for Food Game LEVEL 1
@app.route('/orange', methods=['GET'])
def orange():
    # Render a game template
    return render_template('orange.html')

@app.route('/apple', methods=['GET'])
def apple():
    # Render a game template
    return render_template('apple.html')

@app.route('/banana', methods=['GET'])
def banana():
    # Render a game template
    return render_template('banana.html')

@app.route('/milkshake', methods=['GET'])
def milkshake():
    # Render a game template
    return render_template('milkshake.html')

@app.route('/water', methods=['GET'])
def water():
    # Render a game template
    return render_template('water.html')

@app.route('/juice', methods=['GET'])
def juice():
    # Render a game template
    return render_template('juice.html')
@app.route('/egg', methods=['GET'])
def egg():
    # Render a game template
    return render_template('egg.html')

@app.route('/potato', methods=['GET'])
def potato():
    # Render a game template
    return render_template('potato.html')

@app.route('/rice', methods=['GET'])
def rice():
    # Render a game template
    return render_template('rice.html')


# routes for Food Game LEVEL 2

@app.route('/orange_level2', methods=['GET'])
def orange_level2():
    # Render a game template
    return render_template('orange_level2.html')

@app.route('/apple_level2', methods=['GET'])
def apple_level2():
    # Render a game template
    return render_template('apple_level2.html')

@app.route('/banana_level2', methods=['GET'])
def banana_level2():
    # Render a game template
    return render_template('banana_level2.html')

@app.route('/milkshake_level2', methods=['GET'])
def milkshake_level2():
    # Render a game template
    return render_template('milkshake_level2.html')

@app.route('/water_level2', methods=['GET'])
def water_level2():
    # Render a game template
    return render_template('water_level2.html')

@app.route('/juice_level2', methods=['GET'])
def juice_level2():
    # Render a game template
    return render_template('juice_level2.html')

@app.route('/egg_level2', methods=['GET'])
def egg_level2():
    # Render a game template
    return render_template('egg_level2.html')

@app.route('/potato_level2', methods=['GET'])
def potato_level2():
    # Render a game template
    return render_template('potato_level2.html')

@app.route('/rice_level2', methods=['GET'])
def rice_level2():
    # Render a game template
    return render_template('rice_level2.html')


# routes for Food Game LEVEL 3
@app.route('/orange_level3', methods=['GET'])
def orange_level3():
    # Render a game template
    return render_template('orange_level3.html')

@app.route('/apple_level3', methods=['GET'])
def apple_level3():
    # Render a game template
    return render_template('apple_level3.html')

@app.route('/banana_level3', methods=['GET'])
def banana_level3():
    # Render a game template
    return render_template('banana_level3.html')

@app.route('/milkshake_level3', methods=['GET'])
def milkshake_level3():
    # Render a game template
    return render_template('milkshake_level3.html')

@app.route('/water_level3', methods=['GET'])
def water_level3():
    # Render a game template
    return render_template('water_level3.html')

@app.route('/juice_level3', methods=['GET'])
def juice_level3():
    # Render a game template
    return render_template('juice_level3.html')

@app.route('/egg_level3', methods=['GET'])
def egg_level3():
    # Render a game template
    return render_template('egg_level3.html')


@app.route('/potato_level3', methods=['GET'])
def potato_level3():
    # Render a game template
    return render_template('potato_level3.html')

@app.route('/rice_level3', methods=['GET'])
def rice_level3():
    # Render a game template
    return render_template('rice_level3.html')

# # Routes for Food Game Testing Level 1
@app.route('/testing_game5_level1', methods=['GET'])
def testing_game5_level1():
    # Render a game template
    return render_template('./testing/testing_game5_level1.html')

@app.route('/orange_testing_level1', methods=['GET'])
def orange_testing_level1():
    # Render a game template
    return render_template('./testing/orange_testing_level1.html')

@app.route('/apple_testing_level1', methods=['GET'])
def apple_testing_level1():
    # Render a game template
    return render_template('./testing/apple_testing_level1.html')

@app.route('/banana_testing_level1', methods=['GET'])
def banana_testing_level1():
    # Render a game template
    return render_template('./testing/banana_testing_level1.html')

@app.route('/milkshake_testing_level1', methods=['GET'])
def milkshake_testing_level1():
    # Render a game template
    return render_template('./testing/milkshake_testing_level1.html')

@app.route('/water_testing_level1', methods=['GET'])
def water_testing_level1():
    # Render a game template
    return render_template('./testing/water_testing_level1.html')

@app.route('/juice_testing_level1', methods=['GET'])
def juice_testing_level1():
    # Render a game template
    return render_template('./testing/juice_testing_level1.html')

@app.route('/egg_testing_level1', methods=['GET'])
def egg_testing_level1():
    # Render a game template
    return render_template('./testing/egg_testing_level1.html')

@app.route('/potato_testing_level1', methods=['GET'])
def potato_testing_level1():
    # Render a game template
    return render_template('./testing/potato_testing_level1.html')

@app.route('/rice_testing_level1', methods=['GET'])
def rice_testing_level1():
    # Render a game template
    return render_template('./testing/rice_testing_level1.html')
# Routes for Food  Game Testing Level 2

@app.route('/testing_game5_level2', methods=['GET'])
def testing_game5_level2():
    # Render a game template
    return render_template('./testing/testing_game5_level2.html')

@app.route('/orange_testing_level2', methods=['GET'])
def orange_testing_level2():
    # Render a game template
    return render_template('./testing/orange_testing_level2.html')

@app.route('/apple_testing_level2', methods=['GET'])
def apple_testing_level2():
    # Render a game template
    return render_template('./testing/apple_testing_level2.html')

@app.route('/banana_testing_level2', methods=['GET'])
def banana_testing_level2():
    # Render a game template
    return render_template('./testing/banana_testing_level2.html')

@app.route('/milkshake_testing_level2', methods=['GET'])
def milkshake_testing_level2():
    # Render a game template
    return render_template('./testing/milkshake_testing_level2.html')

@app.route('/water_testing_level2', methods=['GET'])
def water_testing_level2():
    # Render a game template
    return render_template('./testing/water_testing_level2.html')

@app.route('/juice_testing_level2', methods=['GET'])
def juice_testing_level2():
    # Render a game template
    return render_template('./testing/juice_testing_level2.html')

@app.route('/egg_testing_level2', methods=['GET'])
def egg_testing_level2():
    # Render a game template
    return render_template('./testing/egg_testing_level2.html')

@app.route('/potato_testing_level2', methods=['GET'])
def potato_testing_level2():
    # Render a game template
    return render_template('./testing/potato_testing_level2.html')

@app.route('/rice_testing_level2', methods=['GET'])
def rice_testing_level2():
    # Render a game template
    return render_template('./testing/rice_testing_level2.html')


# Routes for Food Game Testing Level 3

@app.route('/testing_game5_level3', methods=['GET'])
def testing_game5_level3():
    # Render a game template
    return render_template('./testing/testing_game5_level3.html')

@app.route('/orange_testing_level3', methods=['GET'])
def orange_testing_level3():
    # Render a game template
    return render_template('./testing/orange_testing_level3.html')

@app.route('/apple_testing_level3', methods=['GET'])
def apple_testing_level3():
    # Render a game template
    return render_template('./testing/apple_testing_level3.html')

@app.route('/banana_testing_level3', methods=['GET'])
def banana_testing_level3():
    # Render a game template
    return render_template('./testing/banana_testing_level3.html')

@app.route('/milkshake_testing_level3', methods=['GET'])
def milkshake_testing_level3():
    # Render a game template
    return render_template('./testing/milkshake_testing_level3.html')

@app.route('/water_testing_level3', methods=['GET'])
def water_testing_level3():
    # Render a game template
    return render_template('./testing/water_testing_level3.html')

@app.route('/juice_testing_level3', methods=['GET'])
def juice_testing_level3():
    # Render a game template
    return render_template('./testing/juice_testing_level3.html')

@app.route('/egg_testing_level3', methods=['GET'])
def egg_testing_level3():
    # Render a game template
    return render_template('./testing/egg_testing_level3.html')

@app.route('/potato_testing_level3', methods=['GET'])
def potato_testing_level3():
    # Render a game template
    return render_template('./testing/potato_testing_level3.html')

@app.route('/rice_testing_level3', methods=['GET'])
def rice_testing_level3():
    # Render a game template
    return render_template('./testing/rice_testing_level3.html')

@app.route('/start_aaa_game/<int:user_id>/<int:disorder_id>', methods=['GET'])
def start_aaa_game(user_id, disorder_id):
    # Store the user_id and disorder_id_list in the session
    session['UserID'] = user_id
    session['DisorderID'] = disorder_id
    print("userid", user_id)
    # Render a game template
    return render_template('loudness_aaa_game.html', user_id=user_id, disorder_id=disorder_id)

@app.route('/submit_score', methods=['POST'])
def submit_score():
    try:
        data = request.get_json()
        if not data or 'UserID' not in data or 'DisorderID' not in data or 'Score' not in data:
            return jsonify({'error': 'Missing data'}), 400
        print("game name", data['GameName'])
        print("level name",data['LevelName'])
        # Simulated database interaction
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO public."UserExercises"("UserID", "DisorderID", "Score", "GameName", "LevelName")
            VALUES (%s, %s, %s, %s, %s);
        """, (data['UserID'], data['DisorderID'], data['Score'], data['GameName'], data['LevelName']))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'status': 'success', 'message': 'Score submitted successfully'})
    except Exception as e:
        print("Failed to submit score:", str(e))  # Logging the error
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5005)
