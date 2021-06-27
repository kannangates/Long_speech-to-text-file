import mimetypes
import streamlit as st
import os
from pydub import AudioSegment
import wave
from google.cloud import storage
from google.cloud import speech

output_filepath = "/Users/kannaperumalc/code/Transcripts/"
# Converting mp3 to wav format


def mp3_to_wav(audio_file_name):
    if audio_file_name.split('.')[1] == 'mp3':
        st.write("This file wil be converted from mp3 to Wav")
        sound = AudioSegment.from_mp3(audio_file_name)
        audio_file_name = audio_file_name.split('.')[0] + '.wav'
        sound.export(audio_file_name, format="wav")
        st.write("mp3_to_wav converted")


# Converting Frame_rate


def frame_rate_channel(audio_file_name):
    with wave.open(audio_file_name, "rb") as wave_file:
        frame_rate = wave_file.getframerate()
        print("\n\n** FILE CONVERSION SUCCESSFUL **")
        channels = wave_file.getnchannels()
        return frame_rate, channels

# Converting stereo to mono, i.e. changing to 1 channel


def stereo_to_mono(audio_file_name):
    sound = AudioSegment.from_wav(audio_file_name)
    sound = sound.set_channels(1)
    sound.export(audio_file_name, format="wav")


# Uploading audio file to Google Cloud
def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)

# Deleting audio file


def delete_blob(bucket_name, blob_name):
    """Deletes a blob from the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.delete()


# GOOGLE TRANSCRIBE
def google_transcribe(audio_file_name):

    file_name = filepath + audio_file_name
    mp3_to_wav(file_name)

    # The name of the audio file to transcribe
    frame_rate, channels = frame_rate_channel(file_name)

    if channels > 1:
        stereo_to_mono(file_name)

    bucket_name = 'aud2txt'
    source_file_name = filepath + audio_file_name
    destination_blob_name = audio_file_name

    upload_blob(bucket_name, source_file_name, destination_blob_name)

    gcs_uri = 'gs://aud2txt/' + audio_file_name
    transcript = ''

    client = speech.SpeechClient()
    audio = speech.RecognitionAudio(uri=gcs_uri)

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=frame_rate,
        language_code='en-US')

    # Detects speech in the audio file
    operation = client.long_running_recognize(config, audio)
    response = operation.result(timeout=10000)

    for result in response.results:
        transcript += result.alternatives[0].transcript

    delete_blob(bucket_name, destination_blob_name)
    return transcript


def write_transcripts(transcript_filename, transcript):
    f = open(output_filepath + transcript_filename, "w+")
    f.write(transcript)
    f.close()


is_check = st.checkbox("Unlock Audio file conversion")
if is_check:
    uploaded_file = st.file_uploader("Upload Files", type=['wav', 'mp3'])
    if uploaded_file is not None:
        file_details = {"FileName": uploaded_file.name,
                        "FileType": uploaded_file.type, "FileSize": uploaded_file.size}
        st.write(file_details)
        st.write(uploaded_file)
        if st.button('Generate text file'):
            #filepath = uploaded_file
            #st.write("file assigned")
            for audio_file_name in os.path.splitext(uploaded_file):
                st.write("Starting transcript")
                st.write(audio_file_name)
                transcript = google_transcribe(audio_file_name)
                transcript_filename = audio_file_name.split('.')[0] + '.txt'
                write_transcripts(transcript_filename, transcript)
