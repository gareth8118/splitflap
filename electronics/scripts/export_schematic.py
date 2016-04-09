#!/usr/bin/env python

#   Copyright 2016 Scott Bezek
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import logging
import os
import subprocess
import sys
import tempfile
import time

from contextlib import contextmanager

electronics_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
repo_root = os.path.dirname(electronics_root)
sys.path.append(repo_root)

from thirdparty.xvfbwrapper.xvfbwrapper import Xvfb
from util import file_util, rev_info

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class PopenContext(subprocess.Popen):
    def __enter__(self):
        return self
    def __exit__(self, type, value, traceback):
        if self.stdout:
            self.stdout.close()
        if self.stderr:
            self.stderr.close()
        if self.stdin:
            self.stdin.close()
        if type:
            self.terminate()
        # Wait for the process to terminate, to avoid zombies.
        self.wait()

def xdotool(command):
    return subprocess.check_output(['xdotool'] + command)

def wait_for_window(name, window_regex, timeout=10):
    DELAY = 0.5
    logger.info('Waiting for %s window...', name)
    for i in range(int(timeout/DELAY)):
        try:
            xdotool(['search', '--name', window_regex])
            logger.info('Found %s window', name)
            return
        except subprocess.CalledProcessError:
            pass
        time.sleep(DELAY)
    raise RuntimeError('Timed out waiting for %s window' % name)

@contextmanager
def recorded_xvfb(video_filename, **xvfb_args):
    with Xvfb(**xvfb_args):
        with PopenContext([
                'recordmydesktop',
                '--no-sound',
                '--no-frame',
                '--on-the-fly-encoding',
                '-o', video_filename], close_fds=True) as screencast_proc: 
            yield
            screencast_proc.terminate()

def _get_versioned_contents(filename):
    with open(filename, 'rb') as schematic:
        original_contents = schematic.read()
        return original_contents, original_contents \
            .replace('Date ""', 'Date "%s"' % rev_info.current_date()) \
            .replace('Rev ""', 'Rev "%s"' % rev_info.git_short_rev())

@contextmanager
def versioned_schematic(filename):
    original_contents, versioned_contents = _get_versioned_contents(filename)
    with open(filename, 'wb') as temp_schematic:
        logger.debug('Writing to %s', filename)
        temp_schematic.write(versioned_contents)
    try:
        yield
    finally:
        with open(filename, 'wb') as temp_schematic:
            logger.debug('Restoring %s', filename)
            temp_schematic.write(original_contents)

def eeschema_plot_schematic(output_directory):
    wait_for_window('eeschema', '\[')

    logger.info('Focus main eeschema window')
    xdotool(['search', '--name', '\[', 'windowfocus'])

    logger.info('Open File->Plot->Plot')
    xdotool(['key', 'alt+f'])
    xdotool(['key', 'p'])
    xdotool(['key', 'p'])

    wait_for_window('plot', 'Plot')
    xdotool(['search', '--name', 'Plot', 'windowfocus'])

    logger.info('Enter build output directory')
    xdotool(['type', output_directory])

    logger.info('Select PDF plot format')
    xdotool([
        'key',
        'Tab',
        'Tab',
        'Tab',
        'Tab',
        'Tab',
        'Up',
        'Up',
        'Up',
        'space',
    ])

    logger.info('Plot')
    xdotool(['key', 'Return'])

    logger.info('Wait before shutdown')
    time.sleep(2)

def export_schematic():
    schematic_file = os.path.join(electronics_root, 'splitflap.sch')
    output_dir = os.path.join(electronics_root, 'build')
    file_util.mkdir_p(output_dir)

    screencast_output_file = os.path.join(output_dir, 'export_schematic_screencast.ogv')
    schematic_output_pdf_file = os.path.join(output_dir, 'splitflap.pdf')
    schematic_output_png_file = os.path.join(output_dir, 'schematic.png')

    with versioned_schematic(schematic_file):
        with recorded_xvfb(screencast_output_file, width=800, height=600, colordepth=24):
            with PopenContext(['eeschema', schematic_file], close_fds=True) as eeschema_proc:
                eeschema_plot_schematic(output_dir)
                eeschema_proc.terminate()

    logger.info('Rasterize')
    subprocess.check_call([
        'convert',
        '-density', '96',
        schematic_output_pdf_file,
       '-background', 'white',
       '-alpha', 'remove',
       schematic_output_png_file,
   ])
    
if __name__ == '__main__':
    export_schematic()

