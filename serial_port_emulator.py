#!/usr/bin/env python3

# Copyright 2021 Ezra Morris
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import argparse
from contextlib import ExitStack
import os
import pty
from selectors import DefaultSelector as Selector, EVENT_READ
import sys
import tty

link_names=[]

def run(num_ports, loopback=False, debug=False):
    """Creates several serial ports. When data is received from one port, sends
    to all the other ports."""

    master_files = {}  # Dict of master fd to master file object.
    slave_names = {}  # Dict of master fd to slave name.

    try:
        os.mkdir('/tmp/dev')
    except:
        pass
    port_num=0
    for _ in range(num_ports):
        master_fd, slave_fd = pty.openpty()
        tty.setraw(master_fd)
        os.set_blocking(master_fd, False)
        slave_name = os.ttyname(slave_fd)
        master_files[master_fd] = open(master_fd, 'r+b', buffering=0)
        slave_names[master_fd] = slave_name
        link_names.append("/tmp/dev/serial_port_%d"%port_num)
        try:
            os.symlink(slave_name, link_names[port_num])
        except:
            os.remove(link_names[port_num])
            os.symlink(slave_name, link_names[port_num])
        print("Name '%s' -> '%s'" % (link_names[port_num], slave_name))
        port_num += 1

    with Selector() as selector, ExitStack() as stack:
        # Context manage all the master file objects, and add to selector.
        for fd, f in master_files.items():
            stack.enter_context(f)
            selector.register(fd, EVENT_READ)

        while True:
            for key, events in selector.select():
                if not events & EVENT_READ:
                    continue

                data = master_files[key.fileobj].read()
                if debug:
                    print(slave_names[key.fileobj], data, file=sys.stderr)

                # Write to master files. If loopback is False, don't write
                # to the sending file.
                for fd, f in master_files.items():
                    if loopback or fd != key.fileobj:
                        f.write(data)


def main():
    parser = argparse.ArgumentParser(
        description='Create a hub of virtual serial ports, which will stay '
        'available until the program exits. Once set up, the port names be '
        'printed to stdout, one per line.'
    )
    parser.add_argument('-n ', '--num_ports', type=int, default=2,
                        help='number of ports to create')
    parser.add_argument('-l', '--loopback', action='store_false', default=False,
                        help='echo data back to the sending device too')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='log received data to stderr')
    args = parser.parse_args()

    num_ports = (args.num_ports if args.num_ports > 0 else 2)

    # Catch KeyboardInterrupt so it doesn't print traceback.
    try:
        run(num_ports, args.loopback, args.debug)
    except KeyboardInterrupt:
        for link_name in link_names:
            os.remove(link_name)
        os.rmdir('/tmp/dev')


if __name__ == '__main__':
    main()
