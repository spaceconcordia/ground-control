#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2014 Shawn <shawn dot bulger at spaceconcordia dot ca>
#
# Distributed under terms of the MIT license.

"""
This is a command-line interface to run the ground station interactively
start   - on   - s : start the ground station for normal operation
mock    - mk   - m : start the mock satellite interaction locally (no radio)
exit    - quit - q : close the program
help    - menu - h : show this menu
"""

#import pexpect
import signal
import os
import stat
import subprocess
import time
import sys

try:
    raw_input
except NameError:
    raw_input = input

#-------------------------------------------------------------
# GLOBALS 
#-------------------------------------------------------------
ground_netman = None
ground_commander = None
mock_satellite_netman = None
mock_satellite_commander = None

GS_BIN_PATH = "/usr/bin/";
GS_PATH = {
    "LOG"            : '/home/logs/gs.log',
    "INPUT_PIPE"     : '/home/pipes/gnd-input',
    "NETMAN"         : GS_BIN_PATH+'gnd',
    "MOCK_SAT_NM"    : GS_BIN_PATH+'sat',
    "MOCK_SAT_CMDR"  : GS_BIN_PATH+'space-commander',
    "DECODE_RB"      : GS_BIN_PATH+'decode-command.rb',
    "GETLOG_RB"      : GS_BIN_PATH+'getlog-command.rb',
    "GETTIME_RB"     : GS_BIN_PATH+'gettime-command.rb',
    "REBOOT_RB"      : GS_BIN_PATH+'reboot-command.rb',
    "UPDATE_RB"      : GS_BIN_PATH+'update-command.rb',
    "STEP2_RB"       : GS_BIN_PATH+'step2.rb'
}

KW_GETTIME  = "010001313337"    #0x01 0x00 0x01 0x31 0x33 0x37
KW_CONFIRM  = "02000121242b"    #0x02 0x00 0x01 0x21 0x24 0x2b
KW_ACK      = "31210052d5"      #0x31 0x21 0x00 0x52 0xd5

#-------------------------------------------------------------
# WRAPPER FUNCTIONS FOR SUBPROCESS 
#-------------------------------------------------------------

def subCustom(args):
    return subprocess.Popen(
            args,
            bufsize=0,
            executable=None,
            stdin=None,
            stdout=None,
            stderr=None,
            preexec_fn=None,
            close_fds=False,
            shell=False,
            cwd=None,
            universal_newlines=False,
            startupinfo=None,
            creationflags=0,
            evn=None
    )

def subP(args):
    return subprocess.Popen(
            args,
            shell=False,
            stdout=subprocess.PIPE
    )

def subShell(args):
    return subprocess.Popen(
            args,
            shell=True,
            executable="/bin/bash"
    )


#-------------------------------------------------------------
# VARIOUS SYSTEM WRAPPER FUNCTIONS 
#-------------------------------------------------------------
def whereis(program):
    for path in os.environ.get('PATH', '').split(':'):
        if os.path.exists(os.path.join(path, program)) and \
            not os.path.isdir(os.path.join(path, program)):
                return os.path.join(path, program)
    return None

def usage():
    print(globals()['__doc__'])

def fail(error):
    print "\r\nFailed: "+error+" Aborting..."
    sys.exit(1)

def exit(exit_message="No message"):
    print "\r\nExiting: "+exit_message
    sys.exit(1)

def signal_handler(signal, frame):
  print '\r\nCaught Cntl+C!'
signal.signal(signal.SIGINT, signal_handler)


#-------------------------------------------------------------
# GROUND STATION FUNCTIONS 
#-------------------------------------------------------------
def check_requirements():
    for key, requirement in GS_PATH.items():
        if ( os.path.isfile(requirement) ) or ( stat.S_ISFIFO(os.stat(requirement).st_mode) ):
            continue
        else : fail(key+" ("+requirement+") is not present!")
            
def start_ground_netman():
  print "[NOTICE] STARTING GROUND NETMAN"
  return subP(GS_PATH["NETMAN"])

def start_mock_satellite_netman() :
  print "[NOTICE] STARTING MOCK SATELLITE NETMAN"
  return subP(GS_PATH["MOCK_SAT_NM"])

def start_mock_satellite_commander() :
  print "[NOTICE] STARTING MOCK SATELLITE COMMANDER"
  return subP(GS_PATH["MOCK_SAT_CMDR"])

def is_subprocess_running(subprocess):
    if subprocess is None:
        return False
    if subprocess.poll() is None:
        return True
    else:
        return False

def tear_down() :
    print "[NOTICE] Tearing down all running processes"
    global ground_netman
    global ground_commander
    global mock_satellite_netman
    if ( ground_netman is not None ) :
        ground_netman.terminate()
    if ( ground_commander is not None ) :
        ground_commander.terminate()
    if ( mock_satellite_netman is not None ) :
        mock_satellite_netman.terminate()
    if ( mock_satellite_commander is not None ) :
        mock_satellite_commander.terminate()

def start_ground_station():
  # test local radio

  global ground_netman
  ground_netman = start_ground_netman()

  # ping satellite

  # start ground-commmander and drop to shell
  global ground_commander
  ground_commander = start_ground_commander()
#end def

def start_mock_interaction():
  global mock_satellite_netman
  mock_satellite_netman = start_mock_satellite_netman()
  global mock_satellite_commander
  mock_satellite_commander = start_mock_satellite_commander()
  start_ground_station()

def start_ground_commander(): 
  print "[NOTICE] STARTING GROUND COMMANDER"
  ground_commander = subP(['python', 'ground-commander.py'])
  stdout, stderr = ground_commander.communicate()
  print stdout
  print stderr

def go_no_go():
  global ground_netman
  return "GO >> " if is_subprocess_running(ground_netman) is True else "NOGO >> "

def command_line_interface():
  print 'Enter commands for the ground station below.\r\nType "menu" for predefined commands, and "exit" to quit'
  input=1
  while 1:
    input=raw_input( go_no_go() + time.strftime("%H:%M:%S") + " >> " )
    if ((input == "exit") | (input == "q")):
      tear_down()
      exit("Because you asked to.")    
    if ((input == "menu") | (input == "help") | (input == "h")):
      usage()
    if ((input == "start") | (input == "on") | (input == "s")):
      start_ground_station()
    if ((input == "mock") | (input == "mk") | (input == "m")):
      start_mock_interaction()

#-------------------------------------------------------------
# GROUND STATION FUNCTIONS 
#-------------------------------------------------------------
def main():
    # TODO not working #location = whereis('echo')
    #if location is not None:
    #    print location
    #subShell(['echo', 'hello space'])
    #process = subprocess.Popen(['echo', 'Hello World!'], shell=False, stdout=subprocess.PIPE)
    #print process.communicate()
    usage()
    check_requirements()
    command_line_interface()

    # off
    tear_down()
    # exit()
    exit("Reached end of main")

if __name__ == '__main__':
    main()
