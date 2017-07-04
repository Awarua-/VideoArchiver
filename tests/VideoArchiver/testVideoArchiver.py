import distutils
import os
import pytest
import shutil
import time
from src.VideoArchiver import VideoArchiver


dir_path = os.path.dirname(os.path.realpath(__file__))
test_data = [("../data/hc.mp4", -1), ("../data/c.mp4", 0),
             ("../data", -1), ("../data/junk.txt", -1), ("../data/more_data/c.mp4", -1)]
test_transcode_data = [("../data/c.mp4", "../data/test.mp4", 0),
                       ("../data/hc.mp4", "../data/test.mp4", -1)]
day_threshold = 30


class TestVideoArchiver(object):

    def setup_method(self):
        self.archiver = VideoArchiver.Transcode()
        self.archiver.set_age(day_threshold)
        path = os.path.join(dir_path, "../data/c.mp4")
        now = time.time()
        new_time = now - (day_threshold + 1) * 24 * 60 * 60
        os.utime(path, times=(new_time, new_time))
        shutil.copyfile(path, os.path.join(dir_path, "../data/test.mp4"))

    def teardown_method(self):
        os.remove(os.path.join(dir_path, "../data/test.mp4"))

    @pytest.mark.parametrize("path,expected", test_data)
    def test___check_if_file_valid(self, path, expected):
        self.archiver.set_path(os.path.join(dir_path, path))
        result = self.archiver._Transcode__check_if_file_valid()
        assert result == expected

    @pytest.mark.parametrize("path,out,expected", test_transcode_data)
    def test___transcode(self, path, out, expected):
        self.archiver.set_path(os.path.join(dir_path, path))
        self.archiver.tfile = type('mock', (object,),
                                   {"name": os.path.join(dir_path, out)})
        result = self.archiver._Transcode__transcode()
        assert result == expected

    def test_directory(self):
        path = os.path.abspath(os.path.join(dir_path, "../temp_data"))
        distutils.dir_util.copy_tree(os.path.join(dir_path, "../data"), path)
        VideoArchiver.transcode_files(path, day_threshold)
        shutil.rmtree(path)
