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
    session.run()


class Transcode(object):

    def __init__(self, path='./placeholder'):
        """This initialises the Transcode session."""
        self.path = path
        self.__create_temp_file()

    def run(self):
        if self.__check_if_file_valid() == 0:
            if self.__transcode() == 0:
                self.__move_file()

        self.__close_temp_file()

    def __check_if_file_valid(self):
        command = ("ffprobe -v quiet -show_entries stream=codec_name " +
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
        print(out)
        if H264_CHECK_STRING not in out:
            click.echo("File was not encoded with {}, but instead was {}"
                       .format(H264_CHECK_STRING, out))
            return -1
        return process.poll()

    def __transcode(self):
        command = "ffmpeg -c:v h264_cuvid -i".split(' ')
        command.append(os.path.realpath(self.path))
        command += "-map 0 -c copy -c:v hevc_nvenc -preset slow".split(' ')
        command.append(os.path.realpath(self.tfile.name))
        command.append("-y")
        transcodeProcess = subprocess.Popen(command, stdout=subprocess.PIPE,
                                            stderr=subprocess.STDOUT,
                                            encoding='utf-8')

        out = ""
        while True:
            output = transcodeProcess.stdout.readline()
            if output == '' and transcodeProcess.poll() is not None:
                break
            if output:
                out += output
        rc = transcodeProcess.poll()

        if rc != 0:
            click.echo("Failed to transcode file:\n{}"
                       .format(transcodeProcess.stdout))
            return -1
        return 0

    def __move_file(self):
        shutil.copyfile(os.path.realpath(self.tfile.name),
                        os.path.realpath(self.path))

    def __close_temp_file(self):
        self.tfile.close()

    def __create_temp_file(self):
        self.tfile = tempfile.NamedTemporaryFile(mode='w')
        self.tfile.name += '.mkv'

if __name__ == "__main__":
    file = read()
