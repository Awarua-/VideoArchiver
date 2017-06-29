import click
import os
import shutil
import subprocess
import tempfile

H264_CHECK_STRING = "h264"


@click.command()
@click.argument('input', type=click.File('rb'))
def read(input):
    click.echo('transcoding file: {}'.format(input.name))
    session = Transcode(input.name)
    session.transcode()


class Transcode(object):

    def __init__(self, path):
        self.path = path

    def transcode(self):
        command = ("ffprobe -show_entries stream=codec_name " +
                   "-select_streams v:0 -of " +
                   "default=noprint_wrappers=1").split(' ')

        command.append(os.path.realpath(self.path))

        process = subprocess.Popen(command, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT,
                                   encoding='utf-8')
        out = ""
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                out = out + output
        rc = process.poll()

        print(out)
        if H264_CHECK_STRING not in out:
            click.echo("File was not encoded with {}, but instead was {}"
                       .format(H264_CHECK_STRING, out))
            return

        tfile = tempfile.NamedTemporaryFile(mode='w')

        command = "ffmpeg -c:v h264_cuvid -i ".split(' ')
        command.append(os.path.realpath(self.path))
        command + " -map 0 -c copy -c:v hevc_nvenc -preset slow ".split(' ')
        command.append(os.path.realpath(tfile.name))

        transcodeProcess = subprocess.Popen(command, stdout=subprocess.PIPE,
                                            stderr=subprocess.STDOUT,
                                            encoding='utf-8')

        out = ""
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output)
                out = out + output
        rc = process.poll()

        if rc != 0:
            click.echo("Failed to transcode file:\n{}"
                       .format(transcodeProcess.stdout))
            tfile.close()
            return

        #shutil.copyfile(os.path.realpath(tfile.name), os.path.realpath(self.path))

        tfile.close()

if __name__ == "__main__":
    file = read()
