# Copyright cozybit, Inc 2010-2011
# All rights reserved

"""
Simple test of throughput from one mesh node to another.
"""

import os
import re
import sys
import wtf
import time
import importlib
import unittest
import subprocess
import threading
import Queue as queue

WTFCONFIG = wtf.conf
STATIONS = WTFCONFIG.mps
ADAPTERS = None
THIS_FILE = os.path.abspath(__file__)
THIS_DIR = os.path.dirname(THIS_FILE)

wpa_cli_error = "Expected exit status of 0 from wpa_cli, got %d instead"


def setUp(self):
    global ADAPTERS
    for station in STATIONS:
        station.comm.send_cmd("stop wpa_supplicant")
        station.comm.send_cmd("svc wifi disable")
        #station.comm.send_cmd("stop")
        #station.comm.send_cmd("start")
        station.comm.send_cmd("start wpa_supplicant")
    time.sleep(2)
    ADAPTERS = [WpasTestAdapter(sta) for sta in STATIONS]


def tearDown(self):
    for n in WTFCONFIG.nodes:
        n.stop()

    for adapter in adapters:
        adapter.cleanUp()


def buildAdbCommand(adb_id):
    return ["adb", "-s", adb_id, "shell", "wpa_cli",
            "-p/data/misc/wifi", "-iwlan0"]


class WpaCliMonitor(threading.Thread):

    regex = re.compile(r'^[\s>]+')

    def __init__(self, q, adb_id):
        threading.Thread.__init__(self)
        self._q = q
        self._process = subprocess.Popen(buildAdbCommand(adb_id),
                                         stdout=subprocess.PIPE)

    def _gen(self):
        while True:
            line = self._process.stdout.readline()
            if not line:
                return
            line = line.strip()
            print 'LaunchMonitorProcess:', line
            split = self.regex.split(line)
            if len(split) > 1:
                line = split[1]
            if not line.startswith("<3>"):
                continue
            yield line[3:]

    def run(self, *args, **kwargs):
        for line in self._gen():
            self._q.put(line)

    def stopMonitor(self):
        self._process.kill()


class EventMonitor (object):

    def __init__(self, sta):
        self._sta = sta
        self._q = queue.Queue()
        self._monitor = WpaCliMonitor(self._q, self._sta.comm.get_adb_id())

    def launch(self):
        self._monitor.start()

    def waitForEvent(self, eventName):
        while True:
            line = self._q.get(timeout=10)
            print 'waitForEvent:', line
            if line.startswith(eventName):
                return line

    def stopMonitor(self):
        self._monitor.stopMonitor()


class WpasTestAdapter (object):

    def __init__(self, sta):
        self._sta = sta
        self._comm = sta.comm
        self._monitor = EventMonitor(sta)
        self._monitor.launch()

    def cleanUp(self):
        self._monitor.stopMonitor()

    def _send_to_wpa_cli(self, cmd):
        cmd = "wpa_cli -p/data/misc/wifi -iwlan0 " + cmd
        print cmd
        code, resp = self._comm.send_cmd(cmd)
        if code != 0:
            raise ValueError(wpa_cli_error % (code,))
        return str.join('', resp)

    def _send_cmd_bool_resp(self, cmd):
        resp = self._send_to_wpa_cli(cmd).strip()
        if resp != "OK":
            raise ValueError(resp)
        return resp

    def _send_cmd_int_resp(self, cmd):
        resp = self._send_to_wpa_cli(cmd).strip()
        if not resp.isdigit():
            raise ValueError(resp)
        return resp

    def add_network(self):
        return self._send_cmd_int_resp("add_network")

    def set_network(self, networkId, prop, val):
        return self._send_cmd_bool_resp(
            "set_network " + networkId + " " + prop + " " + val)

    def set_network_quoted(self, networkId, prop, val):
        return self.set_network(networkId, prop, '\'"' + val + '"\'')

    def mesh_group_add(self, meshId):
        return self._send_cmd_bool_resp("mesh_group_add " + meshId)

    def remove_network(self, networkId):
        return self._send_cmd_bool_resp("remove_network " + networkId)

    def wait_event(self, eventList):
        for event in eventList:
            ev = self._monitor.waitForEvent(event)
            if ev is not None:
                return ev


class WpasMeshTest(unittest.TestCase):

    def __init__(self, *args, **kw):
        unittest.TestCase.__init__(self, *args, **kw)
        fp = os.path.join(THIS_DIR, "..", "submodules", "wpa_supplicant",
                          "tests", "hwsim")
        sys.path.append(fp)
        module = importlib.import_module("test_wpas_mesh")
        self._tests = {}
        for name in module.__dict__.keys():
            if name.startswith("test_") or name.startswith("_test"):
                self._tests[name] = module.__dict__[name]

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_wpas_mesh_mode_scan(self):
        self._tests['test_wpas_mesh_mode_scan'](ADAPTERS)

    def test_wpas_mesh_group_added(self):
        self._tests['test_wpas_mesh_group_added'](ADAPTERS)
