"""Transcoding h264 -> h265.

This module transcodes a single file from h264 to h265 using ffmpeg
and hardware acceleration where supported
"""

import click
import os
import shutil
import subprocess
import tempfile
import time

H264_CHECK_STRING = "h264"
# Warning NVENC check string appears to be unstable between versions of ffmpeg
NVENC_CHECK_STRING = "GPU #0"


def transcode_files(path, age):
    """Transcodes the fileS in the given path.

    Args:
        input_path (str): path to fileS
    """
    session = Transcode()
    session.set_age(age)
    if os.path.isdir(path):
        for root, dirs, files in os.walk(path):
            for file in files:
                path = os.path.join(root, file)
                click.echo('transcoding file: {}'.format(path))
                session.set_path(path)
                session.run()
    elif os.path.isfile(path):
        click.echo('transcoding file: {}'.format(path))
        session.set_path(path)
        session.run()
    else:
        click.echo('input not recognised')


@click.command()
@click.argument('input_path', type=click.Path())
@click.option('--age', default=30)
def read(input_path, age):
    """Read command input function."""
    transcode_files(input_path, age)


class Transcode(object):
    """The transcode instance.

    Args:
        path (str): path of file to transcode
        age (int): number of days old the file needs to be before being transcoded.

    Atributes:
        path (str): path of file to transcode
        tfile (object): tempory file object
        hardware_support (int): indicates hardware support for transcoding
    """

    def __init__(self, path='./placeholder', age=30):
        self.path = path
        self.age = age
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

    def set_age(self, age):
        """Threshold for age of file.

        :param age: Age of file threshold
        """
        self.age = age

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

        if self.__check_if_file_is_old():
            click.echo("File was still recent, not transcoding")
            return -1

        return rc

    def __check_if_file_is_old(self):
        file_time = os.path.getmtime(self.path)
        now = time.time()
        threshold = self.age * 24 * 60 * 60
        if now - file_time < threshold:
            return 1
        return 0

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
        command = "ffmpeg -f lavfi -i nullsrc -c:v hevc_nvenc -gpu list -f null -"
        command = command.split(' ')

        out, rc = self.___run_process(command)

        if NVENC_CHECK_STRING not in out:
            return -1
        else:
            return 0

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
