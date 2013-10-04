#-------------------------------------------------------------------------------
# Name:        dtinfo
# Purpose:     Process a Chrome dev tools timeline or trace and produce stats
#
# Copyright (c) 2010, Google Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions and the following disclaimer in the documentation
#     and/or other materials provided with the distribution.
#   * Neither the name of the <ORGANIZATION> nor the names of its contributors
#     may be used to endorse or promote products derived from this software
#     without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#-------------------------------------------------------------------------------

import sys
import glob
import json

metrics = ['url', 'domContentLoaded', 'onload']

def ProcessDevTools(events):
    started = False
    stats = {}
    for event in events:
        if 'method' in event:
            if ('timestamp' not in event and
                'params' in event and
                'record' in event['params'] and
                'startTime' in event['params']['record']):
                event['timestamp'] = event['params']['record']['startTime'];
            elif ('timestamp' not in event and
                  'params' in event and
                  'timestamp' in event['params']):
                event['timestamp'] = event['params']['timestamp'] * 1000;
            if not started:
                url = ''
                if (event['method'] == 'Network.requestWillBeSent' and
                    'params' in event and
                    'request' in event['params'] and
                    'url' in event['params']['request']):
                    url = event['params']['request']['url']
                elif (event['method'] == 'Timeline.eventRecorded' and
                      'params' in event and
                      'record' in event['params'] and
                      'type' in event['params']['record'] and
                      'data' in event['params']['record'] and
                      'url' in event['params']['record']['data'] and
                      event['params']['record']['type']=='ResourceSendRequest'):
                    url = event['params']['record']['data']['url']
                if (len(url) and url.find('localhost', 0, 20) == -1):
                    stats['url'] = url
                    started = True
            if started:
                if (event['method'] == 'Network.requestWillBeSent' and
                    ('startTime' not in stats or
                     event['timestamp'] < stats['startTime'])):
                    stats['startTime'] = event['timestamp'];
                if (event['method'] == 'Page.loadEventFired' and
                    ('onload' not in stats or
                     event['timestamp'] > stats['onload'])):
                    stats['onload'] = event['timestamp'];
                if (event['method'] == 'Page.domContentEventFired' and
                    ('domContentLoaded' not in stats or
                     event['timestamp'] > stats['domContentLoaded'])):
                    stats['domContentLoaded'] = event['timestamp'];
    return stats

def ProcessFile(dtfile):
    file = open(dtfile, "r")
    events = json.load(file)
    file.close()
    output = dtfile
    if len(events):
        stats = ProcessDevTools(events)
        if ('startTime' in stats and
            stats['startTime'] > 0):
            for metric in metrics:
                if metric in stats:
                    if metric == 'url':
                        output += ',"' + stats['url'].replace('"', '""') + '"'
                    elif stats[metric] >= stats['startTime']:
                        elapsed = stats[metric] - stats['startTime'];
                        output += ",%.3f" % (elapsed / 1000)
                    else:
                        output += ','
                else:
                    output += ','
        else:
            output += ','
    print output

if len(sys.argv) == 1:
    print "Usage: dtinfo <dev tools file(s) to process>\r\n"
else:
    output = 'File'
    for metric in metrics:
        output += ',' + metric
    print output
    for filespec in sys.argv[1:]:
        for file in glob.glob(filespec):
            ProcessFile(file)
