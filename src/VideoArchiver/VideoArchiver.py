"""Transcoding h264 -> h265.

This module transcodes a single file from h264 to h265 using ffmpeg
and hardware acceleration where supported
"""

import click
import os
import shutil
import subprocess
import tempfile

H264_CHECK_STRING = "h264"
NVENC_CHECK_STRING = "supports NVENC"


@click.command()
@click.argument('input', type=click.File('rb'))
def read(input_path):
    """Transcodes the file in the given path.

    Args:
        input_path (str): path to file
    """
    click.echo('transcoding file: {}'.format(input_path.name))
    session = Transcode(input_path.name)
    session.run()


class Transcode(object):
    """The transcode instance.

    Args:
        path (str): path of file to transcode

    Atributes:
        path (str): path of file to transcode
        tfile (object): tempory file object
        hardware_support (int): indicates hardware support for transcoding
    """

    def __init__(self, path='./placeholder'):
        self.path = path
        self.hardware_support = self.__check_hardware_suppport()

    def run(self):
        """Runs the transcoding process."""
        if self.__check_if_file_valid() == 0:
            self.__create_temp_file()
            if self.__transcode() == 0:
                self.__move_file()

            self.__close_temp_file()

    def set_path(self, path):
        """Sets the path for the file to be transcoded.

        :param path: Sets path of file to transcode
        """
        self.path = path

    @classmethod
    def ___run_process(self, command):
        process = subprocess.Popen(command, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT,
                                   encoding='utf-8')
        out = ""
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                out += output
        rc = process.poll()

        return out, rc

    def __transcode(self):
        if self.hardware_support == 0:
            return self.__transcode_hardware()
        else:
            return self.__transcode_software()

    def __check_if_file_valid(self):
        command = ("ffprobe -v quiet -show_entries stream=codec_name " +
                   "-select_streams v:0 -of " +
                   "default=noprint_wrappers=1").split(' ')

        command.append(os.path.realpath(self.path))

        out, rc = self.___run_process(command)

        if H264_CHECK_STRING not in out:
            click.echo("File was not encoded with {}, but instead was {}"
                       .format(H264_CHECK_STRING, out))
            return -1
        return rc

    def __transcode_hardware(self):
        command = "ffmpeg -c:v h264_cuvid -i".split(' ')
        command.append(os.path.realpath(self.path))
        command += "-map 0 -c copy -c:v hevc_nvenc -preset slow".split(' ')
        command.append(os.path.realpath(self.tfile.name))
        command.append("-y")
        out, rc = self.___run_process(command)

        if rc != 0:
            click.echo("Failed to transcode file:\n{}"
                       .format(out))
            return -1
        return 0

    def __check_hardware_suppport(self):
        command = "ffmpeg -f lavfi -i nullsrc -c:v nvenc -gpu list -f null -"
        command = command.split(' ')

        out, rc = self.___run_process(command)

        if NVENC_CHECK_STRING not in out:
            return -1

        return rc

    def __transcode_software(self):
        command = "ffmpeg -c:v h264 -i".split(' ')
        command.append(os.path.realpath(self.path))
        next_command = "-map 0 -c copy -c:v libx265 -preset medium -crf 28"
        command += next_command.split(' ')
        command.append(os.path.realpath(self.tfile.name))
        command.append("-y")

        out, rc = self.___run_process(command)

        if rc != 0:
            click.echo("Failed to transcode file:\n{}"
                       .format(out))
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
    read()
