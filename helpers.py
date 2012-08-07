"""
Jumpshot HipChat Bot Handler Helper Routines
"""

import re
import time
import shlex
import string
import random
import subprocess


########################################################################################################################
def launch_command (args, stdin=""):
    '''
    Launch the specified command with args (each as a separate item of a list).

    @type   args: List or String
    @param  args: First item in list is the command, subsequent items are the arguments. If a String is provided instead
                  of a list then it will be converted with shlex.split().
    @type  stdin: String
    @param stdin: Optional input to write to opened processes stdin.

    @rtype:  Tuple
    @return: (output, errors)
    '''

    # if a list was not provided, convert the string into one.
    if type(args) is not list:
        args = shlex.split(args)

    process  = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate(stdin)

    return out, err


########################################################################################################################
def commify (n):
    """
    Format a large integer with human readable commas.

    @type  n: Integer
    @param n: Integer to format.

    @rtype:  String
    @return: Formatted integer.
    """

    if n is not str:
        n = str(n)

    while True:
        (n, count) = re.subn(r'^([-+]?\d+)(\d{3})', r'\1,\2', n)
        if count == 0:
            break

    return n


########################################################################################################################
def elapsed_time (start, finish=None):
    """
    Determine time elapsed in days, hours, minutes and seconds.

    @type  start:  Float
    @param start:  Starting time.time()
    @type  finish: Float
    @param finish: Ending time.time()

    @rtype:  Tuple
    @return: int(days), int(hours), int(minutes), int(seconds)
    """

    if not finish:
        finish = time.time()

    uptime  = int(float(finish) - float(start))
    days    = uptime  / 86400
    uptime -= days    * 86400
    hours   = uptime  / 3600
    uptime -= hours   * 3600
    minutes = uptime  / 60
    uptime -= minutes * 60
    seconds = uptime

    return days, hours, minutes, seconds


########################################################################################################################
def levenshtein_distance (first, second):
    """
    Provides the Levenshtein distance between two strings. ie: The number of transformations required to transform
    one string to the other.

    @type  first:  String
    @param first:  First string.
    @type  second: String
    @param second: Second string.

    @rtype:  Integer
    @return: Distance between strings.
    """

    if len(first) > len(second):
        first, second = second, first

    if len(second) == 0:
        return len(first)

    first_length  = len(first)  + 1
    second_length = len(second) + 1

    distance_matrix = [range(second_length) for x in range(first_length)]

    for i in range(1, first_length):
        for j in range(1, second_length):
            deletion     = distance_matrix[i-1][j] + 1
            insertion    = distance_matrix[i][j-1] + 1
            substitution = distance_matrix[i-1][j-1]

            if first[i-1] != second[j-1]:
                substitution += 1

            distance_matrix[i][j] = min(insertion, deletion, substitution)

    return distance_matrix[first_length-1][second_length-1]


########################################################################################################################
def random_emoticon_fail ():
    return random.choice(["(jackie)", "(sweetjesus)", "(troll)", "(dumb)", "(yodawg)"])


########################################################################################################################
def sanitize (s):
    return "".join([c for c in s if c in string.printable])
