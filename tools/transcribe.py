from google.cloud import speech_v1
from google.oauth2 import service_account
import io, os, sys, argparse


def select_model(language_code):
    if language_code in ["en-US"]:
        return "video"
    elif language_code in ["en-GB", "es-US"]:
        return "phone_call"
    else:
        return "default"

def split_path(path):
    "Splits freeswitch audio paths to individual params"
    info = {}
    for key in ["filename", "rate", "type", "voice", "country", "lang"]:
        path, info[key] = os.path.split(path)
    return info

def filegen(filepath, chunksize):
    with io.open(filepath, "rb") as f:
        while True:
            chunk = f.read(chunksize)
            yield chunk
            if(len(chunk) < chunksize):
                break

def recognize(client, wav_file_path):
    """
    Uses streaming recognition for short utterances
    Transcribe a short audio file using a specified transcription model
    Apparently video is the best
    """

    info = split_path(wav_file_path)
    code = info["lang"].lower() + "-" + info["country"].upper()

    config = {
        "model": select_model(code),
        "language_code": code,
        "sample_rate_hertz": int(info["rate"]),
        "encoding": speech_v1.enums.RecognitionConfig.AudioEncoding.LINEAR16
    }
    streaming_config = speech_v1.types.StreamingRecognitionConfig(
        config=config,
        single_utterance = False, # Not supported by some models
        interim_results = False
    )

    # Create an iterable generator for the file content
    requests = ( speech_v1.types.StreamingRecognizeRequest(audio_content=chunk) for chunk in filegen(wav_file_path, 1024) )

    responses = client.streaming_recognize(streaming_config, requests)
    for response in responses:
        if len(str(response.error)) > 5:
            print(response.error, file=sys.stderr)
            break

        # First alternative is the most probable result
        result = response.results[0]
        if result.is_final:
            return result.alternatives[0].transcript

def get_wavs(startpath):
    "Generator for wav files in directory"
    for root, dirs, files in os.walk(startpath, topdown=False):
        for name in files:
            if name.endswith(".wav"):
                yield os.path.join(root, name)

def check_enCA(path):
    "Check if the same file exists in the en-CA sounds files"
    pathl = list(path.split('/'))
    pathl[-4] = "june"
    pathl[-5] = "ca"
    pathl[-6] = "en"
    enCA = "/".join(pathl)
    return os.path.isfile(enCA)

def fileexists(filepath):
    if os.path.isfile(filepath):
        return filepath
    else:
        raise argparse.ArgumentTypeError("file does not exist")

def main():
    parser = argparse.ArgumentParser(description="""Uses Google Cloud Speech to transcribe freeswitch sounds.
Expects en-US and en-CA 48000 sounds to be extracted in working directory""")
    parser.add_argument("service_account_file", type=fileexists)
    parser.add_argument("--resume_after", type=fileexists)
    args = parser.parse_args()

    # Set credentials:
    credentials = service_account.Credentials.from_service_account_file(
        args.service_account_file,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )
    client = speech_v1.SpeechClient(credentials=credentials)

    # Header
    print('"{}","{}","{}"'.format("filepath","transcription","is in en-CA"))
    for wav in get_wavs(os.path.join(os.getcwd(), "en", "us")):
        if args.resume_after:
            if wav.endswith(args.resume_after.lstrip("~.")):
                args.resume_after = None
            continue
        transcript = recognize(client, wav)
        print('"{}","{}","{}"'.format(wav, transcript, check_enCA(wav)), flush=True)


if __name__ == "__main__":
    main()
